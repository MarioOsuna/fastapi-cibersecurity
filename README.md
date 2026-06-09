# Threat Analysis API

FastAPI microservice for cybersecurity threat analysis. Portfolio project demonstrating clean architecture, async SQLAlchemy, Redis, structured logging, and >85% test coverage.

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 + Pydantic v2 |
| Database | PostgreSQL (asyncpg) / SQLite (tests) |
| Cache / Rate limiting | Redis 7 |
| ORM | SQLAlchemy 2.0 async |
| Logging | structlog (JSON) |
| Package manager | uv |
| Linting / Formatting | ruff |
| Type checking | mypy strict |

## Quick Start

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), Docker + Compose.

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL and REDIS_URL

# 3. Start dependencies (Postgres + Redis)
docker compose up db redis -d

# 4. Run the API
uv run uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## Docker (full stack)

```bash
docker compose up --build
```

Starts the API, Postgres 16, and Redis 7. The API waits for both dependencies to pass their healthchecks before accepting traffic.

## Running Tests

```bash
# All tests with coverage report
uv run pytest --cov=app --cov-report=term-missing -v

# Single file
uv run pytest tests/api/test_health.py -v
```

Coverage threshold is 85% (enforced by `pytest-cov`). Current: **100%**.

## Code Quality

```bash
uv run ruff check app/ tests/      # lint
uv run ruff format app/ tests/     # format
uv run mypy app/                   # type check (strict)
```

Pre-commit hooks run all three automatically on every commit:

```bash
uv run pre-commit install   # one-time setup
```

## Architecture

```
app/
├── api/
│   └── v1/
│       └── health.py          # GET /health  (liveness)
│                              # GET /health/ready  (readiness)
├── core/
│   ├── config.py              # Pydantic Settings — DATABASE_URL required, fail-fast
│   ├── dependencies.py        # Depends() factories (Phase 2+)
│   └── logging.py             # structlog JSON pipeline
├── models/                    # SQLAlchemy ORM models (Phase 2)
├── repositories/              # Async DB access layer (Phase 2)
├── schemas/
│   └── health.py              # HealthResponse, ReadinessResponse
├── services/                  # Business logic (Phase 3)
└── main.py                    # create_app() factory + lifespan
tests/
├── api/
│   ├── test_health.py         # Endpoint integration tests
│   └── test_health_checks.py  # check_database / check_redis unit tests
├── core/
│   ├── test_config.py
│   └── test_logging.py
├── schemas/
│   └── test_health_schemas.py
└── conftest.py                # Fixtures: app() + async_client()
```

**Key design decisions:**

- `create_app()` factory pattern — enables per-test app instances with `dependency_overrides`.
- `check_database` / `check_redis` defined at module level — patchable via `unittest.mock.patch` without touching endpoints.
- Readiness endpoint returns `JSONResponse` directly — bypasses Pydantic response_model to allow HTTP 503.
- `@lru_cache` on `get_settings()` — settings parsed once per process.
- Liveness (`/health`) always returns 200 while the process is alive; readiness (`/health/ready`) returns 503 when dependencies are down, removing the pod from the load balancer without restarting it.

## Health Endpoints

```
GET /health        → 200 always (liveness probe)
GET /health/ready  → 200 if DB + Redis ok, 503 if either is down (readiness probe)
```

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","environment":"development","timestamp":"..."}

curl http://localhost:8000/health/ready
# {"status":"ok","checks":{"database":"ok","redis":"ok"}}
```

## Design Doc

Full architecture and phase-by-phase plan: [docs/architecture/2026-06-09-threat-analysis-api-design.md](docs/architecture/2026-06-09-threat-analysis-api-design.md)
