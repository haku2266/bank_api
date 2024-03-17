from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator, Generator

from src.config import settings

# asynchronous engine
async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
)

# synchronous engine
# sync_engine = create_engine(
#     url=settings.DATABASE_URL_psycopg,
#     echo=True,
# )

# asynchronous local session
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# synchronous local session
# SyncSessionLocal = sessionmaker(bind=sync_engine,
#                                 autocommit=False,
#                                 autoflush=False,
#                                 expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# async def get_sync_session() -> Generator[Session, None]:
#     async with SyncSessionLocal() as session:
#         yield session


class Base(DeclarativeBase):
    pass
