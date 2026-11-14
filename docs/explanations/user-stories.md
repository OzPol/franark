# User stories

| ID | Story | Acceptance criteria | Delivery |
|---|---|---|---|
| US-001 | As Oz, I can open a local workbench and inspect the team. | Health endpoint works; ten roles are listed; no credentials appear in responses. | Local pilot |
| US-002 | As Oz, I can submit notes and watch the handoffs. | A saved run shows assignments, results, review decisions, and final status. | Local pilot |
| US-003 | As Oz, I can restart without losing completed work. | Sources and step outputs remain; unfinished work is identified as interrupted. | Local pilot |
| US-004 | As Oz, I can use a model API for ordinary meeting notes. | Structured outputs, source references, call limits, and explicit runtime selection. | Adapter included; account validation next |
| US-005 | As PM FRAN, I can prioritize from policy and facts. | Deterministic rule evaluation, evidence, policy version, and visible assumptions. | Milestone 1 |
| US-006 | As Oz, I can add instructions after a meeting. | New tasks link to the project, reconcile existing tasks, and preserve decisions. | Milestone 1 |
| US-007 | As an IT lead, I can obtain a vendor assessment. | Contract/invoice scope, normalized comparison, transition effort, and cited findings. | Milestone 2 |
| US-008 | As a WellSky analyst, I can produce a diagnostic packet. | Exact checks, source-applicability checks, read-only queries, interpretations, and questions. | Milestone 2 |
| US-009 | As a developer, I can inject another specialist. | Registration and graph insertion work; reviewer separation is preserved. | Core contract included |
| US-010 | As Oz, I can connect approved work sources and destinations. | Scoped authentication, source cursors, duplicate prevention, and per-action verification. | Milestone 2 |
| US-011 | As Oz, I receive a consolidated clarification packet. | Nonblocking tasks continue; repeated questions are merged and identify what they unblock. | Milestone 1 |
| US-012 | As a maintainer, I can publish consistent documentation. | Templates, version archive, Sphinx navigation, and strict documentation build. | Local pilot |
| US-013 | As Oz, I can run bounded unattended work. | Durable scheduler, exact-action policy checks, retries, cancellation, and recovery. | Milestone 3 |
| US-014 | As Oz, I can perform the remaining tablet test. | Testable build, account-connection instructions, expected results, and failure capture steps. | Milestone 2 |

Development issue IDs and milestone dependencies are maintained in
`backlog/issues.json` and the repository's `PROJECT.md`.
