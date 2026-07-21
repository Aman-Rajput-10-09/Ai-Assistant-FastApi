import os
from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

def _normalize_database_url(database_url: str) -> tuple[str, dict]:
    """Return a SQLAlchemy async URL and asyncpg connect args."""
    connect_args = {}

    if database_url.startswith("postgres://"):
        database_url = "postgresql+asyncpg://" + database_url[len("postgres://"):]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+asyncpg://" + database_url[len("postgresql://"):]

    if database_url.startswith("postgresql+asyncpg://"):
        split_url = urlsplit(database_url)
        query_params = dict(parse_qsl(split_url.query, keep_blank_values=True))

        sslmode = query_params.pop("sslmode", None)
        if sslmode:
            if sslmode in {"require", "prefer", "verify-ca", "verify-full"}:
                connect_args["ssl"] = True
            elif sslmode == "disable":
                connect_args["ssl"] = False

        database_url = urlunsplit(
            (
                split_url.scheme,
                split_url.netloc,
                split_url.path,
                urlencode(query_params),
                split_url.fragment,
            )
        )
        connect_args["timeout"] = settings.DB_CONNECT_TIMEOUT_SECONDS

    return database_url, connect_args


database_url, connect_args = _normalize_database_url(settings.DATABASE_URL)

engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
    "connect_args": connect_args,
}

is_sqlite = database_url.startswith("sqlite")
is_vercel = os.getenv("VERCEL") == "1"

if not is_sqlite:
    if is_vercel:
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_async_engine(database_url, **engine_kwargs)

# Async session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Declarative base
class Base(DeclarativeBase):
    pass


_db_initialized = False


# Dependency to get async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    global _db_initialized
    if not _db_initialized:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _db_initialized = True
        except Exception:
            pass

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
