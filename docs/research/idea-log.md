# History of ideas and implementation

This is my design and implementation ledger. It separates motivation, working
software, measured results and unverified integrations.

## 2026-11-19 - compression mechanisms and Franark

I started from `cognitive_compression_multi_agent_simulator.html` and explored
using its six information mechanisms inside Franark and SFC workflows. The
prototype contained isolated demonstrations, manual activation thresholds,
synthetic system metrics and a placeholder semantic audit. It did not execute
the full displayed pipeline.

I chose to build and understand the system with established methods and observed
measurements before searching for improvements or research novelty. The first
suite implements BM25 selection, exact state deltas, DEFLATE storage encoding,
explicit projection, BM25+MMR extraction and conservative event-boundary timelines.
Method records identify the research/standard, adaptation, equation and limitations.

The implementation preserves the existing Python agent contracts, grants tools
through role/instance/project scope, records real telemetry and provides an
explicit reproduction-bundle download. No biological equivalence or semantic
fidelity guarantee is claimed.

## 2026-11-20 - SFC tenant and executable pilot

I selected SFC's tenant as the deployment target. I will separate development/test
and production resources there rather than create a personal cloud deployment.
All changes remain on `capability-foundation`; `main` stays unchanged.

The synthetic assessment pilot now includes saved drafts, frozen submissions,
version-bound acknowledgements, validation, prior-birthdate comparison, human
review, correction drafts, template notes and generic outputs. A model can draft
quality findings after configuration; it cannot release a record. The test form
is not an invented replacement for a 701 assessment.

Storage uses SQLAlchemy with a working local SQLite backend and an Azure SQL
managed-identity adapter. Tenant JWT/role verification, record ownership, an
Azure deployment template and four context/stack/workflow/data diagrams are part
of this checkpoint. Live tenant, database, provider and physical-device tests
remain unverified.

## My remaining design inputs

- Exact form/version, note template, field/correction rules and accepted examples.
- Online/offline needs and signature requirements.
- SFC licenses, tenant access, program/record scopes, accounts and budget.
- Supported vendor import/receipt contracts and test access.
- Appropriate model inputs, analytics permissions and task-specific quality labels.

I will link later entries to commits, datasets, configurations and observed
outcomes, including negative and inconclusive results. `PILOT_CHECKLIST.md` holds
the current collection and test sequence.


## 2026-11-20 - Focused architecture views

I separated the conceptual model into service structure, capture dimensions,
connectivity, application surfaces, platform connections, business destinations,
software layers, responsibilities, revision states, callable methods, source
provenance and relational entities. Each concept retains a stable ID.
Mermaid notation and native Excalidraw files preserve both semantic relationships
and direct editing. Paper remains explicit; offline synchronization and future
provider choices are dashed options rather than implemented features.
