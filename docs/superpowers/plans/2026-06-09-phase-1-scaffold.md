# Threat Analysis API — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a production-quality FastAPI project with clean layer separation, Pydantic Settings, health endpoints (liveness + readiness), structlog JSON logging, Docker multi-stage build, docker-compose, pre-commit hooks, and full test coverage for the infrastructure layer.

**Architecture:** Layered `app/` root package — `core/` (config, logging), `api/v1/` (routers), `schemas/` (Pydantic), `models/` / `repositories/` / `services/` (stubs for later phases). All settings injected via `Depends(get_settings)`. Fresh one-shot connections for readiness checks in Phase 1; replaced by pooled connections in Phase 2.

**Tech Stack:** Python 3.11, FastAPI 0.115+, Pydantic v2, pydantic-settings, SQLAlchemy 2.0 async, aiosqlite, redis[asyncio], structlog, uv, ruff, mypy strict, pytest-asyncio, httpx, Docker multi-stage.

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Dependencies, ruff/mypy/pytest/coverage config |
| `.gitignore` | Python + uv ignores (uv.lock is committed) |
| `app/__init__.py` | Package marker |
| `app/main.py` | `create_app()` factory, lifespan stub, router registration |
| `app/core/config.py` | `Settings` (Pydantic BaseSettings), `get_settings()` with lru_cache |
| `app/core/logging.py` | `setup_logging()` — structlog JSON configuration |
| `app/core/dependencies.py` | Depends factories stub (Phase 2+) |
| `app/api/v1/health.py` | `GET /health`, `GET /health/ready`; `check_database()`, `check_redis()` helpers |
| `app/schemas/health.py` | `HealthResponse`, `ReadinessResponse` Pydantic models |
| `app/models/__init__.py` | Package marker (Phase 2) |
| `app/repositories/__init__.py` | Package marker (Phase 2) |
| `app/services/__init__.py` | Package marker (Phase 3) |
| `tests/conftest.py` | `app` fixture with settings override, `async_client` fixture |
| `tests/core/test_config.py` | Settings defaults, explicit values, missing required field |
| `tests/core/test_logging.py` | setup_logging runs, structlog is configured |
| `tests/schemas/test_health_schemas.py` | Schema instantiation and field validation |
| `tests/api/test_health.py` | /health 200, /health/ready 200+503 (mocked deps) |
| `Dockerfile` | Multi-stage: uv builder + slim runtime with non-root user |
| `docker-compose.yml` | api + postgres + redis services with healthchecks |
| `.env.example` | Environment variable template |
| `.pre-commit-config.yaml` | ruff + ruff-format + mypy hooks |
| `README.md` | Quick start, test instructions, architecture overview |

---

### Task 1: Project scaffold + pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `app/__init__.py`, `app/core/__init__.py`, `app/core/dependencies.py`
- Create: `app/api/__init__.py`, `app/api/v1/__init__.py`
- Create: `app/schemas/__init__.py`, `app/models/__init__.py`
- Create: `app/repositories/__init__.py`, `app/services/__init__.py`
- Create: `tests/__init__.py`, `tests/core/__init__.py`
- Create: `tests/api/__init__.py`, `tests/schemas/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "threat-analysis-api"
version = "0.1.0"
description = "Security threat analysis API — FastAPI portfolio project"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "aiosqlite>=0.20.0",
    "asyncpg>=0.29.0",
    "redis[hiredis]>=5.0.0",
    "structlog>=24.1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.1.0",
    "pytest-asyncio>=0.23.6",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
    "types-redis>=4.6.0",
    "sqlalchemy[mypy]>=2.0.30",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["app"]

[tool.coverage.report]
fail_under = 85
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.py[cod]
*.pyo
.venv/
.env
*.db
.coverage
htmlcov/
dist/
.mypy_cache/
.ruff_cache/
.pytest_cache/
```

Note: `uv.lock` is intentionally **not** gitignored — it must be committed for reproducible Docker builds.

- [ ] **Step 3: Create all package markers and stubs**

Create these as empty files (just `pass` or empty):

```
app/__init__.py
app/api/__init__.py
app/api/v1/__init__.py
app/schemas/__init__.py
app/models/__init__.py
app/repositories/__init__.py
app/services/__init__.py
app/core/__init__.py
tests/__init__.py
tests/core/__init__.py
tests/api/__init__.py
tests/schemas/__init__.py
```

Create `app/core/dependencies.py`:
```python
# Depends factories — populated in Phase 2
```

- [ ] **Step 4: Install dependencies**

