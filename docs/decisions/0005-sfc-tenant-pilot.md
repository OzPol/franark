# ADR-0005: SFC tenant target and a complete synthetic pilot

Document ID: ADR-0005. Owner: Oz. Status: implemented pilot; tenant connection pending.
Updated: 2026-11-20. Scope: PILOT-001.

## Context

I am targeting SFC's tenant directly rather than creating a separate personal
cloud deployment. I need an executable test path before selecting the exact
assessment, signing agreement and vendor transfer contract. All work remains on
`capability-foundation`; `main` is not a deployment or merge target for this step.

## Decision

Add one explicitly synthetic, schema-driven form and a persisted draft/submission/
review/correction flow. Keep functions for validation and rendering, and services
for storage and lifecycle operations. Preserve existing agent contracts.

Use SQLAlchemy for shared SQLite/Azure SQL storage rather than duplicate query
implementations. Add optimistic revision checks, owner/assigned-reviewer scope,
idempotent creation and audit events. Submitted answers remain immutable.

Add strict single-tenant JWT validation, app-role requirements and SFC App Service
configuration. Local authentication remains loopback-only and cannot run on Azure
App Service. Actual tenant identities and provider connections still need testing.

## Consequences

The pilot can exercise form entry, a changed birthdate, signature acknowledgement,
human resolution, note generation and generic exports without inventing a 701
schema or claiming a vendor transfer. AI quality review is optional and cannot
approve a record. Self-review exists only for the synthetic administration test.

Live clinical/program rules, attachment storage, email delivery, provider-backed
signatures, offline behavior and vendor mapping remain separate acceptance work.
The collection checklist is maintained in `PILOT_CHECKLIST.md` and app setup data.
