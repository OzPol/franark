# Start Franark locally

Repository: <https://github.com/OzPol/franark>. FRAN is the Project Manager, supported by a configurable team of specialist agents.

## 1. Prepare Docker

Install or open [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
Use the Linux container environment. Follow Docker's installation guidance if
Windows asks for WSL setup or a restart. Organization licensing depends on the
applicable Docker Desktop terms.

In PowerShell, check:

```powershell
docker version
```

Then check:

```powershell
docker compose version
```

The first command should show a reachable Server section. If Docker installation
is unavailable on the machine, use the Python guide in `docs/how-to`.

## 2. Clone the repository

```powershell
git clone https://github.com/OzPol/franark.git
```

Enter the repository:

```powershell
cd franark
```

Create your local configuration:

```powershell
Copy-Item .env.example .env
```

The default runtime is `demo`. Leave it that way for the first run.

## 3. Start the workbench and documentation

```powershell
docker compose --profile docs up --build -d
```

Check the services:

```powershell
docker compose ps
```

Open:

- Workbench: <http://127.0.0.1:8765>
- Sphinx documentation: <http://127.0.0.1:8766>
- Capabilities lab: <http://127.0.0.1:8765/lab>

The initial image builds download packages. Later starts reuse the built images.

## 4. Complete the first workflow

1. Select **IT and vendor assessment**.
2. Click **Use sample**.
3. Click **Run workflow**.
4. Open the run and inspect the assignment and result events.
5. Confirm the final draft review is accepted and the run is finished.
6. Download the report.
7. Restart the app and confirm the run history is still present.

```powershell
docker compose restart app
```

This verifies the launch, workflow order, persistence, and report path.

## 5. Enable live model analysis when ready

Create an API project/key under the chosen work account at
<https://platform.openai.com/api-keys>. Select a model available to that project
that supports structured outputs. Put the values in local `.env`:

```text
FRANARK_RUNTIME=openai
FRANARK_MODEL=YOUR_AVAILABLE_MODEL_ID
OPENAI_API_KEY=YOUR_LOCAL_API_KEY
```

Recreate the app container so changed environment values take effect:

```powershell
docker compose up -d --force-recreate app
```

Run the synthetic sample first, then a small authorized work source. The UI shows
the runtime and notes that model runs use billable API calls. The IT workflow
has ten agent steps; information tools can add follow-up model requests. The
configured cap stops requests when reached, so inspect usage before increasing it.
Call, tool-round and output-token limits are available in `.env`. They are not a
hard dollar budget.

ChatGPT Plus and the API have separate usage accounting. Current subscription
API-credit benefits apply to eligible Pro and Business subscriptions; check the
API project's balance independently.

## 6. Continue development

The next implementation work should establish structured
action records and evaluation examples, then connect one source and one output
destination. Keep development issues in GitHub and operational tickets in their
designated SFC system.

Useful operations:

```powershell
docker compose logs --tail 100 app
```

```powershell
docker compose stop
```

If you close the laptop or it sleeps, local work pauses. A later always-on work
computer or server can run the same application configuration.