```bash
uv sync
```

Expected: `.venv/` created, `uv.lock` generated, all packages installed. No errors.

- [ ] **Step 5: Commit scaffold**

```bash
git add pyproject.toml .gitignore app/ tests/
git commit -m "feat: project scaffold with uv + pyproject.toml"
```

---

### Task 2: Core config

**Files:**
- Create: `app/core/config.py`
- Create: `tests/core/test_config.py`

- [ ] **Step 1: Write failing test**

Create `tests/core/test_config.py`:

```python
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    s = Settings(database_url="sqlite+aiosqlite:///./test.db")
    assert s.app_name == "Threat Analysis API"
    assert s.app_version == "0.1.0"
    assert s.environment == "development"
    assert s.redis_url == "redis://localhost:6379"
    assert s.debug is False
    assert s.log_level == "INFO"


def test_settings_accepts_explicit_values() -> None:
    s = Settings(
        database_url="sqlite+aiosqlite:///./test.db",
        environment="staging",
        debug=True,
        log_level="DEBUG",
    )
    assert s.environment == "staging"
    assert s.debug is True
    assert s.log_level == "DEBUG"


def test_settings_missing_database_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
uv run pytest tests/core/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.core.config'`

- [ ] **Step 3: Create `.env` for local dev (gitignored)**

```bash
# Create .env (this file will not be committed)
cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./dev.db
REDIS_URL=redis://localhost:6379
EOF
```

- [ ] **Step 4: Implement `app/core/config.py`**

```python
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Threat Analysis API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    database_url: str
    redis_url: str = "redis://localhost:6379"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
uv run pytest tests/core/test_config.py -v
```

Expected:
```
tests/core/test_config.py::test_settings_defaults PASSED
tests/core/test_config.py::test_settings_accepts_explicit_values PASSED
tests/core/test_config.py::test_settings_missing_database_url_raises PASSED
tests/core/test_config.py::test_get_settings_is_cached PASSED
```

- [ ] **Step 6: Commit**

```bash
git add app/core/config.py tests/core/test_config.py
git commit -m "feat: core settings with Pydantic Settings v2 + lru_cache"
```

---

### Task 3: Structlog setup

**Files:**
- Create: `app/core/logging.py`
- Create: `tests/core/test_logging.py`

- [ ] **Step 1: Write failing test**

Create `tests/core/test_logging.py`:

```python
import logging

import structlog

from app.core.logging import setup_logging


def test_setup_logging_does_not_raise() -> None:
    setup_logging("INFO")


def test_setup_logging_configures_structlog() -> None:
    setup_logging("INFO")
    logger = structlog.get_logger("test")
    assert logger is not None


def test_setup_logging_sets_root_level_info() -> None:
    setup_logging("INFO")
    assert logging.getLogger().level == logging.INFO


def test_setup_logging_sets_root_level_warning() -> None:
    setup_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
uv run pytest tests/core/test_logging.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.core.logging'`

- [ ] **Step 3: Implement `app/core/logging.py`**

```python
import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
        force=True,
    )
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/core/test_logging.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core/logging.py tests/core/test_logging.py
git commit -m "feat: structlog JSON logging setup"
```

---

### Task 4: Health schemas

**Files:**
- Create: `app/schemas/health.py`
- Create: `tests/schemas/test_health_schemas.py`

- [ ] **Step 1: Write failing test**

Create `tests/schemas/test_health_schemas.py`:

```python
from datetime import datetime, timezone

from app.schemas.health import HealthResponse, ReadinessResponse


def test_health_response_fields() -> None:
    resp = HealthResponse(
        status="ok",
        version="0.1.0",
        environment="development",
        timestamp=datetime.now(timezone.utc),
    )
    assert resp.status == "ok"
    assert resp.version == "0.1.0"
    assert resp.environment == "development"


def test_readiness_response_ok() -> None:
    resp = ReadinessResponse(
        status="ok",
        checks={"database": "ok", "redis": "ok"},
    )
    assert resp.status == "ok"
    assert resp.checks["database"] == "ok"
    assert resp.checks["redis"] == "ok"


def test_readiness_response_degraded() -> None:
    resp = ReadinessResponse(
        status="degraded",
        checks={"database": "ok", "redis": "error: Connection refused"},
    )
    assert resp.status == "degraded"
    assert resp.checks["redis"].startswith("error:")
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
uv run pytest tests/schemas/test_health_schemas.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.schemas.health'`

