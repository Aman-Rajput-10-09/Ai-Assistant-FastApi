from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

engine_kwargs = {"echo": settings.DEBUG, "pool_pre_ping": True}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Async session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Declarative base
class Base(DeclarativeBase):
    pass


# Dependency to get async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
