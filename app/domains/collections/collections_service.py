# app/domains/collections/collections_service.py
import math

from app.core.exceptions import ForbiddenException
from app.domains.collections.collections_repository import CollectionRepository
from app.schemas.collections import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    CollectionResponseDetail,
)
from app.schemas.response import DetailResponse, ListResponse, Meta, PaginationInfo
from app.models.users import User
from app.models.collections import Collection


class _OwnerScopedRepo:
    """
    一个内部的、轻量级的仓库代理。
    它的职责是在调用真正的仓库方法之前，动态地注入所有权逻辑。
    """

    def __init__(self, repository: CollectionRepository, user: User):
        self._repo = repository
        self._user = user

    async def create(self, *, obj_in: CollectionCreate) -> Collection:
        return await self._repo.create(obj_in=obj_in, user_id=self._user.id)

    async def get(self, *, id: int) -> Collection:
        # 获取后检查所有权
        db_obj = await self._repo.get(id=id)
        if db_obj.user_id != self._user.id:
            raise ForbiddenException("Access denied.")
        return db_obj

    async def get_list(self, **kwargs) -> tuple[int, list[Collection]]:
        # 自动注入 user_id 过滤器
        kwargs["user_id"] = self._user.id
        return await self._repo.get_list(**kwargs)

    async def update(self, *, id: int, obj_in: CollectionUpdate) -> Collection:
        # 先用带权限的 get 检查所有权
        db_obj = await self.get(id=id)
        # 再调用无权限的 repo.update
        return await self._repo.update(db_obj=db_obj, obj_in=obj_in)

    async def delete(self, *, id: int) -> None:
        # 先用带权限的 get 检查所有权
        await self.get(id=id)
        # 再调用无权限的 repo.delete
        await self._repo.delete(id=id)

    async def add_hero(self, *, collection_id: int, hero_id: int) -> None:
        # 确保 collection 属于当前用户
        await self.get(id=collection_id)
        # 调用原始 repo 的特殊方法
        await self._repo.add_hero(collection_id=collection_id, hero_id=hero_id)


class CollectionService:
    def __init__(self, repository: CollectionRepository):
        self.repository = repository  # 注入的是无作用域的、纯粹的仓库

    def _get_scoped_repo(self, current_user: User) -> _OwnerScopedRepo:
        """一个内部辅助方法，用于获取一个临时的、带用户作用域的仓库代理。"""
        return _OwnerScopedRepo(self.repository, current_user)

    async def create_collection(
        self, *, obj_in: CollectionCreate, current_user: User
    ) -> DetailResponse[CollectionResponse]:
        scoped_repo = self._get_scoped_repo(current_user)
        new_collection_orm = await scoped_repo.create(obj_in=obj_in)
        collection_dto = CollectionResponse.model_validate(new_collection_orm)
        return DetailResponse(data=collection_dto)

    async def get_collection(
        self, *, collection_id: int, current_user: User
    ) -> DetailResponse[CollectionResponseDetail]:
        scoped_repo = self._get_scoped_repo(current_user)
        collection_orm = await scoped_repo.get(id=collection_id)
        collection_dto = CollectionResponseDetail.model_validate(collection_orm)
        return DetailResponse(data=collection_dto)

    async def get_collections(
        self,
        *,
        limit: int | None,
        offset: int | None,
        current_user: User,
        search: str | None = None,
        order_by: list[str] | None = None,
    ) -> ListResponse[CollectionResponse]:
        scoped_repo = self._get_scoped_repo(current_user)
        total, collections_orm = await scoped_repo.get_list(
            limit=limit, offset=offset, search=search, order_by=order_by
        )
        items_dto = [CollectionResponse.model_validate(c) for c in collections_orm]
        # ... (组装 ListResponse 的逻辑保持不变) ...
        pagination_info = None
        if limit is not None and offset is not None:
            size = limit
            page = offset // size + 1
            pages = math.ceil(total / size) if size > 0 else 0
            pagination_info = PaginationInfo(
                total=total, page=page, size=size, pages=pages
            )
        return ListResponse(data=items_dto, meta=Meta(pagination=pagination_info))

    async def update_collection(
        self, *, collection_id: int, obj_in: CollectionUpdate, current_user: User
    ) -> DetailResponse[CollectionResponse]:
        scoped_repo = self._get_scoped_repo(current_user)
        updated_collection_orm = await scoped_repo.update(
            id=collection_id, obj_in=obj_in
        )
        collection_dto = CollectionResponse.model_validate(updated_collection_orm)
        return DetailResponse(data=collection_dto)

    async def delete_collection(
        self, *, collection_id: int, current_user: User
    ) -> None:
        scoped_repo = self._get_scoped_repo(current_user)
        await scoped_repo.delete(id=collection_id)

    async def add_hero_to_collection(
        self, *, collection_id: int, hero_id: int, current_user: User
    ) -> None:
        scoped_repo = self._get_scoped_repo(current_user)
        await scoped_repo.add_hero(collection_id=collection_id, hero_id=hero_id)
