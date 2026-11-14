# Connect a model API

Create a project API key in the selected work API organization. Keep the key in
local `.env`. Select an available model that supports the Responses API and
JSON-schema structured outputs.

```text
FRANARK_RUNTIME=openai
FRANARK_MODEL=YOUR_AVAILABLE_MODEL_ID
OPENAI_API_KEY=YOUR_LOCAL_API_KEY
```

Docker:

```bash
docker compose up -d --force-recreate app
```

Python: stop and restart `franark serve`. The CLI loads local `.env` before
starting the application. When invoking Uvicorn directly, supply the environment
yourself.

Run the synthetic example first. The API adapter requests structured results,
sets an output-token limit, uses a 60-second request timeout, and disables
automatic SDK retries. The per-run call cap is separate from a dollar budget.

Notes and prior step outputs are sent to the configured provider in model mode.
The API key remains server-side. `store=False` disables Responses application
storage for these calls; provider logging and retention follow the applicable
API organization settings and terms.

References:

- [OpenAI quickstart](https://developers.openai.com/api/docs/quickstart)
- [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [API subscription-credit eligibility](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)
- [API data controls](https://developers.openai.com/api/docs/guides/your-data)
