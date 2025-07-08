from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config.config import database_settings

engine = create_async_engine(
    str(database_settings.DATABASE_URL),
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def db_session() -> AsyncIterator[AsyncSession]:
    """
    Database Session Generator.

    :return: A database session.
    """
    async with async_session() as session:  # type: AsyncSession
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    """
    Asynchronous context manager that provides a SQLAlchemy session with transaction management.

    This function yields an active SQLAlchemy AsyncSession that automatically begins a transaction.
    The transaction is committed when the context exits successfully, and rolled back if an exception occurs.

    Yields:
        AsyncSession: An active SQLAlchemy asynchronous session for performing database operations.
    """
    async with async_session() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


class Base(DeclarativeBase):
    """
    Base class for defining main database tables.
    """

    pass
