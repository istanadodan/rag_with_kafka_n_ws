from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager, contextmanager
from core.config import settings
from typing import Generator, AsyncGenerator

# 모델 베이스
Base = declarative_base()

# Async엔지 생성
engine: AsyncEngine = create_async_engine(
    url=settings.db_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    # max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    future=True,
)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


# 의존성: FastAPI에서 DB 세션 제공
async def get_db():  # -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


@asynccontextmanager
async def db_session_ctx():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


# 테이블 생성 헬퍼
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


#############################################################################

from sqlalchemy import create_engine

sync_engine = create_engine(
    settings.db_url.replace("+asyncpg", ""),  # 중요
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    pool_pre_ping=True,
    pool_recycle=3600,
)


# sql 사용가능한 connection pool
@contextmanager
def get_rdb():
    conn = sync_engine.raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
    finally:
        conn.close()