- [ ] **Step 3: Implement `app/schemas/health.py`**

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, str]
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/schemas/test_health_schemas.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/schemas/health.py tests/schemas/
git commit -m "feat: health response schemas (HealthResponse, ReadinessResponse)"
```

---

### Task 5: App factory + test conftest

**Files:**
- Create: `app/main.py`
- Create: `tests/conftest.py`
- Create: `tests/api/test_health.py` (placeholder — full tests in Task 6)

- [ ] **Step 1: Write failing test**

Create `tests/api/test_health.py`:

```python
async def test_placeholder() -> None:
    pass  # Full health tests added in Task 6
```

Create `tests/conftest.py`:

```python
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app

_TEST_SETTINGS = Settings(
    database_url="sqlite+aiosqlite:///./test.db",
    redis_url="redis://localhost:6379",
)


@pytest.fixture
def app() -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: _TEST_SETTINGS
    return application


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
uv run pytest tests/api/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Implement `app/main.py`**

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    # Phase 2: init DB engine and Redis client here
    yield
    # Phase 2: close DB engine and Redis client here


def create_app() -> FastAPI:
    _app = FastAPI(
        title="Threat Analysis API",
        version="0.1.0",
        lifespan=lifespan,
    )
    # Phase 4: register exception handlers here
    # Phase 5: register middleware here
    return _app


