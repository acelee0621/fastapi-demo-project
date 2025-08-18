# app/core/dependencies.py
from typing import Type, TypeVar, Callable, Protocol
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db


# ---------- 协议 ----------
class _RepoProto(Protocol):
    def __init__(self, session: AsyncSession) -> None: ...


class _ServiceProto(Protocol):
    def __init__(self, repository: _RepoProto) -> None: ...


# ---------- 带 bound 的类型变量 ----------
T = TypeVar("T", bound=_ServiceProto)
R = TypeVar("R", bound=_RepoProto)


# ---------- 工厂 ----------
def get_service(service_cls: Type[T], repo_cls: Type[R]) -> Callable[..., T]:
    def _factory(session: AsyncSession = Depends(get_db)) -> T:
        return service_cls(repo_cls(session))

    return _factory

