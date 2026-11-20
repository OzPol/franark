from pathlib import Path
import sqlite3
import struct
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from sqlalchemy.dialects import mssql
from sqlalchemy.schema import CreateTable

from franark.database import azure_token_hook, metadata
from franark.store import Store


class DatabaseTests(unittest.TestCase):
    def test_unsafe_azure_sql_configuration_is_rejected_before_connecting(self):
        from franark.database import make_engine
        with TemporaryDirectory() as folder:
            for url in ("mssql+pyodbc://@server.database.windows.net/db?Encrypt=no&TrustServerCertificate=yes",
                        "mssql+pyodbc://@server.database.windows.net/db?Encrypt=yes&TrustServerCertificate=no&Authentication=ActiveDirectoryPassword"):
                with self.assertRaises(ValueError):
                    make_engine(Path(folder) / "unused.sqlite3", url)

    def test_all_tables_compile_for_azure_sql(self):
        for table in metadata.sorted_tables:
            statement = str(CreateTable(table).compile(dialect=mssql.dialect()))
            self.assertIn("CREATE TABLE", statement)
            self.assertNotIn("AUTOINCREMENT", statement)

    def test_managed_identity_token_hook_uses_sql_scope_and_utf16(self):
        scopes = []
        credential = SimpleNamespace(get_token=lambda scope: (scopes.append(scope) or SimpleNamespace(token="synthetic-token")))
        args, parameters = ["DRIVER=x;Trusted_Connection=Yes;Encrypt=yes"], {}
        azure_token_hook(credential)(None, None, args, parameters)
        self.assertNotIn("Trusted_Connection", args[0])
        packed = parameters["attrs_before"][1256]
        length = struct.unpack("<I", packed[:4])[0]
        self.assertEqual(packed[4:4 + length].decode("utf-16-le"), "synthetic-token")
        self.assertEqual(scopes, ["https://database.windows.net/.default"])

    def test_original_sqlite_database_is_migrated_without_losing_history(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "old.sqlite3"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE runs (id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL, title TEXT NOT NULL, notes TEXT NOT NULL, domain TEXT NOT NULL, runtime TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, message TEXT NOT NULL)")
                db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("original", "key", "hash", "Synthetic original", "Synthetic notes", "general", "demo", "finished", "2026", "2026", ""))
            store = Store(path)
            record = store.get("original")
            self.assertEqual(record["notes"], "Synthetic notes")
            self.assertEqual(record["owner_subject"], "local-pilot")
            self.assertTrue(store.ping())
            store.engine.dispose()


if __name__ == "__main__":
    unittest.main()