app = create_app()
```

- [ ] **Step 4: Run test — expect PASS**

```bash
uv run pytest tests/api/test_health.py -v
```

Expected: `test_placeholder PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/conftest.py tests/api/test_health.py
git commit -m "feat: app factory with lifespan stub + async test client fixture"
```

---

### Task 6: Health endpoints

**Files:**
- Create: `app/api/v1/health.py`
- Modify: `app/main.py` — import and register health router
- Modify: `tests/api/test_health.py` — replace placeholder with full tests

- [ ] **Step 1: Write failing tests**

Replace `tests/api/test_health.py` entirely:

```python
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_liveness_returns_200(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200


async def test_liveness_body(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "development"
    assert "timestamp" in body


async def test_readiness_ok_returns_200(async_client: AsyncClient) -> None:
    with (
        patch("app.api.v1.health.check_database", new=AsyncMock(return_value="ok")),
        patch("app.api.v1.health.check_redis", new=AsyncMock(return_value="ok")),
    ):
        response = await async_client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"


async def test_readiness_503_when_redis_down(async_client: AsyncClient) -> None:
    with (
        patch("app.api.v1.health.check_database", new=AsyncMock(return_value="ok")),
        patch(
            "app.api.v1.health.check_redis",
            new=AsyncMock(return_value="error: Connection refused"),
        ),
    ):
        response = await async_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"].startswith("error:")


async def test_readiness_503_when_database_down(async_client: AsyncClient) -> None:
    with (
        patch(
            "app.api.v1.health.check_database",
            new=AsyncMock(return_value="error: unable to open database"),
        ),
        patch("app.api.v1.health.check_redis", new=AsyncMock(return_value="ok")),
    ):
        response = await async_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"].startswith("error:")
    assert body["checks"]["redis"] == "ok"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/api/test_health.py -v
```

Expected: 4 FAILURES — routes not registered yet, returns 404.

- [ ] **Step 3: Implement `app/api/v1/health.py`**

```python
from datetime import UTC, datetime
from typing import Annotated, Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


async def check_database(database_url: str) -> str:
    try:
        engine = create_async_engine(database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


async def check_redis(redis_url: str) -> str:
    try:
        r = aioredis.from_url(redis_url)
        await r.ping()
        await r.aclose()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


@router.get("/health", response_model=HealthResponse)
async def liveness(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/health/ready")
async def readiness(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    db_status = await check_database(settings.database_url)
    redis_status = await check_redis(settings.redis_url)

    checks = {"database": db_status, "redis": redis_status}
    all_ok = all(v == "ok" for v in checks.values())

    body: dict[str, Any] = {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }
    return JSONResponse(content=body, status_code=200 if all_ok else 503)
```

- [ ] **Step 4: Wire router into `app/main.py`**

Replace `app/main.py` entirely:

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    # Phase 2: init DB engine and Redis client here
    yield
    # Phase 2: close DB engine and Redis client here


def create_app() -> FastAPI:
    _app = FastAPI(
        title="Threat Analysis API",
        version="0.1.0",
        lifespan=lifespan,
    )
    _app.include_router(health_router)
    # Phase 4: register exception handlers here
    # Phase 5: register middleware here
    return _app


app = create_app()
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
uv run pytest tests/api/test_health.py -v
```

Expected:
```
tests/api/test_health.py::test_liveness_returns_200 PASSED
tests/api/test_health.py::test_liveness_body PASSED
tests/api/test_health.py::test_readiness_ok_returns_200 PASSED
tests/api/test_health.py::test_readiness_503_when_redis_down PASSED
tests/api/test_health.py::test_readiness_503_when_database_down PASSED
```

- [ ] **Step 6: Run full suite with coverage**

```bash
uv run pytest --cov=app --cov-report=term-missing -v
```

Expected: all tests PASS, coverage ≥ 85%.

- [ ] **Step 7: Commit**

```bash
git add app/api/v1/health.py app/main.py tests/api/test_health.py
git commit -m "feat: health endpoints — liveness and readiness with dependency checks"
```

---

### Task 7: Infrastructure files

**Files:**
- Create: `.env.example`
- Create: `Dockerfile`
- Create: `docker-compose.yml`

No automated tests — verified manually with `docker compose up`.

- [ ] **Step 1: Create `.env.example`**

```
# Application
APP_NAME="Threat Analysis API"
APP_VERSION="0.1.0"
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# Database
# SQLite for local dev:
DATABASE_URL=sqlite+aiosqlite:///./dev.db
# PostgreSQL for docker-compose:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/threat_analysis

# Redis
REDIS_URL=redis://redis:6379
```

- [ ] **Step 2: Create `Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Use official uv binary from the uv Docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies into .venv using the lockfile (reproducible)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user — security best practice for container workloads
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Copy the virtualenv from builder (compiled packages, no build tools)
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY app/ ./app/

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: threat_analysis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

- [ ] **Step 4: Commit**

```bash
git add .env.example Dockerfile docker-compose.yml
git commit -m "feat: multi-stage Dockerfile + docker-compose with postgres and redis"
```

---

### Task 8: Pre-commit hooks

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.7.0
          - pydantic-settings>=2.3.0
          - sqlalchemy[mypy]>=2.0.30
          - types-redis>=4.6.0
```

- [ ] **Step 2: Install hooks**

```bash
uv run pre-commit install
```

Expected: `pre-commit installed at .git/hooks/pre-commit`

- [ ] **Step 3: Run hooks on all files**

```bash
uv run pre-commit run --all-files
```

Expected: all hooks pass (or auto-fix style issues). If mypy reports errors, fix them before proceeding.

- [ ] **Step 4: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: pre-commit hooks (ruff + mypy)"
```

---

### Task 9: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

````markdown
# Threat Analysis API

A security threat analysis API built with FastAPI, demonstrating clean architecture,
async SQLAlchemy, Redis caching, and structured JSON logging.

Portfolio project for a cybersecurity SaaS context. Engineering focus: layered
architecture, rule-based scoring engine, observability, and comprehensive test coverage.

## Stack

Python 3.11 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 async · Redis · structlog · uv

## Quick Start

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for the interactive API documentation.

## Running Tests

```bash
# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html && open htmlcov/index.html
```

## Docker

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/threat_analysis
docker compose up --build
```

## Architecture

Layered architecture with dependencies pointing inward:

```
api/          → schemas, services, core
services/     → repositories, models, core
repositories/ → models, core
models/       → core
core/         → (no internal dependencies)
```

Each layer communicates through explicit interfaces. Business logic lives only in
`services/`. The scoring engine (`services/scoring/`) is a set of isolated rules,
each independently testable.

See [docs/superpowers/specs/2026-06-09-threat-analysis-api-design.md](docs/superpowers/specs/2026-06-09-threat-analysis-api-design.md)
for the full design document including architectural decisions.
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with quick start, test instructions, architecture overview"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run full test suite with coverage**

```bash
uv run pytest --cov=app --cov-report=term-missing -v
```

Expected: all tests PASS, coverage ≥ 85% for `app/`.

- [ ] **Step 2: Lint and format check**

```bash
uv run ruff check app/ tests/
uv run ruff format --check app/ tests/
```

Expected: no errors, no files would be reformatted.

- [ ] **Step 3: Type check**

```bash
uv run mypy app/
```

Expected: `Success: no issues found in N source files`

- [ ] **Step 4: Verify app starts and responds**

```bash
uv run uvicorn app.main:app --port 8001 &
sleep 2
curl -s http://localhost:8001/health | python3 -m json.tool
kill %1
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-06-09T..."
}
```

- [ ] **Step 5: Commit uv.lock + final state**

```bash
git add uv.lock
git commit -m "chore: Phase 1 complete — scaffold, config, health, Docker, pre-commit"
```
