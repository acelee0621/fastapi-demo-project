# app/core/dependencies.py
from typing import Type, TypeVar, Callable, Protocol, Any
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis_db import get_cache_redis

# 引入需要的类
from app.domains.heroes.heroes_repo import HeroRepository
from app.domains.heroes.heroes_serv import HeroService
from app.domains.collections.collections_repository import CollectionRepository
from app.domains.collections.collections_service import CollectionService


# ---------- 协议 ----------
class _RepoProto(Protocol):
    """一个仓库类必须可以用 session 来初始化。"""

    def __init__(self, session: AsyncSession) -> None: ...


class _ServiceProto(Protocol):
    """一个服务类必须可以用一个 repository 对象来初始化。"""

    def __init__(self, repository: Any) -> None: ...


# ---------- 带 bound 的类型变量 ----------
T = TypeVar("T", bound=_ServiceProto)
R = TypeVar("R", bound=_RepoProto)


# ---------- 工厂 ----------
def get_service(service_cls: Type[T], repo_cls: Type[R]) -> Callable[..., T]:
    def _factory(session: AsyncSession = Depends(get_db)) -> T:
        return service_cls(repo_cls(session))

    return _factory


# ---------- 依赖项 ----------

# 专有的依赖项，不适用于通过工厂函数来构造，就单独写
def get_hero_service(
    session: AsyncSession = Depends(get_db), redis: Redis = Depends(get_cache_redis)
) -> HeroService:
    """Dependency for getting HeroService instance."""
    repository = HeroRepository(session)
    return HeroService(repository, redis)

# 通用依赖项，适用于通过工厂函数来构造
get_collection_service: Callable[..., CollectionService] = get_service(
    service_cls=CollectionService, repo_cls=CollectionRepository
)
