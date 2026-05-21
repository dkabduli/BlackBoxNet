import os

from app.core.db_urls import (
    get_async_connect_args,
    get_async_database_url,
    get_sync_database_url,
)


def test_neon_url_normalized_to_asyncpg(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@ep-abc.neon.tech/neondb?sslmode=require",
    )
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    async_url = get_async_database_url()
    assert async_url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in async_url
    assert get_async_connect_args() == {"ssl": True}
    sync_url = get_sync_database_url()
    assert sync_url.startswith("postgresql://")
    assert "sslmode=require" in sync_url
    assert "+asyncpg" not in sync_url.split("://", 1)[0]


def test_explicit_sync_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/db")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql://u:p@host/db")
    assert get_sync_database_url() == "postgresql://u:p@host/db"
    assert get_async_connect_args() == {}


def test_strips_channel_binding_for_neon(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@ep-abc.neon.tech/neondb?sslmode=require&channel_binding=require",
    )
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    async_url = get_async_database_url()
    assert "channel_binding" not in async_url
    assert "sslmode" not in async_url
    assert get_async_connect_args() == {"ssl": True}
