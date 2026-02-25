# syntax=docker/dockerfile:1

# ── Stage 1: build deps ───────────────────────────────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# Copy uv binary from the official image — no install script needed
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# uv is 10-100x faster than pip; --system writes to the image's Python directly
RUN uv pip install --system --no-cache .

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages and CLI entry-points (alembic, gunicorn, uvicorn...)
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run migrations then start gunicorn (config in gunicorn.conf.py)
CMD ["sh", "-c", "alembic upgrade head && gunicorn -c gunicorn.conf.py app.main:app"]
