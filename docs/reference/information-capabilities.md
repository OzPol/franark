# Information capability API

Scope: CAP-001. All methods are supplied-input transformations. They do not query
external systems, send messages, access other projects or modify business records.

| Tool | Input model | Returned representation |
|---|---|---|
| `memory.select` | query, documents with IDs/versions, byte budget | BM25-selected complete documents with scores and omissions |
| `memory.delta` | source ID, base/current versions, before/after objects | Hashed add/remove/replace patch and exact-replay check |
| `memory.pack` | text, compression level | zlib/DEFLATE/base64 packet and reconstruction check |
| `memory.project` | source/version, record, fields/protected JSON Pointers | Selected values and explicit missing fields |
| `memory.summarize` | query, documents, byte/sentence budgets, relevance weight | BM25+MMR-selected verbatim sentences with character offsets |
| `memory.timeline` | source ID, ordered snapshots, heartbeat interval | State-change/critical/heartbeat/final keyframes and folded IDs |

`GET /api/capabilities` returns exact JSON Schemas, synthetic examples and research
reference metadata. `POST /api/capabilities/execute` accepts:

```json
{"name":"memory.pack","arguments":{"text":"synthetic example","level":6}}
```

Response fields are `method`, `method_version`, `implementation_sha256`,
`references`, `result` and `metrics`. Invalid arguments return 422; oversized HTTP
requests return 413. HTTP error messages do not reproduce submitted values.

`GET /api/measurements` returns the most recent 100 local telemetry records.
These endpoints inherit the app's loopback-only development boundary. They do not
implement employee authentication or per-client access control.

## Calling from application code

```python
from franark.capabilities import execute, handlers
from franark.core import Toolbox

tools = Toolbox(frozenset({"memory.pack"}), handlers())
measured = tools.call("memory.pack", text="synthetic repeated content")
```

An agent's effective tool set remains the intersection of its role, instance and
project grants. Adding a capability name to a role is insufficient unless an
implementation and the other grants also exist. Current pure methods are granted
through `run_saved`; the OpenAI adapter advertises only the eligible schemas.

OpenAI function names use aliases such as `memory_pack`, mapped back to
`memory.pack`. Arbitrary input records require non-strict function schemas;
Pydantic still validates and bounds inputs before execution. Final AgentResult
output retains its strict schema. Tool results describe supplied data, so an
agent-generated field extraction still requires source verification.

`FRANARK_MAX_TOOL_ROUNDS` (default 2, range 0–4) bounds information-tool rounds per
agent. `FRANARK_MAX_CALLS` also caps actual model requests across the workflow,
including follow-ups; no SDK retry silently exceeds it. The default 10-request
budget can stop a multi-agent workflow that uses tools. Increase it deliberately
within the supported range after examining usage. Exceeding a budget fails the
run and preserves its recorded steps; it does not grant additional calls.

See [method equations](../research/methods.md) for algorithms and measurement
definitions and [the lab guide](../how-to/use-capabilities.md) for reproduction.
