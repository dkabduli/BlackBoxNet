import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_DEFAULT_ASYNC = "postgresql+asyncpg://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"

# Neon connection strings often include channel_binding=require; asyncpg rejects it.
_STRIP_QUERY_KEYS = frozenset({"channel_binding"})


def _normalize_postgres_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return url
    filtered = [(k, v) for k, v in parse_qsl(parsed.query) if k not in _STRIP_QUERY_KEYS]
    if len(filtered) == len(parse_qsl(parsed.query)):
        return url
    return urlunparse(parsed._replace(query=urlencode(filtered)))


def get_async_database_url() -> str:
    """Neon and Render provide postgresql:// — normalize for asyncpg."""
    url = os.getenv("DATABASE_URL", _DEFAULT_ASYNC)
    url = _normalize_postgres_url(url)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_sync_database_url() -> str:
    """Alembic migrations use a sync driver URL."""
    explicit = os.getenv("DATABASE_URL_SYNC")
    if explicit:
        url = explicit.replace("postgresql+asyncpg://", "postgresql://", 1)
    else:
        url = os.getenv("DATABASE_URL", _DEFAULT_ASYNC).replace(
            "postgresql+asyncpg://", "postgresql://", 1
        )
    return _normalize_postgres_url(url)
