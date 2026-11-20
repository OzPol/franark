# SFC pilot checkpoint

Deployment target: SFC Microsoft tenant. Working branch: `capability-foundation`.
Pull request: <https://github.com/OzPol/franark/pull/26>. `main` remains unchanged.

## Working pilot

- Synthetic assessment entry, saved drafts and submitted revisions.
- Typed/pen acknowledgement tied to the submitted data hash.
- Required-field/type/date checks and prior-record birthdate comparison.
- Human review, written resolution, correction drafts and audit history.
- Template case-note draft and approved PDF/JSON/CSV/note downloads.
- Downloadable unsent review email draft; no email delivery.
- Optional OpenAI quality-review call after server-side API configuration.
- Six measured information methods and research records.
- Microsoft Entra JWT/role verification and record ownership checks.
- Shared SQLAlchemy storage, local SQLite and an Azure SQL managed-identity adapter.
- Four architecture diagrams in the app and documentation.

The form is a synthetic workflow fixture, not an official 701 instrument. The
pilot does not submit to eCIRTS/WellSky/SAMS or validate a signature provider.

## First test session

1. I will use `capability-foundation`, not `main`.
2. I will start the local test with `./Start-Franark.ps1` and open `/portal`.
3. I will load the synthetic example, add a test signer, acknowledge it and submit.
4. I will review the note, enter a resolution and approve the synthetic record.
5. I will download its PDF and JSON, then create a correction draft.
6. I will change the birthdate, acknowledge the new revision and submit again.
7. I will confirm the change is flagged against the previous approved source,
   inspect the unsent email draft, and verify that review is required.
8. I will open `/architecture`, `/lab` and Connection readiness.

Local execution is a synthetic development test. My hosted deployment will be in
SFC's tenant; I am not setting up a separate personal tenant deployment.

## Information I need to collect

### Tenant, hosting and identity

- [ ] SFC tenant ID, Azure subscription, approved resource group and region.
- [ ] Existing SFC Azure/Microsoft 365 administrator and required deployment rights.
- [ ] Dedicated single-tenant app registration/client ID and ID/access-token v2 settings.
- [ ] App assignments and `Franark.Pilot`, `Franark.Reviewer`, `Franark.Admin` roles.
- [ ] A pilot administrator and a separate assigned reviewer test account/object ID.
- [ ] Container registry/image location and `AcrPull` permission for the web-app identity.
- [ ] Approved Key Vault references and secret-reader grants for the app identity.
- [ ] Returned HTTPS host/callback URI and any SFC domain requirement.
- [ ] Microsoft 365/Power Platform licenses, expected staff count and hosting budget.

### Forms, signatures and workflow

- [ ] Exact first form and version: 701C, another 701 instrument, or another form.
- [ ] Blank original, de-identified completed example and required case-note template.
- [ ] Field definitions, codes, required/conditional questions and calculations.
- [ ] Client identifiers, duplicate/uncertain matches and prior-record authority.
- [ ] Signature/consent/witness requirements and accepted correction process.
- [ ] In-person versus remote signing needs and any existing provider agreement/API rights.
- [ ] Offline requirements and available iPad/Surface/laptop test devices.
- [ ] Program access rules, reviewer assignments and pilot acceptance examples.

### Data, files and analytics

- [ ] Dedicated Franark Azure SQL server/database and network access path.
- [ ] Schema bootstrap account and scoped managed-identity runtime grants.
- [ ] SharePoint library or Blob destination and client/vendor document linkage.
- [ ] Access, retention, backup and restoration requirements.
- [ ] Approved reporting views and Power BI/Fabric access/capacity, if applicable.

### Model API and notifications

- [ ] Approved SFC API organization/project, model, data settings and usage limits.
- [ ] Server-side API key/Key Vault reference; synthetic live API test.
- [ ] Service mailbox, allowed recipients and approved notification wording.
- [ ] Microsoft Graph draft/send permissions and mailbox restrictions.

### Vendor transfers

- [ ] Current eCIRTS/WellSky/SAMS import/API specifications and permitted automation.
- [ ] Accepted sample files, mappings, code lists and external client identifiers.
- [ ] Test access, acknowledgement/rejection format and reconciliation examples.
- [ ] Billing/roster batch rules and duplicate prevention/retry requirements.

## Next implementation sequence

I will verify SFC sign-in and record scope with synthetic data, connect the approved
SQL/model/file accounts, then replace the test fixture with the verified form and
note template. Signature and vendor-transfer adapters follow the actual contracts.
Live tenant, device, SQL, model and provider tests remain separate from local tests.
