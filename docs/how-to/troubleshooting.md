# Troubleshooting

| Symptom | Check or action |
|---|---|
| Docker client cannot reach server | Open Docker Desktop and check `docker version` for a Server section. |
| Port 8765 is occupied | Stop the application already using it, or change the host side of the Compose port mapping. |
| API mode is not configured | Set both the API key and model in `.env`, then recreate the app container. |
| Model run fails with AuthenticationError | Confirm the local key belongs to the intended API project and is active. |
| Model run fails with RateLimitError | Check API project balance and applicable rate limits. |
| Model run fails with ValueError | Check model support for structured outputs and the output-token cap; incomplete results stop the run. |
| A run needs input | Inspect the recorded questions; provide the missing source information in the next run. |
| Reviewer rejects a result | Inspect the specific defects and prepare a corrected run. Automatic rework is a later milestone. |
| Run is interrupted | Inspect saved steps. Restarted processes do not silently replay paid calls. |
| Demo shows only outlines | Demo uses literal ACTION lines and fixed role outlines. Enable model mode for analysis of ordinary notes. |

To inspect application startup:

```bash
docker compose logs --tail 100 app
```

The app stores exception types rather than full provider error payloads. This
keeps source packets and credentials out of run error messages.
