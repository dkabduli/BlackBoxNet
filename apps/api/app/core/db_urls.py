import os

_DEFAULT_ASYNC = "postgresql+asyncpg://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"


def get_async_database_url() -> str:
    """Neon and Render provide postgresql:// — normalize for asyncpg."""
    url = os.getenv("DATABASE_URL", _DEFAULT_ASYNC)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_sync_database_url() -> str:
    """Alembic migrations use a sync driver URL."""
    explicit = os.getenv("DATABASE_URL_SYNC")
    if explicit:
        return explicit.replace("postgresql+asyncpg://", "postgresql://", 1)
    url = os.getenv("DATABASE_URL", _DEFAULT_ASYNC)
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)
