# app/api/v1/heroes_route.py
from loguru import logger
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.collections.collections_repository import CollectionRepository
from app.domains.collections.collections_service import CollectionService
from app.schemas.collections import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionResponseDetail,
    HeroAttachRequest
)

from app.domains.users.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
    dependencies=[Depends(get_current_user)],
)


def get_collection_service(
    session: AsyncSession = Depends(get_db),
) -> CollectionService:
    repository = CollectionRepository(session)
    return CollectionService(repository)


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    service: CollectionService = Depends(get_collection_service),
    current_user=Depends(get_current_user),
) -> CollectionResponse:
    try:
        created_collection = await service.create_collection(
            data=data, current_user=current_user
        )
        logger.info(f"Created collection {created_collection.id}")
        return created_collection
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        raise


@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    search: str | None = Query(
        None,
        description="按名称、描述进行模糊搜索",
        max_length=100,
    ),
    order_by: list[str] | None = Query(
        None,
        description="排序字段，如 -title,description (-表示倒序，默认正序)",
        example=["-title", "description"],
    ),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    service: CollectionService = Depends(get_collection_service),
    current_user=Depends(get_current_user),
) -> list[CollectionResponse]:
    try:
        offset = (page - 1) * limit

        collections = await service.get_collections(
            search=search,
            order_by=order_by,
            limit=limit,
            offset=offset,
            current_user=current_user,
        )

        return collections
    except Exception as e:
        logger.error(f"Failed to fetch collections: {e}")
        raise


@router.get("/{collection_id}", response_model=CollectionResponseDetail)
async def get_collection(
    collection_id: int,
    service: CollectionService = Depends(get_collection_service),
    current_user=Depends(get_current_user),
) -> CollectionResponseDetail:
    try:
        collection = await service.get_collection(
            collection_id=collection_id, current_user=current_user
        )
        logger.info(f"Retrieved collection {collection_id}")
        return collection
    except Exception as e:
        logger.error(f"Failed to get collection {collection_id}: {str(e)}")
        raise


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_collection(
    data: CollectionUpdate,
    collection_id: int,
    service: CollectionService = Depends(get_collection_service),
    current_user=Depends(get_current_user),
) -> CollectionResponse:
    try:
        updated_collection = await service.update_collection(
            data=data, collection_id=collection_id, current_user=current_user
        )
        logger.info(f"Updated collection {collection_id}")
        return updated_collection
    except Exception as e:
        logger.error(f"Failed to update collection {collection_id}: {str(e)}")
        raise


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hero(
    collection_id: int,
    service: CollectionService = Depends(get_collection_service),
    current_user=Depends(get_current_user),
) -> None:
    """Delete hero."""
    try:
        await service.delete_collection(
            collection_id=collection_id, current_user=current_user
        )
        logger.info(f"Deleted collection {collection_id}")
    except Exception as e:
        logger.error(f"Failed to delete collection {collection_id}: {str(e)}")
        raise


@router.post(
    "/{collection_id}/heroes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="把 hero 加入收藏",
)
async def add_hero_to_collection(
    collection_id: int,
    payload: HeroAttachRequest,
    service: CollectionService = Depends(get_collection_service),
    current_user=Depends(get_current_user),
) -> None:
    await service.add_hero_to_collection(
        collection_id, payload.hero_id, current_user=current_user
    )
