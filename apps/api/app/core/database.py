from datetime import datetime
from sqlalchemy import TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column

from app.core.db_urls import get_async_connect_args, get_async_database_url

DATABASE_URL = get_async_database_url()

engine = create_async_engine(
    DATABASE_URL,
    connect_args=get_async_connect_args(),
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),
    }


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
