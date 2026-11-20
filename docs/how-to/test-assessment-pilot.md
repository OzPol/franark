# Test the assessment pilot

The current form exercises the software flow with synthetic data. It is not a
701 form, a certified signing process or a configured vendor export.

## Start

From the `capability-foundation` checkout in PowerShell:

```powershell
./Start-Franark.ps1
```

The launcher preserves an existing `.env`, starts the app/docs containers, checks
health and opens `http://127.0.0.1:8765/portal`. Python launch remains
`franark serve` after installing the documented dependencies.

## Exercise the review loop

1. Select **Load synthetic example**. Use `SYN-001` as the client reference.
2. Enter a test signer and confirm the acknowledgement. Drawing is optional;
   typed acknowledgement provides the keyboard-accessible alternative.
3. Select **Validate and submit**. The saved data is frozen and a template note
   is generated. No API key is needed for rule validation or template rendering.
4. Enter a review resolution and select **Approve pilot record**. Local pilot
   administration permits self-review of this synthetic fixture only.
5. Download the PDF, note, JSON or CSV preview. The CSV escapes spreadsheet
   formula prefixes. None of these formats claims vendor import compatibility.
6. Select **Create correction draft**, change the birthdate and acknowledge the
   new revision. Submit again. The old record and acknowledgement remain fixed.
7. Inspect the changed-birthdate warning and its prior source link. A reviewer
   must resolve it before approval; validation errors require a corrected draft.
8. Download the unsent review email draft. No email has been sent.

With an OpenAI runtime/key/model configured, **Run AI quality review** makes a
bounded API call. The result is an advisory draft, cached for that submitted
revision. It cannot approve a record or change its answers. Provider tests begin
with synthetic data. The UI shows a connection requirement rather than a fake
model result when credentials are absent.

## Inspect the system

- `/architecture`: four context, stack, workflow and record diagrams.
- `/lab`: six callable information methods with observed metrics and references.
- **Connection readiness**: administrator-only configuration/backend report and
  collection checklist. No secrets are exposed by this endpoint.
- `http://127.0.0.1:8766`: complete documentation when the docs profile is running.

The hosted target is SFC's tenant. The local pilot binds to loopback and does
not provide tablet access from another device. SFC hosting/HTTPS/sign-in must be
verified before a remote-device test. Offline form storage is not implemented.
