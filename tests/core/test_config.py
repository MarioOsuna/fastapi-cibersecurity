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
        Settings(_env_file=None)


def test_normalizes_postgres_url() -> None:
    s = Settings(database_url="postgres://user:pass@host:5432/db")
    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_normalizes_postgresql_url() -> None:
    s = Settings(database_url="postgresql://user:pass@host:5432/db")
    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_preserves_asyncpg_url() -> None:
    s = Settings(database_url="postgresql+asyncpg://user:pass@host:5432/db")
    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_preserves_sqlite_url() -> None:
    s = Settings(database_url="sqlite+aiosqlite:///./test.db")
    assert s.database_url == "sqlite+aiosqlite:///./test.db"


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
