# app/domains/collections/collections_service.py
from app.domains.collections.collections_repository import CollectionRepository
from app.schemas.collections import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    CollectionResponseDetail,
)


class CollectionService:
    def __init__(self, repository: CollectionRepository):
        """Service layer for note operations."""

        self.repository = repository

    async def create_collection(
        self, data: CollectionCreate, *, current_user
    ) -> CollectionResponse:
        new_collection = await self.repository.create(data, current_user=current_user)
        return CollectionResponse.model_validate(new_collection)

    async def get_collection(
        self, collection_id: int, *, current_user
    ) -> CollectionResponseDetail:
        collection = await self.repository.get_by_id(
            collection_id, current_user=current_user
        )
        return CollectionResponseDetail.model_validate(collection)

    async def get_collections(
        self,
        *,
        search: str | None,
        order_by: list[str] | None,
        limit: int | None,
        offset: int | None,
        current_user,
    ) -> list[CollectionResponse]:
        collections = await self.repository.get_all(
            search=search,
            order_by=order_by,
            limit=limit,
            offset=offset,
            current_user=current_user,
        )
        return [
            CollectionResponse.model_validate(collection) for collection in collections
        ]

    async def update_collection(
        self, data: CollectionUpdate, collection_id: int, *, current_user
    ) -> CollectionResponse:
        updated_collection = await self.repository.update(
            data, collection_id, current_user=current_user
        )
        return CollectionResponse.model_validate(updated_collection)

    async def delete_collection(self, collection_id: int, *, current_user) -> None:
        await self.repository.delete(collection_id, current_user=current_user)
        
    async def add_hero_to_collection(
        self, collection_id: int, hero_id: int, *, current_user
    ) -> None:
        # 1. 验证collection是否存在及属于当前用户
        await self.repository.get_by_id(collection_id, current_user=current_user)
        # 2. 添加收藏
        await self.repository.add_hero(collection_id, hero_id)
