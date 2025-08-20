# app/domains/collections/collections_service.py
import math

# 导入所有需要的模型和 Schema
from app.domains.collections.collections_repository import CollectionRepository
from app.schemas.collections import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    CollectionResponseDetail,
)

# 导入我们标准化的响应模型
from app.schemas.response import DetailResponse, ListResponse, Meta, PaginationInfo
from app.models.users import User


class CollectionService:
    def __init__(self, repository: CollectionRepository):
        """服务层，负责处理 Collection 相关的业务逻辑。"""
        self.repository = repository

    async def create_collection(
        self, *, obj_in: CollectionCreate, current_user: User
    ) -> DetailResponse[CollectionResponse]:
        """
        为当前用户创建一个新的 Collection。
        """
        # 调用仓库层中为用户创建的特定方法
        new_collection_orm = await self.repository.create_for_user(
            obj_in=obj_in, current_user=current_user
        )

        # 将 ORM 对象转换为 Pydantic Schema
        collection_dto = CollectionResponse.model_validate(new_collection_orm)

        # 使用标准响应模型包装返回
        return DetailResponse(data=collection_dto)

    async def get_collection(
        self, *, collection_id: int, current_user: User
    ) -> DetailResponse[CollectionResponseDetail]:
        """
        获取单个属于当前用户的 Collection 详情。
        """
        # 调用仓库层中为用户获取的特定方法，它已经包含了所有权检查
        collection_orm = await self.repository.get_for_user(
            id=collection_id, current_user=current_user
        )

        # 转换为包含英雄列表的详细 DTO
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
        """
        获取当前用户的 Collection 列表。
        """
        # 1. 从仓库层获取原始数据元组 (总数, ORM对象列表)
        total, collections_orm = await self.repository.get_list_for_user(
            limit=limit,
            offset=offset,
            current_user=current_user,
            search=search,
            order_by=order_by,
        )

        # 2. 将列表中的 ORM 对象 (Collection) 转换为 Pydantic Schema (CollectionResponse)
        items_dto = [CollectionResponse.model_validate(c) for c in collections_orm]

        # 3. 在服务层组装最终的 ListResponse 对象
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
        """
        更新一个属于当前用户的 Collection。
        """
        # 调用仓库层中为用户更新的特定方法
        updated_collection_orm = await self.repository.update_for_user(
            id=collection_id, obj_in=obj_in, current_user=current_user
        )

        collection_dto = CollectionResponse.model_validate(updated_collection_orm)

        return DetailResponse(data=collection_dto)

    async def delete_collection(
        self, *, collection_id: int, current_user: User
    ) -> None:
        """
        删除一个属于当前用户的 Collection。
        """
        # 调用仓库层中为用户删除的特定方法
        await self.repository.delete_for_user(
            id=collection_id, current_user=current_user
        )

    async def add_hero_to_collection(
        self, *, collection_id: int, hero_id: int, current_user: User
    ) -> None:
        """
        向一个 Collection 中添加一个 Hero。
        这是特定于 Collection 的业务逻辑。
        """
        # 步骤 1: 验证 Collection 的存在性和所有权
        # 我们复用 get_for_user 方法，因为它已经完美地处理了这两种检查。
        await self.repository.get_for_user(id=collection_id, current_user=current_user)

        # 步骤 2: 调用仓库层中添加英雄的自定义方法
        await self.repository.add_hero(collection_id=collection_id, hero_id=hero_id)
