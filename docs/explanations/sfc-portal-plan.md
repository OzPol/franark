# SFC application hub: requirements and design choices

Status: synthetic pilot implemented; SFC tenant connections pending. Updated 2026-11-20.
This is my requirements and design record. I have selected SFC's tenant as the
deployment target. The exact assessment, licenses, signature policy and vendor
contracts remain open.
Observable outcomes are listed in [the proposed user stories](sfc-user-stories.md).

## Intended behavior

Employees use their Microsoft work identity to access a central SFC resource hub.
Case management, nutrition, Friendship at Home, CRC and Friendship Centers can
have different forms, resources and record permissions. Vendors may submit
designated material through a separate scoped access route.

Staff enter information once on an iPad, Surface or laptop. The system preserves
structured answers and linked attachments, produces a versioned document, captures
the appropriate signature, validates answers and drafts a template-based case
note. Staff review exceptions and proposed outputs before controlled export or
submission. The hub also contains searchable, reviewed procedures and FAQs.

## Language, functions, classes and workflow definitions

| Area | Recommended starting point | Alternative and when it fits |
|---|---|---|
| Application API | Extend existing Python/FastAPI | .NET/C# if SFC has a dedicated .NET maintenance team; C++ only for a measured native compute bottleneck |
| Reusable logic | Functions for validation, mapping, projection, calculations and note rendering | A class when a component owns state, configuration, connections or a lifecycle |
| Connectors | Classes implementing stable repository/model/mail/signature/export interfaces | Direct function integration for one small, stateless operation |
| Workflow | Versioned definitions plus explicit state transitions and review points | A durable workflow engine when schedules, retries, parallelism and long waits justify it |
| Data operations | Parameterized SQL behind a repository layer | Stored procedures for stable transactional operations/reporting; no arbitrary model-generated production SQL |
| Frontend | Accessible web UI with Microsoft-style navigation; React/Fluent UI is a candidate for richer forms | Power Apps for rapid internal forms if its licensing and extensibility fit |

A workflow is more than a collection of functions: it defines who may do what,
which input/output versions each step consumes, acceptance rules, exceptions,
retry policy and what happens after interruption. The existing agent DAG remains
useful for analysis tasks. Operational forms need a separate persisted business
state machine; model output cannot assign itself approval or delivery status.

Avoid microservices initially. A modular application can expose a stable API and
split components later when workload or deployment requirements demand it.

## Custom portal versus Microsoft low-code

**Custom web app:** best fit for the combined agent workbench, research metrics,
form templates, specialized review and custom export adapters. Hosting and
maintenance remain our responsibility. It can be linked from SharePoint or Teams
and deployed under an SFC-controlled subdomain after identity and network setup.

