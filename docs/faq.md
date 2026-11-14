# Frequently asked questions

## Do agents need separate ChatGPT accounts?

No. They are configured runtime instances sharing a workflow and state store.
The API adapter uses the chosen API project's credentials.

## Do I invite agents to GitHub or a ChatGPT group?

No. GitHub access is for development collaboration. Agent handoffs and messages
are recorded inside Franark. A ChatGPT-to-Franark submission tool can be added
as a separate integration later.

## Where do the app and agents run?

The app and workflow engine run on the computer hosting the service. Model mode
calls the configured cloud API. Demo mode is local and deterministic.

## Is Plus enough to start?

The demo needs no model subscription. Live API mode uses an API project/key and
its available credits. Plus does not include the current Pro/Business API-credit
benefit. Subscription-based Codex adapters are a separate possible integration.

## Can the app change WellSky settings or send emails now?

The local pilot prepares findings, proposed checks, and drafts. External actions
are added through the planned work adapters and their project permissions.

## Why have both FRAN and a Coordinator?

FRAN owns outcomes, priorities, and project communication. The Coordinator
assigns work, tracks execution, and manages dependencies against that plan.

## Is a reviewer verdict independent proof?

It is a recorded review result. Actual support comes from source checks,
calculations, tests, and observed outcomes. The engine keeps the reviewing
instance separate from the worker on the same deliverable.

## How does the documentation stay consistent?

One role catalog generates its reference page. Templates record their versions,
older structures have an archive, Git records edits, and CI builds the docs
with warnings treated as errors.
