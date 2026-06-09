# Design: Threat Analysis API — Phase 1

**Date:** 2026-06-09  
**Status:** Approved  
**Scope:** Project scaffold, config, health endpoints, Docker base

---

## 1. Overview

A FastAPI-based security threat analysis API built for a cybersecurity SaaS portfolio.
Primary goal: demonstrate clean architecture, testability, and observability — not build
a production security product. The API ingests security events, calculates risk scores per
IP, and queries indicators of compromise (IOCs).

This spec covers Phase 1 only: project scaffold, tooling, configuration, health endpoints,
and Docker/compose base.

---

## 2. Stack

| Concern | Choice | Rationale |
|---|---|---|
| Runtime | Python 3.11+ | Type narrowing improvements, better async |
| Framework | FastAPI 0.115+ | Native async, Pydantic v2 native |
| Validation | Pydantic v2 | Required for settings + schemas |
| ORM | SQLAlchemy 2.0 async | Async-first, modern API |
| Dev DB | SQLite (aiosqlite) | Zero-dependency for local dev/tests |
| Prod DB | PostgreSQL 16 | Via docker-compose |
| Cache / RL | Redis 7 | Rate limiting + IOC cache |
| Package mgr | uv | Fast, lockfile reproducible |
| Linter/fmt | ruff | Replaces black + isort + flake8 |
| Type check | mypy strict | Catches errors at CI time |
| Testing | pytest + pytest-asyncio + httpx | Async-native test stack |
| Logging | structlog | Structured JSON, correlation IDs |
| Containers | Docker multi-stage + docker-compose | Dev parity + optimized image |

---

## 3. Directory Layout

```
fastapi-cibersecurity/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App factory, lifespan, middleware registration
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py           # GET /health, GET /health/ready
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── health.py               # HealthResponse, ReadinessResponse
│   ├── models/                     # Phase 2 — SQLAlchemy models
│   │   └── __init__.py
│   ├── repositories/               # Phase 2 — data access layer
│   │   └── __init__.py
│   ├── services/                   # Phase 3 — business logic / scoring engine
│   │   └── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── config.py               # Pydantic Settings
│       ├── logging.py              # structlog configuration
│       └── dependencies.py        # Depends factories (Phase 2+)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # app fixture, async client
│   └── api/
│       ├── __init__.py
│       └── test_health.py
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-06-09-threat-analysis-api-design.md
├── .github/
│   └── workflows/                  # Phase 7 — CI
├── Dockerfile                      # Multi-stage
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

**Why `v1/` from the start:** versioning the API prefix costs nothing now; retrofitting it
after clients exist is disruptive. `/api/v1/` is the convention, but health endpoints live
at root (`/health`, `/health/ready`) per K8s convention.

---

## 4. Configuration — `app/core/config.py`

```python
class Settings(BaseSettings):
    app_name: str = "Threat Analysis API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    database_url: str          # No default — fail fast on missing config
    redis_url: str = "redis://localhost:6379"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

`database_url` has no default so the app raises at startup (not at first DB call) if the
variable is missing. This is the "fail fast" pattern — important in containers where a
misconfigured pod should crash-loop rather than serve degraded responses.

`get_settings()` is wrapped with `@lru_cache` so Pydantic Settings is only parsed once per
process, not on every `Depends(get_settings)` call.

---

## 5. Health Endpoints

### `GET /health` — Liveness

Always returns 200 if the Python process is alive. Used by K8s `livenessProbe`.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-06-09T12:00:00Z"
}
```

### `GET /health/ready` — Readiness

Attempts:
1. `SELECT 1` on the DB connection pool
2. `PING` on the Redis connection

Returns 200 if both pass. Returns 503 with a JSON body listing which dependency failed
if either is unavailable. Used by K8s `readinessProbe` — a 503 removes the pod from the
load balancer without restarting it.

```json
// 503 example
{
  "status": "degraded",
  "checks": {
    "database": "ok",
    "redis": "error: Connection refused"
  }
}
```

**Phase 1 note:** In Phase 1, the readiness endpoint creates a fresh one-shot connection
(`aiosqlite.connect` + `redis.asyncio.from_url`) purely to verify reachability, then
closes it. The real connection pooling (SQLAlchemy `AsyncEngine`, shared Redis client)
is introduced in Phase 2 and injected via `Depends`. The readiness endpoint will be
updated in Phase 2 to use those pooled connections instead.

---

## 6. Application Factory — `app/main.py`

FastAPI uses a `lifespan` async context manager (not deprecated `on_startup`/`on_shutdown`
events) to manage resources. In Phase 1 the lifespan is a stub; Phase 2 adds DB pool init
and Redis client init inside it.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 2: init DB pool, Redis client
    yield
    # Phase 2: close connections

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router)       # /health, /health/ready
# Phase 4: app.include_router(events_router, prefix="/api/v1")
# Phase 4: app.include_router(threats_router, prefix="/api/v1")
```

---

## 7. Dockerfile — Multi-Stage

```dockerfile
# Stage 1: builder
FROM python:3.11-slim AS builder
RUN pip install uv
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Stage 2: runtime
FROM python:3.11-slim AS runtime
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ ./app/
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why multi-stage:** the builder stage pulls gcc/build-tools for packages with C extensions
(e.g., `psycopg2-binary`, `cryptography`). The runtime stage only receives compiled
`.so` files — no compiler toolchain. Typical result: ~200MB vs ~500MB image.

Non-root user (`appuser`, uid 1000) is a security best practice for container workloads.

---

## 8. docker-compose.yml

Three services:
- `api` — builds from local Dockerfile, `env_file: .env`
- `db` — `postgres:16-alpine`, named volume, healthcheck
- `redis` — `redis:7-alpine`, no persistence needed for dev

`api` depends on `db` and `redis` with `condition: service_healthy` so the API only starts
after both dependencies are accepting connections.

---

## 9. pyproject.toml Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]  # errors, pyflakes, isort, pyupgrade, bugbear, simplify

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["app"]

[tool.coverage.report]
fail_under = 85
```

---

## 10. Tests — Phase 1 Scope

`tests/conftest.py` provides:
- `app` fixture: the FastAPI app instance
- `async_client` fixture: `httpx.AsyncClient` with `ASGITransport`

`tests/api/test_health.py` covers:
- `GET /health` → 200, body has `status == "ok"`
- `GET /health/ready` → 200 when deps available; 503 when Redis unreachable (mock)

The Phase 1 readiness test mocks Redis/DB to simulate a failure and asserts the 503 with
the `checks` body — this exercises the error path without needing a real Redis in tests.

---

## 11. pre-commit Hooks

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff          # lint
      - id: ruff-format   # format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]
```

---

## 12. Out of Scope for Phase 1

- SQLAlchemy models and migrations (Phase 2)
- Repository and service layers (Phase 2-3)
- Scoring engine (Phase 3)
- Event/threat/indicator endpoints (Phase 4)
- Middleware and correlation IDs (Phase 5)
- Rate limiting (Phase 6)
- GitHub Actions CI (Phase 7)
