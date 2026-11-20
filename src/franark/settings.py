from dataclasses import dataclass
from pathlib import Path
import os
from uuid import UUID


@dataclass(frozen=True)
class Settings:
    runtime: str = "demo"
    model: str = ""
    api_key: str = ""
    data_dir: Path = Path("data")
    max_calls: int = 10
    max_output_tokens: int = 1400
    max_tool_rounds: int = 2
    auth_mode: str = "local"
    tenant_id: str = ""
    client_id: str = ""
    public_origin: str = ""
    database_url: str = ""
    sql_auth: str = "managed_identity"
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "testserver")

    def __post_init__(self):
        if self.runtime not in {"demo", "openai"}:
            raise ValueError("FRANARK_RUNTIME must be demo or openai.")
        if not 1 <= self.max_calls <= 20:
            raise ValueError("FRANARK_MAX_CALLS must be between 1 and 20.")
        if not 256 <= self.max_output_tokens <= 8000:
            raise ValueError("FRANARK_MAX_OUTPUT_TOKENS must be between 256 and 8000.")
        if not 0 <= self.max_tool_rounds <= 4:
            raise ValueError("FRANARK_MAX_TOOL_ROUNDS must be between 0 and 4.")
        if self.auth_mode not in {"local", "entra"}:
            raise ValueError("Authentication mode must be local or entra.")
        if self.auth_mode == "local" and not set(self.allowed_hosts) <= {"127.0.0.1", "localhost", "testserver"}:
            raise ValueError("Local authentication is restricted to loopback hosts.")
        if self.auth_mode == "local" and os.getenv("WEBSITE_SITE_NAME"):
            raise ValueError("Azure App Service requires Entra authentication mode.")
        if self.auth_mode == "entra":
            UUID(self.tenant_id)
            UUID(self.client_id)
            from urllib.parse import urlparse
            parsed = urlparse(self.public_origin)
            if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts or parsed.path or parsed.query or parsed.fragment or parsed.username:
                raise ValueError("Entra mode requires an HTTPS origin matching one exact allowed host, without a trailing slash.")
        if self.sql_auth not in {"managed_identity", "connection_string"}:
            raise ValueError("SQL authentication mode is invalid.")

    @classmethod
    def from_env(cls):
        return cls(
            runtime=os.getenv("FRANARK_RUNTIME", "demo"),
            model=os.getenv("FRANARK_MODEL", ""),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            data_dir=Path(os.getenv("FRANARK_DATA_DIR", "data")),
            max_calls=int(os.getenv("FRANARK_MAX_CALLS", "10")),
            max_output_tokens=int(os.getenv("FRANARK_MAX_OUTPUT_TOKENS", "1400")),
            max_tool_rounds=int(os.getenv("FRANARK_MAX_TOOL_ROUNDS", "2")),
            auth_mode=os.getenv("FRANARK_AUTH_MODE", "local"),
            tenant_id=os.getenv("FRANARK_TENANT_ID", ""),
            client_id=os.getenv("FRANARK_CLIENT_ID", ""),
            public_origin=os.getenv("FRANARK_PUBLIC_ORIGIN", ""),
            database_url=os.getenv("FRANARK_DATABASE_URL", ""),
            sql_auth=os.getenv("FRANARK_SQL_AUTH", "managed_identity"),
            allowed_hosts=tuple(value.strip() for value in os.getenv("FRANARK_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if value.strip()),
        )
