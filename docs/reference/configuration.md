# Configuration

| Variable | Default | Meaning |
|---|---|---|
| `FRANARK_RUNTIME` | `demo` | `demo` or `openai`. |
| `FRANARK_MODEL` | Empty | Model ID for live API requests. |
| `OPENAI_API_KEY` | Empty | Server-side API key. |
| `FRANARK_DATA_DIR` | `./data` | Local data directory; Compose overrides it to `/app/data`. |
| `FRANARK_MAX_CALLS` | `10` | Maximum agent invocations and actual model requests per run, each capped; model follow-ups count. Supported range 1–20. |
| `FRANARK_MAX_OUTPUT_TOKENS` | `1400` | Output-token cap for each model response; supported range 256–8000. |
| `FRANARK_MAX_TOOL_ROUNDS` | `2` | Maximum information-tool rounds per agent; supported range 0–4. |
| `FRANARK_AUTH_MODE` | `local` | Loopback-only development, or `entra` for the SFC hosted pilot. |
| `FRANARK_TENANT_ID`, `FRANARK_CLIENT_ID` | Empty | Exact SFC tenant and dedicated application audience; required in Entra mode. |
| `FRANARK_PUBLIC_ORIGIN` | Empty | Exact HTTPS origin, required in Entra mode. |
| `FRANARK_ALLOWED_HOSTS` | Loopback hosts | Exact accepted hosts; cloud mode needs the returned SFC host. |
| `FRANARK_DATABASE_URL` | Empty | Empty selects local SQLite; Azure uses a TLS-enforced `mssql+pyodbc` URL. |
| `FRANARK_SQL_AUTH` | `managed_identity` | Azure SQL token strategy; `connection_string` is an explicit alternative. |

The default IT workflow has ten steps. General has eight; WellSky and software
have nine. Tool use can add follow-up model requests; a call cap stops a run
when the limit is reached. The pilot does
not automatically retry or loop after rejection.

Roles live in `src/franark/resources/roles.json`. Each has a stable role ID,
display name, instructions, capabilities, and maximum tool allowlist. Changing
a friendly name does not change its technical role or existing workflow routes.

Workflow definitions currently live in `pipeline.py`. The core supports agent
registration and step insertion. Configuration-driven workflow loading,
per-project permissions, explicit priority-policy evaluation, and per-role model
selection are tracked in the backlog.
