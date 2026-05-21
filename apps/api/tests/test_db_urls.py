import os

from app.core.db_urls import get_async_database_url, get_sync_database_url


def test_neon_url_normalized_to_asyncpg(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@ep-abc.neon.tech/neondb?sslmode=require",
    )
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    assert get_async_database_url().startswith("postgresql+asyncpg://")
    assert get_sync_database_url().startswith("postgresql://")
    assert "+asyncpg" not in get_sync_database_url().split("://", 1)[0]


def test_explicit_sync_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/db")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql://u:p@host/db")
    assert get_sync_database_url() == "postgresql://u:p@host/db"
