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

The stable issue IDs below link to the imported GitHub development issues.

| ID | Issue | Milestone | Priority | Depends on |
|---|---|---|---|---|
| [FW-001](https://github.com/OzPol/franark/issues/1) | Bootstrap the private repository and issue backlog | M0 | P0 | — |
| [FW-002](https://github.com/OzPol/franark/issues/2) | Verify the local Docker launch on the target computer | M0 | P0 | [FW-001](https://github.com/OzPol/franark/issues/1) |
| [FW-003](https://github.com/OzPol/franark/issues/3) | Validate the work API project with synthetic notes | M0 | P1 | [FW-002](https://github.com/OzPol/franark/issues/2) |
| [FW-004](https://github.com/OzPol/franark/issues/4) | Run repository CI and documentation checks | M0 | P1 | [FW-001](https://github.com/OzPol/franark/issues/1) |
| [FW-005](https://github.com/OzPol/franark/issues/5) | Introduce structured operational task records | M1 | P0 | [FW-002](https://github.com/OzPol/franark/issues/2) |
| [FW-006](https://github.com/OzPol/franark/issues/6) | Add versioned evidence records and source locations | M1 | P0 | [FW-005](https://github.com/OzPol/franark/issues/5) |
| [FW-007](https://github.com/OzPol/franark/issues/7) | Implement the approved priority-policy engine | M1 | P0 | FW-005, FW-006 |
| [FW-008](https://github.com/OzPol/franark/issues/8) | Support project check-ins and task reconciliation | M1 | P1 | [FW-005](https://github.com/OzPol/franark/issues/5) |
| [FW-009](https://github.com/OzPol/franark/issues/9) | Consolidate clarification questions without blocking unrelated work | M1 | P1 | FW-005, FW-006 |
| [FW-010](https://github.com/OzPol/franark/issues/10) | Load versioned workflows from configuration | M1 | P1 | [FW-005](https://github.com/OzPol/franark/issues/5) |
| [FW-011](https://github.com/OzPol/franark/issues/11) | Add per-role runtime and model profiles | M1 | P2 | FW-003, FW-010 |
| [FW-012](https://github.com/OzPol/franark/issues/12) | Connect an approved Outlook or Teams source | M2 | P0 | FW-006, FW-016 |
| [FW-013](https://github.com/OzPol/franark/issues/13) | Add invoice and document ingestion | M2 | P1 | [FW-006](https://github.com/OzPol/franark/issues/6) |
| [FW-014](https://github.com/OzPol/franark/issues/14) | Add a read-only WellSky reporting adapter | M2 | P1 | FW-006, FW-016 |
| [FW-015](https://github.com/OzPol/franark/issues/15) | Connect one ticket or draft destination | M2 | P1 | FW-005, FW-016 |
| [FW-016](https://github.com/OzPol/franark/issues/16) | Implement exact-action policy checks and scoped tool adapters | M2 | P0 | FW-005, FW-006 |
| [FW-017](https://github.com/OzPol/franark/issues/17) | Deliver the first IT provider assessment | M2 | P1 | FW-007, FW-013 |
| [FW-018](https://github.com/OzPol/franark/issues/18) | Deliver a forms or vendor-portal tablet pilot | M2 | P1 | FW-008, FW-016 |
| [FW-019](https://github.com/OzPol/franark/issues/19) | Add durable scheduling and bounded rework | M3 | P1 | FW-009, FW-010, FW-016 |
| [FW-020](https://github.com/OzPol/franark/issues/20) | Add usage accounting and enforceable run budgets | M3 | P1 | [FW-011](https://github.com/OzPol/franark/issues/11) |
| [FW-021](https://github.com/OzPol/franark/issues/21) | Add authenticated remote and multiuser access | M3 | P2 | [FW-016](https://github.com/OzPol/franark/issues/16) |
| [FW-022](https://github.com/OzPol/franark/issues/22) | Add database migrations and tested backup restoration | M3 | P1 | FW-005, FW-019 |
| [FW-023](https://github.com/OzPol/franark/issues/23) | Add documentation publishing and journal feeds | M3 | P2 | [FW-004](https://github.com/OzPol/franark/issues/4) |
| [FW-024](https://github.com/OzPol/franark/issues/24) | Evaluate executable packaging after the local pilot | M3 | P2 | FW-002, FW-022 |

The machine-readable backlog includes a user story and acceptance criteria for each issue. Use `python tools/seed_issues.py --repo OzPol/franark` to preview an import.

## Definition of done

- The issue acceptance criteria are met and verified.
- Changes are reviewed with source evidence or focused technical checks.
- Relevant documentation and changelog entries are updated.
- Operational outputs identify remaining decisions or required physical tests.

## First release scope

The starter provides local runs, a role catalog, persistent event history, a model adapter, reports, documentation, and tests. Source connectors, operational task records, deterministic priority policy evaluation, external actions, and unattended scheduling follow the milestones above.

## CAP-001 — Information mechanism foundation

Requested 2026-11-19. Add six callable, measured baseline information methods,
source papers/standards, research history and a local lab. Acceptance criteria:
validated input contracts; effective tool permissions; actual timing/byte/hash
records; exact reconstruction where claimed; bounded model function calling;
preserved original agent contracts; tests and strict documentation build.

The SFC portal requirements and options are recorded in
`docs/explanations/sfc-portal-plan.md`. Form selection, offline behavior, licenses,
production identity and supported import interfaces remain open decisions. This
scope does not mark integration milestones or existing GitHub issues complete.
