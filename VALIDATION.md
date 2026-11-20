# Validation record

## CAP-001 — 2026-11-19

Python 3.12, pinned repository dependencies, synthetic inputs and fake model clients.

| Check | Result |
|---|---|
| Unit/application suite | 43 tests passed, including exact replay, Unicode roundtrips, source offsets, pinned-budget refusal, timeline corrections and HTTP input limits. |
| Model tools | Fake-client function-call round trip, allowlist rejection and actual request-budget enforcement passed. No live API account was used. |
| Method examples | All six registered synthetic examples executed; actual output overhead is reported even when larger than input. |
| Generated role reference | Matches the catalog. |
| Sphinx | Strict warnings-as-errors build passed. |
| JavaScript | Both dashboard and capabilities-lab inline scripts pass Node syntax checks. |
| Browser/device QA | Not completed; UI verification covers TestClient responses and JavaScript syntax only. Physical iPad/Surface and employee sign-in checks remain pending. |

Microsoft identity, Azure SQL/storage, email, signature providers and vendor
imports are proposed integrations, not connected or tested. The operational
portal and assessment workflows are not implemented in this change.

## Original local pilot

Local pilot checks completed with Python 3.12:

| Check | Result |
|---|---|
| Unit and application tests | 23 passed. |
| Included domain workflows | General, IT, WellSky, and software demo paths completed. |
| Structured model adapter | Fake-client contract, incomplete-response handling, and call-cap tests passed. |
| Generated role reference | Matches the canonical role configuration. |
| Sphinx build | 44 source pages built with warnings treated as errors. |
| Dashboard JavaScript | Syntax check passed. |
| Compose configuration | Parsed; app and documentation ports bind to localhost. |
| Backlog | 24 issue definitions; dependency graph is acyclic; import preview completed. |

Target-computer checks are FW-002 and FW-003: build and launch the Docker images,
inspect the browser flow, and validate the selected work API project using the
synthetic sample. These checks are described in `START_HERE.md`.

Source-system and action connectors follow milestone M2. Unattended scheduling,
recovery, and usage budgets follow milestone M3.
