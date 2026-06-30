FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev

COPY . .

EXPOSE 8001
CMD ["uv", "run", "python", "weather_server.py"]
