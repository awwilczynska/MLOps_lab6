# MLOps Laboratory 13 - homework
# Trip Planning Assistant — Gemini Solution

Terminal chat assistant using Google Gemini API, a custom OpenWeatherMap MCP server,
remote Tavily MCP, and optional Guardrails safety validators.

> **Deviation from task spec — vLLM replaced by Gemini API:**
> The task specifies vLLM as the LLM backend. However, the official vLLM Docker image
> requires CUDA and does not run on a CPU-only machine. A CPU-only vLLM build is possible
> but inference on even the smallest models (e.g. Qwen3-0.6B) takes several minutes per
> response, making the assistant unusable for interactive testing. For this reason I decided
> to use the Google Gemini API with the OpenAI-compatible client — it exposes the same
> REST interface, so the same OpenAI Python client, tool-calling loop, and MCP integration
> work identically — the full agent architecture is preserved.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Internet access (Gemini API + Tavily are remote services)

---

## Step 1 — Get the required API keys

You need **three** keys (all free tiers work). Get them before continuing.

| Key | Where to get it |
|-----|-----------------|
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → click **Create API key** |
| `OPENWEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) → subscribe to **Free** plan → copy key from *My API keys* |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) → sign up → copy the API key from the dashboard |

Optional fourth key (enables stronger safety filters):

| Key | Where to get it |
|-----|-----------------|
| `GUARDRAILS_API_KEY` | [hub.guardrailsai.com](https://hub.guardrailsai.com) → sign up → copy token |

> **Note:** OpenWeatherMap keys can take up to 2 hours to activate after registration.
>
> **Note on free-plan limitations:** The OpenWeatherMap free plan only supports a 5-day (3-hourly) forecast. The 16-day forecast and monthly statistics endpoints require a paid plan. Monthly climate data is therefore fetched from the [Open-Meteo historical archive](https://open-meteo.com/en/docs/historical-weather-api) instead, which is completely free and requires no API key.

---

## Step 2 — Create the `.env` file

In this directory (`homework/`) create a `.env` file with the following content, replacing placeholders with your real keys:

```
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=<your-gemini-api-key>
OPENWEATHER_API_KEY=<your-openweathermap-api-key>
TAVILY_API_KEY=<your-tavily-api-key>
GUARDRAILS_API_KEY=        ← leave empty if you skipped this key
```

---

## Step 3 — Build and start the services

```bash
docker compose up -d --build
```

This builds and starts two containers in the background:

| Container | What it does |
|-----------|-------------|
| `weather-mcp` | FastMCP HTTP server exposing OpenWeatherMap tools on port 8001 |
| `trip-chat` | The Python chat app, waiting for `weather-mcp` to be healthy |

First build takes **3–5 minutes** (downloads Python, installs packages).
Subsequent starts are instant (layers are cached).

Check that both containers are running:

```bash
docker compose ps
```

Both should show **`healthy`** or **`running`** under *Status*.

---

## Step 4 — Start the chat

Attach your terminal to the chat container:

```bash
docker attach trip-chat
```

Press ENTER

You will see:

```
============================================================
  Trip Planning Assistant  (powered by Gemini API)
  Type your question, or press Ctrl+C to exit.
============================================================

You:
```

Type your question and press **Enter**. Example questions to try (checked by me):

- `I want to visit Rome in July. What should I pack?`
- `I'm going to Barcelona in November. Can you recommend any cheap places to stay?`
- `What's the weather in Tokyo for the next 5 days?`
- `Plan a 5-day trip to Barcelona for me`
- `What is the capital of France?`
- `Write me a poem about life` ← model will refuse (not travel-related)
- `What's the weather in Toronto for the next 9 days?` ← model will inform it can only provide up to 5 days and ask if you want a 5-day forecast instead

When the model fetches data, you will see tool calls printed:

```
  [tool] get_daily_forecast({'city': 'Tokyo', 'days': 5})
```

---

## Step 5 — Exit the chat

Press **Ctrl+C** inside the attached terminal. The chat exits cleanly.

To detach without stopping the container (leave it running): press **Ctrl+P** then **Ctrl+Q**.

---

## Step 6 — Stop all services

```bash
docker compose down
```

---

## Troubleshooting

**`trip-chat` container exits immediately on start**
The chat container waits for `weather-mcp` to be healthy. If `weather-mcp` fails to start, check its logs:
```bash
docker compose logs weather-mcp
```
The most common cause is a missing or invalid `OPENWEATHER_API_KEY` in `.env`.

**`[warning] Could not connect to MCP server 'tavily'`**
Your `TAVILY_API_KEY` is missing or invalid. The assistant will still work but without web search.

**`[error] Could not generate a response`**
Your `GEMINI_API_KEY` is missing or invalid. Verify it in `.env` and rebuild:
```bash
docker compose down
docker compose up -d --build
docker attach trip-chat
```

**Guardrails validators not found**
If you did not provide `GUARDRAILS_API_KEY`, the app prints:
```
[info] Guardrails Hub validators not installed – security relies on system prompt only.
```
This is expected and the assistant works normally.
