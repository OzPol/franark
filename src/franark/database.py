"""Portable relational schema and explicit Azure SQL connection strategy."""
from pathlib import Path
import struct

from sqlalchemy import (Column, ForeignKey, Integer, MetaData, String, Table,
                        Unicode, UnicodeText, create_engine, event, inspect, text)
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool, StaticPool

metadata = MetaData()
runs = Table("runs", metadata,
    Column("id", String(32), primary_key=True),
    Column("request_key", String(100), unique=True, nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column("title", Unicode(150), nullable=False), Column("notes", UnicodeText, nullable=False),
    Column("domain", String(30), nullable=False), Column("runtime", String(30), nullable=False),
    Column("status", String(30), nullable=False), Column("created_at", String(40), nullable=False),
    Column("updated_at", String(40), nullable=False), Column("message", UnicodeText, nullable=False),
    Column("owner_subject", String(200), nullable=False, server_default="local-pilot"))
events = Table("events", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String(32), ForeignKey("runs.id"), nullable=False),
    Column("kind", String(30), nullable=False), Column("step_id", String(100), nullable=False),
    Column("agent_id", String(100), nullable=False), Column("result_json", UnicodeText),
    Column("created_at", String(40), nullable=False))
measurements = Table("measurements", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String(32), ForeignKey("runs.id")), Column("kind", String(30), nullable=False),
    Column("metadata_json", UnicodeText, nullable=False), Column("created_at", String(40), nullable=False),
    Column("owner_subject", String(200), nullable=False, server_default="local-pilot"))
form_definitions = Table("form_definitions", metadata,
    Column("form_key", String(150), primary_key=True),
    Column("definition_json", UnicodeText, nullable=False), Column("created_at", String(40), nullable=False))
submissions = Table("submissions", metadata,
    Column("id", String(32), primary_key=True),
    Column("request_key", String(64), unique=True, nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column("form_key", String(150), ForeignKey("form_definitions.form_key"), nullable=False),
    Column("client_ref", Unicode(100), nullable=False),
    Column("owner_subject", String(200), nullable=False), Column("reviewer_subject", String(200)),
    Column("state", String(30), nullable=False), Column("revision", Integer, nullable=False),
    Column("answers_json", UnicodeText, nullable=False), Column("signature_json", UnicodeText),
    Column("findings_json", UnicodeText, nullable=False), Column("note", UnicodeText, nullable=False),
    Column("payload_sha256", String(64), nullable=False),
    Column("supersedes_id", String(32), ForeignKey("submissions.id")),
    Column("ai_review_json", UnicodeText),
    Column("created_at", String(40), nullable=False), Column("updated_at", String(40), nullable=False))
submission_events = Table("submission_events", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("submission_id", String(32), ForeignKey("submissions.id"), nullable=False),
    Column("actor_subject", String(200), nullable=False), Column("action", String(40), nullable=False),
    Column("detail_json", UnicodeText, nullable=False), Column("created_at", String(40), nullable=False))


def azure_token_hook(credential):
    """SQLAlchemy's documented pyodbc access-token hook; no token persistence."""
    def connect(dialect, connection_record, cargs, cparams):
        cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")
        token = credential.get_token("https://database.windows.net/.default").token.encode("utf-16-le")
        cparams.setdefault("attrs_before", {})[1256] = struct.pack(f"<I{len(token)}s", len(token), token)
    return connect


def make_engine(path: Path, database_url: str = "", sql_auth: str = "managed_identity"):
    if not database_url:
        path.parent.mkdir(parents=True, exist_ok=True)
        database_url = "sqlite:///" + str(path.resolve())
    url = make_url(database_url)
    options = {"pool_pre_ping": True, "hide_parameters": True}
    if url.get_backend_name() == "sqlite":
        options["poolclass"] = StaticPool if url.database in {None, ":memory:"} else NullPool
        options["connect_args"] = {"check_same_thread": False}
    elif url.get_backend_name() == "mssql":
        lower = {key.lower(): str(value).lower() for key, value in url.query.items()}
        if not url.host or not url.host.endswith(".database.windows.net") or lower.get("encrypt") not in {"yes", "true"} or lower.get("trustservercertificate") not in {"no", "false"}:
            raise ValueError("Azure SQL requires an Azure SQL hostname, Encrypt=yes and TrustServerCertificate=no.")
        if sql_auth == "managed_identity" and (url.username or url.password or set(lower) & {"uid", "pwd", "authentication", "trusted_connection"}):
            raise ValueError("Managed identity SQL configuration must not mix token and credential authentication.")
    engine = create_engine(url, **options)
    if engine.dialect.name not in {"sqlite", "mssql"}:
        engine.dispose()
        raise ValueError("Only SQLite and Azure SQL are configured database backends.")
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def sqlite_options(connection, record):
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 10000")
    elif sql_auth == "managed_identity":
        if engine.url.username or engine.url.password:
            raise ValueError("Managed identity SQL configuration must not contain a username or password.")
        from azure.identity import DefaultAzureCredential
        event.listen(engine, "do_connect", azure_token_hook(DefaultAzureCredential()))
    metadata.create_all(engine)
    inspector = inspect(engine)
    for table in (runs, measurements):
        if "owner_subject" not in {column["name"] for column in inspector.get_columns(table.name)}:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table.name} ADD owner_subject VARCHAR(200) NOT NULL DEFAULT 'local-pilot'"))
    return engine
