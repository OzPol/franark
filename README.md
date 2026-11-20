# Franark

A local workbench for a configurable team of agents: project management,
coordination, operational work, domain analysis, review, and reporting.

**Repository name:** `franark`. Python package and CLI: `franark`. FRAN is the Project Manager; specialist agents form her working team.

## Start locally

With Docker Desktop running, copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Start the app and documentation:

```powershell
docker compose --profile docs up --build -d
```

Open the [workbench](http://127.0.0.1:8765) and
[documentation](http://127.0.0.1:8766). Select **Use sample**, then **Run workflow**.
Demo mode needs no API key.

## Information capabilities and research record

Open [Capabilities lab](http://127.0.0.1:8765/lab) to run six real, measured
information methods against editable synthetic examples. Methods include BM25
selection, versioned JSON differences, lossless DEFLATE encoding, field projection,
MMR sentence extraction and event-boundary timelines. They are callable through
the agent Toolbox and the OpenAI function-call adapter when configured.

The [method record](docs/research/methods.md) includes equations, source papers and
standards, adaptation choices and limitations. The [research ledger](docs/research/idea-log.md)
tracks the history; the [SFC portal plan](docs/explanations/sfc-portal-plan.md)
compares architecture, forms, signatures, identity, storage and export options.
Those portal integrations are proposed, not connected or deployed by this change.

For Linux/macOS, the copy command is `cp .env.example .env`.

## Included in v0.1

- Local browser dashboard for notes, workflow selection, agent activity, and reports.
- Ten configurable roles and a reusable agent/registry/workflow interface.
- General, IT, WellSky, and software assessment workflows.
- SQLite run history, event records, duplicate-request handling, and restart status.
- Demo runtime and an OpenAI Responses adapter with structured results and call limits.
- Sphinx/MyST documentation, templates with a version archive, issue forms, a
  portable issue backlog, user stories, architectural decisions, and CI checks.

Live model runs prepare action lists, proposed checks, and drafts from submitted
notes. Outlook, Teams, WellSky, SQL, ticketing, device access, and unattended
execution are separate integration milestones in [PROJECT.md](PROJECT.md).

## Tomorrow's launch

Read [START_HERE.md](START_HERE.md) for the short repository and Windows launch
sequence. Read [PROJECT.md](PROJECT.md) for milestones and issue IDs.

## Development

Create a Python environment, then install:

```bash
python -m pip install -c requirements.lock -e '.[openai,dev,docs]'
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

Build documentation:

```bash
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Start the browser app:

```bash
franark serve
```

Run a CLI demonstration:

```bash
franark demo
```

Python setup without Docker is documented in
[docs/how-to/run-with-python.md](docs/how-to/run-with-python.md).

## Collaboration

GitHub holds code, reviewed documentation, development issues, and pull requests.
The application holds operational runs and agent messages in local storage.
Agent identities are application configuration, so they need no GitHub invitations.

Runtime data and credentials are excluded from Git. Keep operational SFC records
in the configured work environment. Model mode sends the selected source packet
to the configured API provider; demo mode makes no model calls.
