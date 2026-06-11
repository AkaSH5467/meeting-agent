import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker | None = None


def _build_url() -> str:
    """
    Builds the asyncpg connection URL.
    For Cloud SQL on Cloud Run: uses unix socket path.
    For local dev: uses TCP with host/port.
    Set CLOUD_SQL_UNIX_SOCKET=1 in Cloud Run environment to switch.
    """
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASS"]
    db = os.environ["DB_NAME"]

    if os.getenv("CLOUD_SQL_UNIX_SOCKET"):
        # Cloud Run unix socket path
        instance = os.environ["CLOUD_SQL_INSTANCE"]  # project:region:instance
        socket_dir = f"/cloudsql/{instance}"
        return f"postgresql+asyncpg://{user}:{password}@/{db}?host={socket_dir}"
    else:
        # Local dev — direct TCP
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = os.getenv("DB_PORT", "5432")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


async def create_engine() -> AsyncEngine:
    global _engine
    if _engine is not None:
        return _engine
    url = _build_url()
    _engine = create_async_engine(
        url,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
        echo=False,
    )
    return _engine


async def create_tables() -> None:
    eng = await create_engine()
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def ping_db() -> bool:
    try:
        eng = await create_engine()
        async with eng.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database ping failed: {e}")
        return False


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    global _session_maker
    if _session_maker is None:
        eng = await create_engine()
        _session_maker = async_sessionmaker(eng, expire_on_commit=False)
    async with _session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_connector() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None