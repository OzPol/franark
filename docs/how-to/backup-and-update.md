# Back up and update the local installation

The Docker installation uses the `franark_data` named volume. Container
recreation keeps that volume. The Python installation uses the local `data`
folder by default.

To take a consistent Docker backup, stop the app first:

```bash
docker compose stop app
```

Create a local `backups` directory, then copy the database:

```bash
docker compose cp app:/app/data/franark.sqlite3 ./backups/franark.sqlite3
```

Restart the app:

```bash
docker compose start app
```

For an update, stop the app, take the backup, pull reviewed repository changes,
then rebuild:

```bash
docker compose --profile docs up --build -d
```

Backups contain the submitted source notes and agent outputs. Keep them in the
designated work location. The application marks unfinished runs as interrupted
after a restart so you can inspect completed steps before starting a new run.
