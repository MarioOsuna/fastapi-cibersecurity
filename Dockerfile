# ── builder ──────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:latest AS uv-bin

FROM python:3.11-slim AS builder

COPY --from=uv-bin /uv /usr/local/bin/uv

WORKDIR /build

# Cache deps layer separately from app code
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Now install the project itself
COPY app/ ./app/
RUN uv sync --frozen --no-dev

# ── runtime ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN adduser --system --uid 1000 --no-create-home appuser

COPY --from=builder /build/.venv /app/.venv

WORKDIR /app
COPY app/ ./app/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
