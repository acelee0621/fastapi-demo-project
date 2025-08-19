# app/core/redis_db.py
from fastapi import Request
from redis.asyncio import Redis
from app.core.config import settings

def create_auth_redis() -> Redis:
    return Redis.from_url(
        f"redis://{settings.REDIS_HOST}/1",
        max_connections=20,
        decode_responses=True,
    )

def create_cache_redis() -> Redis:
    return Redis.from_url(
        f"redis://{settings.REDIS_HOST}/2",
        max_connections=20,
        decode_responses=True,
    )
    
    
async def get_auth_redis(request: Request) -> Redis:
    return request.state.auth_redis

async def get_cache_redis(request: Request) -> Redis:
    return request.state.cache_redis