**Power Apps with SharePoint/Dataverse:** useful for quickly testing internal
forms and approval workflows. Verify licenses before comparing cost: Microsoft's
[SQL connector](https://learn.microsoft.com/en-us/connectors/sql/) is Premium in
Power Apps and Power Automate. Microsoft 365 ownership alone does not establish
that SQL/custom-connector usage is included. The
[Developer Plan](https://learn.microsoft.com/en-us/power-platform/admin/powerapps-flow-licensing-faq)
does not provide production use rights.

**Hybrid:** Power Apps or a SharePoint surface collects data while the Franark
API handles validation, note generation, agents and experiments. This can reduce
initial form-development work but introduces another configuration/deployment
surface and may still require premium/custom-connector rights.

## Identity, access and environment separation

Recommended staff authentication: single-tenant Microsoft Entra ID using OpenID
Connect. Validate issuer, audience, tenant and token lifetime. Require actual app
assignment/authorization; checking an email suffix is insufficient. Use Entra
[application roles and groups](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps)
for broad roles, with per-program, assigned-record and action scope enforced in
the API. UI navigation alone is not a permission control. Conditional Access and
device rules depend on SFC's tenant configuration and licenses.

Proposed roles: submitter, assigned case worker, program reviewer, resource editor,
analytics reader and administrator. Their exact permissions need program input.
Agents inherit the invoking user's authorized scope plus explicit service policy.
Scheduled work needs a separate narrowly scoped service identity. Client records
must not leak into a general employee FAQ or cross-program search index.

Vendors are not automatically employees. Options are Entra B2B guest assignments
with resource-specific permissions or narrowly scoped submission invitations.
Remote signing links belong to a separate signature flow. For in-person signing,
the employee session and the client's signer identity/consent are different records.

I will keep development/test and production resources separate within SFC's
tenant, with distinct app registrations, databases, storage and audit records.
A personal tenant deployment is unnecessary. A multi-tenant SaaS product remains
a separate future decision.

## API, database, files and analytics

Recommended path: browser -> authenticated application API -> Azure SQL for
structured records, with SharePoint or Azure Blob Storage for documents.
Browsers and model prompts never receive database credentials. Azure-hosted
services can use [managed identity for SQL](https://learn.microsoft.com/en-us/azure/app-service/tutorial-connect-msi-sql-database)
and appropriately scoped storage access. Provider secrets belong in a managed
secret store, not browser settings or repository files.

| Storage choice | Good fit | Tradeoff |
|---|---|---|
| Azure SQL + Blob | Application-owned relational records and generated/uploaded files | More application/document-management work |
| Azure SQL + SharePoint | Structured answers plus familiar employee document libraries and existing retention processes | Must reconcile library permissions, versions and API access |
| Dataverse + SharePoint | Low-code forms, relationships and business rules | Licensing and platform coupling |

Store file bytes in a document/object store; keep attachment IDs, client/vendor
links, document versions, hashes, media types, ownership and access metadata in
the relational database. Blob storage alone is not a document-permission model.

Proposed entities: people/organizations, external identifiers, program assignments,
form definitions/versions, submissions/revisions, typed responses, attachments,
signature records, draft notes, validation findings, review decisions, export
batches, per-record delivery receipts and audit events. Preserve the source value,
normalized value and any human correction separately. Use transactions, foreign
keys and optimistic concurrency for operational integrity.

Expose approved reporting views or a curated analytics pipeline for Power BI and
potential Fabric use. Choosing a Fabric integration is separate from making
transactional records queryable; no Fabric capacity or connection is assumed.

## Forms and signatures

**Recommended:** schema-based, tablet-friendly data entry; generate the required
PDF layout from the submitted revision. The schema defines field IDs, types,
answer codes, required/conditional logic, validation and form version. The PDF
can closely match an approved original, while the data remains queryable.

**Alternative:** fill the existing PDF's actual form fields and extract/store
their values. Useful when exact layout is mandatory and the PDF contains reliable
AcroForm fields. Flattened scans and inconsistent PDFs make this less dependable.
OCR is a migration/fallback input path, not necessary for newly entered data.

The first form is not yet identified. DOEA lists multiple
[701 instruments](https://elderaffairs.org/resources/forms/); a 701C must not be
silently replaced with 701A/701B or an invented generic assessment. We need the
actual version, required note template and accepted output examples.

| Signature path | When useful | Design implication |
|---|---|---|
| In-person pen/touch capture | Staff-assisted assessments on a tablet | Capture signer identification, consent, employee witness/context, time and exact document hash/version; an ink image alone is not a cryptographic digital signature |
| Microsoft 365 eSignature | SharePoint-centered remote document requests | Pay-as-you-go configuration and tenant setup required; not assumed free with Microsoft 365 |
| Adobe Acrobat Sign / DocuSign | Existing agreement or required provider-supported remote/in-person flows | Verify plan, API entitlement, signer experience and audit evidence before selection |

Microsoft documents [eSignature setup and provider integration](https://learn.microsoft.com/en-us/microsoft-365/documentprocessing/esignature-setup).
Its published [pricing](https://learn.microsoft.com/en-us/microsoft-365/documentprocessing/syntex-pay-as-you-go-services)
lists native eSignature at USD 2 per request when checked on 2026-11-19;
third-party provider subscriptions/usage are separate. Confirm current terms and
SFC's entitlements before budgeting. Availability in SharePoint does not establish
that a custom portal can automate signing through a supported API.

The signature method must satisfy the specific form/program requirements. Freeze
the signed revision; changes produce a new revision with a clear re-review and,
where required, re-signing path. Provide a keyboard/screen-reader alternative to
pen entry: Microsoft's [pen-input guidance](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-pen-input)
also calls out this accessibility need.

Offline support is a separate decision. A browser/PWA can collect local drafts,
but protecting sensitive records on shared devices, sync conflicts, cache expiry
and signed-version handling require deliberate design. Do not quietly cache client
records in browser storage. Online-only is simpler when connectivity is reliable.

## Validation, case notes and quality review

Use deterministic checks for required fields, answer codes, dates, cross-field
rules, duplicate submissions and changes against the matched prior client record.
Client identity must be resolved before comparisons; uncertain matches require
human resolution rather than automatic merging.

First note-generation option: a template renderer using explicit values and
approved conditional phrases. Second option: a model drafts a narrative from
those values and selected source evidence. The latter is useful for synthesis
but requires review for unsupported statements, omitted qualifications and
template adherence. Preserve template, prompt and model versions with each draft.
Never invent an observation or overwrite a signed assessment from a model guess.

AI-assisted quality review can flag possible inconsistencies and explain its
evidence. It should abstain when evidence is insufficient. A staff correction
records who changed what and why; re-run validation and regenerate affected drafts.

Proposed exception workflow:

1. Submitted revision enters rule validation.
2. Issues enter assigned staff review; corrections create a new revision and
   return to validation.
3. Validated information produces note and document drafts.
4. Human release review either requests changes or approves export preparation.

Signing may occur before or after parts of this flow depending on the real form
process. Its placement is deliberately not finalized.

## Email, notifications and the knowledge hub

Recommended notification design: an in-app review queue is authoritative;
Microsoft Graph email provides a short notification and authorized link. Outlook
drafts/manual review are a useful first pilot. Power Automate is an alternative
for simple tenant-owned routing. Automatic sending requires a configured mailbox,
recipient policy, event/outbox handling, deduplication, rate limits and retry rules.

My communication style is represented by versioned templates:

> Hi [staff name], could you check one detail in [record link]? The birthdate
> entered on this assessment differs from the previous record. It may be an
> intended correction; please confirm which value we should use. Thank you.

The email does not need to reproduce client identifiers or both birthdates. Show
the exact comparison in the authorized application. Use a clearly identified
SFC/Franark service sender or an approved delegated identity; my writing style
does not imply permission to send under my personal identity. Final wording and notification thresholds remain
configurable.

For FAQs and how-to resources, use source-linked drafts, an editorial review
queue, owner/version/effective dates and access labels. Agents can propose
updates from reviewed procedures and recurring questions. Publishing a resource
is separate from drafting it; client-specific material never becomes a general FAQ.

## Exports, automation and reconciliation

Prefer a documented vendor API when SFC has permission and a supported interface.
Otherwise produce the exact accepted batch/EDI/import format, with a mapping
version, validation report and preview. Screen automation is a last option after
the vendor-supported paths and their constraints are understood.

No eCIRTS, SAMS or WellSky assessment/billing import contract is verified in this
change. Read-only reporting SQL access does not establish import/write access.
We need actual specifications, accepted samples, identifiers, required codes,
test access, error/acknowledgement format and permitted automation behavior.

Use a persisted job queue and transactional outbox for business actions. Derive
idempotency from environment, record identity, submission version, destination and
operation. Keep each attempt and receipt. Ambiguous timeouts need reconciliation
before retrying; a network response alone does not establish successful import.
Reconcile accepted/rejected records and totals before marking a batch complete.
Start with human-released exports, then automate only steps supported by observed
outcomes and explicit program rules.

## Incremental delivery and open questions

1. Implemented: callable methods, model tools, telemetry, assessment/review pilot,
   generic exports, JWT verification, SQL adapter, diagrams and tests.
2. Select the first form, note template, online/offline behavior and platform path.
3. Configure a development Entra app and authenticated API with program/record
   permissions; verify isolation before accepting operational records.
4. Map the verified assessment and note template into the existing pilot flow.
5. Connect approved Azure, model, file and notification accounts; validate each
   connector with narrow test scope.
6. Confirm signature and vendor transfer requirements; pilot with designated staff.

My connection work depends on SFC tenant permissions and verified contracts.
I will keep credentials in the approved secret store and retain non-secret
configuration and acceptance records in the project.
