# app/lifespan.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI
from loguru import logger
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.database import setup_database_connection, close_database_connection
from app.core.redis_db import create_auth_redis, create_cache_redis


# Lifespan: 在应用启动时调用 get_settings，触发配置加载和缓存
class LifespanState(TypedDict, total=False):
    auth_redis: Redis
    cache_redis: Redis

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[LifespanState]:
    # -------- 启动 --------
    get_settings()
    await setup_database_connection()

    auth_redis  = create_auth_redis()
    cache_redis = create_cache_redis()

    await auth_redis.ping()
    await cache_redis.ping()
    logger.info("🚀 应用启动，数据库 & Redis 已就绪。")

    yield {"auth_redis": auth_redis, "cache_redis": cache_redis}

    # -------- 关闭 --------
    await close_database_connection()
    await auth_redis.aclose()
    await cache_redis.aclose()    
    logger.info("应用关闭，资源已释放。")