# Complete a first run

Prerequisite: the populated repository and Docker Desktop, or the Python setup.

1. Copy `.env.example` to `.env`.
2. Leave `FRANARK_RUNTIME=demo`.
3. Run `docker compose --profile docs up --build -d`.
4. Open <http://127.0.0.1:8765>.
5. Select **IT and vendor assessment**, then **Use sample**.
6. Click **Run workflow** and inspect the events.
7. Download the report after the final draft review.

The sample uses literal `ACTION:` lines. The demo processes those lines and
shows the configured handoffs. Live model mode analyzes ordinary notes using
the same result contract.

Expected result: ten IT workflow steps, a finished status, a reviewed draft, and
saved history that remains after restarting the application.

For API setup, see [Connect a model](../how-to/connect-model.md).
