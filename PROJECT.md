# Franark project

FRAN is the queen bee and Project Manager. Specialist worker agents investigate, prepare, verify, and report work.

## Product goal

Reduce repetitive coordination by turning work discussions and evidence into traceable tasks, reviewed deliverables, and bounded actions.

## Delivery milestones

| Milestone | Exit condition |
|---|---|
| M0 — Launch | Target-machine demo, repository checks, documentation, and synthetic API validation. |
| M1 — Reliable workflows | Structured task/evidence records, policy-based priorities, check-ins, and questions. |
| M2 — Work integrations | One approved source and destination, scoped tools, IT/WellSky and tablet pilots. |
| M3 — Controlled autonomy | Durable scheduling, budgets, recovery, and appropriate shared access. |

## Backlog

These are prepared development issues. GitHub issue numbers will be recorded after repository import.

| ID | Issue | Milestone | Priority | Depends on |
|---|---|---|---|---|
| FW-001 | Bootstrap the private repository and issue backlog | M0 | P0 | — |
| FW-002 | Verify the local Docker launch on the target computer | M0 | P0 | FW-001 |
| FW-003 | Validate the work API project with synthetic notes | M0 | P1 | FW-002 |
| FW-004 | Run repository CI and documentation checks | M0 | P1 | FW-001 |
| FW-005 | Introduce structured operational task records | M1 | P0 | FW-002 |
| FW-006 | Add versioned evidence records and source locations | M1 | P0 | FW-005 |
| FW-007 | Implement the approved priority-policy engine | M1 | P0 | FW-005, FW-006 |
| FW-008 | Support project check-ins and task reconciliation | M1 | P1 | FW-005 |
| FW-009 | Consolidate clarification questions without blocking unrelated work | M1 | P1 | FW-005, FW-006 |
| FW-010 | Load versioned workflows from configuration | M1 | P1 | FW-005 |
| FW-011 | Add per-role runtime and model profiles | M1 | P2 | FW-003, FW-010 |
| FW-012 | Connect an approved Outlook or Teams source | M2 | P0 | FW-006, FW-016 |
| FW-013 | Add invoice and document ingestion | M2 | P1 | FW-006 |
| FW-014 | Add a read-only WellSky reporting adapter | M2 | P1 | FW-006, FW-016 |
| FW-015 | Connect one ticket or draft destination | M2 | P1 | FW-005, FW-016 |
| FW-016 | Implement exact-action policy checks and scoped tool adapters | M2 | P0 | FW-005, FW-006 |
| FW-017 | Deliver the first IT provider assessment | M2 | P1 | FW-007, FW-013 |
| FW-018 | Deliver a forms or vendor-portal tablet pilot | M2 | P1 | FW-008, FW-016 |
| FW-019 | Add durable scheduling and bounded rework | M3 | P1 | FW-009, FW-010, FW-016 |
| FW-020 | Add usage accounting and enforceable run budgets | M3 | P1 | FW-011 |
| FW-021 | Add authenticated remote and multiuser access | M3 | P2 | FW-016 |
| FW-022 | Add database migrations and tested backup restoration | M3 | P1 | FW-005, FW-019 |
| FW-023 | Add documentation publishing and journal feeds | M3 | P2 | FW-004 |
| FW-024 | Evaluate executable packaging after the local pilot | M3 | P2 | FW-002, FW-022 |

The machine-readable backlog includes a user story and acceptance criteria for each issue. Use `python tools/seed_issues.py --repo OzPol/franark` to preview an import.

## Definition of done

- The issue acceptance criteria are met and verified.
- Changes are reviewed with source evidence or focused technical checks.
- Relevant documentation and changelog entries are updated.
- Operational outputs identify remaining decisions or required physical tests.

## First release scope

The starter provides local runs, a role catalog, persistent event history, a model adapter, reports, documentation, and tests. Source connectors, operational task records, deterministic priority policy evaluation, external actions, and unattended scheduling follow the milestones above.
