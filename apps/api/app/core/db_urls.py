import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_DEFAULT_ASYNC = "postgresql+asyncpg://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"

# asyncpg does not accept libpq query params (sslmode, channel_binding) in the URL.
_ASYNC_STRIP_QUERY_KEYS = frozenset({"channel_binding", "sslmode"})
_SYNC_STRIP_QUERY_KEYS = frozenset({"channel_binding"})


def _strip_query_params(url: str, strip_keys: frozenset[str]) -> tuple[str, dict[str, str]]:
    parsed = urlparse(url)
    if not parsed.query:
        return url, {}
    pairs = parse_qsl(parsed.query)
    kept: list[tuple[str, str]] = []
    stripped: dict[str, str] = {}
    for key, value in pairs:
        if key in strip_keys:
            stripped[key] = value
        else:
            kept.append((key, value))
    clean = urlunparse(parsed._replace(query=urlencode(kept) if kept else ""))
    return clean, stripped


def get_async_database_url() -> str:
    """Neon/Render postgresql:// → asyncpg URL without libpq-only query params."""
    url = os.getenv("DATABASE_URL", _DEFAULT_ASYNC)
    url, _ = _strip_query_params(url, _ASYNC_STRIP_QUERY_KEYS)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_async_connect_args() -> dict:
    """SSL for asyncpg when Neon supplies sslmode=require in DATABASE_URL."""
    raw = os.getenv("DATABASE_URL", _DEFAULT_ASYNC)
    _, stripped = _strip_query_params(raw, _ASYNC_STRIP_QUERY_KEYS)
    sslmode = stripped.get("sslmode", "")
    if sslmode in ("require", "verify-ca", "verify-full", "prefer"):
        return {"ssl": True}
    if "neon.tech" in raw:
        return {"ssl": True}
    return {}


def get_sync_database_url() -> str:
    """Alembic/psycopg2 — keep sslmode in URL, drop channel_binding only."""
    explicit = os.getenv("DATABASE_URL_SYNC")
    if explicit:
        url = explicit.replace("postgresql+asyncpg://", "postgresql://", 1)
    else:
        url = os.getenv("DATABASE_URL", _DEFAULT_ASYNC).replace(
            "postgresql+asyncpg://", "postgresql://", 1
        )
    url, _ = _strip_query_params(url, _SYNC_STRIP_QUERY_KEYS)
    return url
