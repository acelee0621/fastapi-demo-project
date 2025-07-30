from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from loguru import logger
from app.core.config import settings
from app.models.base import Base


# --- 1. 全局变量定义 ---
_engine: Optional[AsyncEngine] = None
_SessionFactory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("数据库引擎未初始化. 请先调用 setup_database_connection")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _SessionFactory is None:
        raise RuntimeError("会话工厂未初始化. 请先调用 setup_database_connection")
    return _SessionFactory


# --- 2. 通用的数据库初始化和关闭函数 ---
# 这些函数现在是通用的，可以在任何需要初始化数据库的地方调用。
# 它们负责设置全局的 engine 和 SessionFactory。
async def setup_database_connection():
    """
    初始化全局的数据库引擎和会话工厂。
    这是一个通用的设置函数，可以在 FastAPI 启动时调用。
    """
    global _engine, _SessionFactory
    if _engine is not None:
        logger.info("数据库已初始化，跳过重复设置。")
        return

    _engine = create_async_engine(
        settings.DB.DATABASE_URL,
        pool_size=settings.DB.POOL_SIZE,
        max_overflow=settings.DB.MAX_OVERFLOW,
        pool_timeout=settings.DB.POOL_TIMEOUT,
        pool_recycle=settings.DB.POOL_RECYCLE,
        echo=settings.DB.ECHO,
        pool_pre_ping=True,
    )
    _SessionFactory = async_sessionmaker(
        class_=AsyncSession, expire_on_commit=False, bind=_engine
    )
    logger.info("数据库引擎和会话工厂已创建。")


async def close_database_connection():
    """
    关闭全局的数据库引擎连接池。
    这是一个通用的关闭函数，可以在 FastAPI 关闭时调用。
    """
    global _engine, _SessionFactory
    if _engine:
        await _engine.dispose()
        _engine = None  # 清理引用
        _SessionFactory = None  # 清理引用
        logger.info("数据库引擎连接池已关闭。")


# --- 3. 依赖注入函数 ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    为每个请求或任务提供数据库会话。
    它现在依赖由 setup_database_connection 管理的全局 SessionFactory。
    """
    if _SessionFactory is None:
        # 这个错误通常不应该在正确配置的生产环境中出现
        # 它表明 setup_database_connection 未在应用启动时调用
        raise Exception("数据库未初始化。请检查 FastAPI 的 lifespan 启动配置。")

    async with _SessionFactory() as session:
        yield session


# --- 4. 数据库表创建工具 ---
async def create_db_and_tables():
    if not _engine:
        raise Exception("无法创建表，因为数据库引擎未初始化。")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建成功。")
