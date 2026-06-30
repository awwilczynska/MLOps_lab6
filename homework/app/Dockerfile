FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev

# Install Guardrails Hub validators.
# GUARDRAILS_API_KEY is a build-time secret; if omitted, validators are skipped
# and the app falls back to system-prompt-only security.
ARG GUARDRAILS_API_KEY=""
RUN if [ -n "$GUARDRAILS_API_KEY" ]; then \
        printf 'n\n' | uv run guardrails configure --token "$GUARDRAILS_API_KEY" --enable-metrics false && \
        uv run guardrails hub install hub://guardrails/detect_jailbreak && \
        uv run guardrails hub install hub://guardrails/toxic_language; \
    fi

COPY . .

CMD ["uv", "run", "python", "app.py"]
