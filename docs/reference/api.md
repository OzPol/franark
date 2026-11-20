# Local HTTP API

The browser dashboard and API are served by the same local process. The Compose
host ports bind to `127.0.0.1`. The pilot is a single-user workbench; adding remote
access or multiple users requires the corresponding authentication milestone.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Application health and version. |
| `GET /api/config` | Runtime, model, role catalog, sample notes, and readiness; excludes the key. |
| `POST /api/runs` | Save and queue a new run. |
| `GET /api/runs` | Latest 100 run summaries. |
| `GET /api/runs/{id}` | Source notes and ordered assignment/result events. |
| `GET /api/runs/{id}/report` | Download a Markdown report. |
| `GET /lab` | Local capabilities lab. |
| `GET /api/capabilities` | Method schemas, examples and research references. |
| `POST /api/capabilities/execute` | Run a validated information method and record telemetry. |
| `GET /api/measurements` | Latest 100 content-free method/model usage records. |
| `GET /portal` | Synthetic assessment pilot. |
| `GET /architecture` | Context, software, workflow and record diagrams. |
| `GET /api/identity` | Verified caller identity and assigned app roles. |
| `GET /api/setup` | Administrator-only connection readiness and collection checklist. |
| `GET /api/portal/forms` | Frozen synthetic form definitions and versions. |
| `GET, POST /api/portal/submissions` | List authorized records or create an idempotent draft. |
| `GET, PUT /api/portal/submissions/{id}` | Inspect an authorized revision or update an owned draft with a revision precondition. |
| `POST /api/portal/submissions/{id}/submit` | Freeze a draft, bind acknowledgement and run validation. |
| `POST /api/portal/submissions/{id}/review` | Assigned reviewer/admin approves or requests changes with a resolution. |
| `POST /api/portal/submissions/{id}/correction` | Create a linked new draft with no carried-over signature. |
| `POST /api/portal/submissions/{id}/ai-review` | Optional bounded model quality draft; cannot release a record. |
| `GET /api/portal/submissions/{id}/export/{format}` | Approved PDF/JSON/CSV/note, or an unsent email draft for findings. |

Submission fields are `title`, `notes`, `domain`, and optional `request_key`.
Domains are `general`, `it`, `wellsky`, and `software`. Notes are limited to
20,000 characters. Reusing a request key with the same content returns the
existing run. Reusing it with different content returns a conflict.

Run states: `queued`, `running`, `finished`, `rejected`, `needs_input`, `failed`,
and `interrupted`. A finished run means the configured steps completed; individual
review results identify which drafts were accepted.

The interactive endpoint reference is also available at `/docs` on the app port.

In `entra` mode, API requests require a valid configured-tenant JWT and app role.
Run history and measurements are scoped to the caller unless the caller is an
administrator. Portal scope is owner, explicitly assigned reviewer, or admin.
Unknown/out-of-scope records return 404. Local mode remains loopback-only.
