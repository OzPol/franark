# Proposed SFC portal user stories

My requirements record, started 2026-11-19. These describe the target capabilities;
the synthetic pilot implements a test subset. Program staff must validate the
real form, workflow rules and acceptance examples before their pilot.

| ID | User story | Observable acceptance condition |
|---|---|---|
| SFC-HUB-001 | As an employee, I can open the SFC resource hub using my Microsoft work identity. | Authorized app assignments succeed; unassigned identities and out-of-scope record requests are denied by the API. |
| SFC-FRM-001 | As case management, nutrition, Friendship at Home, CRC or Friendship Centers staff, I can find the right form for my program. | Form catalog identifies owner/version/effective dates and shows only authorized submissions. |
| SFC-FRM-002 | As staff, I can complete a form on an iPad, Surface or touch laptop without printing and retyping it. | Required fields, conditional questions, codes, drafts and clear errors match the chosen real form; accessibility and target-device checks pass. Offline behavior remains a decision. |
| SFC-SIG-001 | As a client, I can sign the appropriate document in a supported staff-assisted or remote flow. | The signer, consent, form revision, document hash, timestamp and provider/audit evidence remain linked; a change creates a new revision with an explicit signing policy. |
| SFC-DOC-001 | As authorized staff, I can retrieve attachments from the correct client or vendor record. | File ID/version, owner, scope and relational links are preserved; unauthorized download links fail; exports retain the required document association. |
| SFC-NTE-001 | As a case worker, I receive a case-note draft in the required template from submitted assessment values. | Every factual statement traces to entered values or authorized evidence; missing information stays explicit; staff can correct and release a versioned draft. |
| SFC-QA-001 | As a reviewer, I see possible mistakes before records are released. | Deterministic checks and optional model findings show field/source evidence, severity, review owner and correction history; no model silently edits the assessment. |
| SFC-MSG-001 | As a submitter, I receive respectful, specific requests to check an inconsistency. | An assigned in-app item links to the comparison; optional email uses an approved tone/sender and avoids unnecessary client details; duplicate notifications are suppressed. |
| SFC-EXP-001 | As operations staff, I can preview and release a supported export for eCIRTS, WellSky/SAMS, billing or roster updates. | Destination schema/version is verified; approved input revision maps reproducibly; receipts, per-record rejections, totals and duplicate prevention are recorded. No connector is presumed available. |
| SFC-KNW-001 | As an employee, I can find current FAQs and how-to resources without searching unrelated client files. | Published entries cite approved sources, owner and effective version; agent drafts pass editorial review; access rules prevent client-data disclosure. |
| SFC-VND-001 | As a vendor, I can submit designated material without seeing employee resources or other vendor/client records. | A scoped guest/invitation route allows only the designated operation and resource; access can expire or be revoked. |
| SFC-ANL-001 | As an authorized analyst, I can report on standardized records and process performance. | Approved views/datasets reconcile to submissions and respect scope; Power BI/Fabric connection and capacity are verified separately. |
| SFC-RES-001 | As the platform owner, I can inspect how agent information methods affect quality, latency and resource use. | Method/workflow/model identities, dataset versions, settings, observed usage and scored outcomes can be traced and reproduced without placing operational data in Git. |

The design alternatives and unresolved requirements are maintained in
[the SFC portal plan](sfc-portal-plan.md). The synthetic pilot demonstrates form entry, review, corrections, generic outputs
and research measurements. Actual program forms, live SFC connections and
production acceptance remain separate from these demonstrations.
