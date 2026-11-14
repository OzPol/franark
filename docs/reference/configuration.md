# Configuration

| Variable | Default | Meaning |
|---|---|---|
| `FRANARK_RUNTIME` | `demo` | `demo` or `openai`. |
| `FRANARK_MODEL` | Empty | Model ID for live API requests. |
| `OPENAI_API_KEY` | Empty | Server-side API key. |
| `FRANARK_DATA_DIR` | `./data` | Local data directory; Compose overrides it to `/app/data`. |
| `FRANARK_MAX_CALLS` | `10` | Maximum agent calls in a run; supported range 1–20. |
| `FRANARK_MAX_OUTPUT_TOKENS` | `1400` | Output-token cap for each model response; supported range 256–8000. |

The default IT workflow has ten steps. General has eight; WellSky and software
have nine. A lower call cap stops a run when the limit is reached. The pilot does
not automatically retry or loop after rejection.

Roles live in `src/franark/resources/roles.json`. Each has a stable role ID,
display name, instructions, capabilities, and maximum tool allowlist. Changing
a friendly name does not change its technical role or existing workflow routes.

Workflow definitions currently live in `pipeline.py`. The core supports agent
registration and step insertion. Configuration-driven workflow loading,
per-project permissions, explicit priority-policy evaluation, and per-role model
selection are tracked in the backlog.
