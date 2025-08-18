# app/domains/users/auth_dependencies.py
# from fastapi import Depends, HTTPException, status
# import jwt
# from jwt.exceptions import PyJWTError
# from app.core.config import settings
# from app.core.security import oauth2_scheme
# from app.domains.users.service_dependencies import get_user_service
# from app.domains.users.user_service import UserService
# from app.schemas.users import UserResponse


# 将get_current_user函数进一步拆分
# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     service: UserService = Depends(get_user_service),
# ) -> UserResponse:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         payload = jwt.decode(
#             token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
#         )
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#     except PyJWTError:
#         raise credentials_exception

#     user = await service.get_user_by_username(username)
#     if user is None:
#         raise credentials_exception
#     return UserResponse.model_validate(user)


from typing import Annotated

import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, status
from pydantic import ValidationError
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import oauth2_scheme
from app.core.redis_db import get_auth_redis
from app.domains.users.service_dependencies import get_user_service
from app.domains.users.user_service import UserService
from app.schemas.users import UserResponse


# ---------- 配置 ----------
CACHE_TTL = 60 * 15  # 缓存过期时间 15 分钟


# ---------- 辅助 ----------
async def _username_from_token(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """
    把 token 解包，直接返回 username；不合法就抛 401。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (PyJWTError, ValidationError):
        raise credentials_exception
    return username


# ---------- 主依赖 ----------
async def get_current_user(
    username: Annotated[str, Depends(_username_from_token)],
    redis: Annotated[Redis, Depends(get_auth_redis)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    1. 先查缓存
    2. 缓存没命中 -> 查数据库 -> 写回缓存
    3. 用户不存在 -> 401
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # 查缓存
    key = f"user:{username}"
    cached = await redis.get(key)
    if cached:
        user = UserResponse.model_validate_json(cached)
    else:
        # 缓存没命中 -> 查数据库
        user_orm = await service.get_user_by_username(username)
        if user_orm is None:
            raise credentials_exception
        user = UserResponse.model_validate(user_orm)

        # 写回缓存
        await redis.set(key, user.model_dump_json(), ex=CACHE_TTL)

    return user
