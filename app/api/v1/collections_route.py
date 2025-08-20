# app/api/v1/heroes_route.py
from fastapi import APIRouter, Depends, status, Query
from loguru import logger

# 导入我们标准化的响应模型
from app.schemas.response import DetailResponse, ListResponse
from app.schemas.collections import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionResponseDetail,
    HeroAttachRequest,
)

# 导入服务层和依赖项
from app.core.dependencies import get_collection_service
from app.domains.collections.collections_service import CollectionService
from app.models.users import User
from app.domains.users.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
    # 👇 在这里统一应用依赖，所有此路由下的端点都将自动受其保护
    dependencies=[Depends(get_current_user)],
)



@router.post(
    "",
    response_model=DetailResponse[CollectionResponse],  # 👈 使用标准化后的 response_model
    status_code=status.HTTP_201_CREATED,
    summary="创建一个新的收藏集",
)
async def create_collection(
    data: CollectionCreate,
    service: CollectionService = Depends(get_collection_service),
    current_user: User = Depends(get_current_user),  # 在需要时单独获取
):
    # 👇 移除 try...except，让全局异常处理器接管
    # 👇 更新服务层调用，使用关键字参数 obj_in
    created_collection = await service.create_collection(
        obj_in=data, current_user=current_user
    )
    logger.info(
        f"User {current_user.id} created collection {created_collection.data.id}"
    )
    return created_collection


@router.get(
    "",
    response_model=ListResponse[CollectionResponse],  # 👈 使用标准化后的 response_model
    summary="获取当前用户的收藏集列表",
)
async def list_collections(
    search: str | None = Query(
        None, description="按名称、描述进行模糊搜索", max_length=100
    ),
    order_by: list[str] | None = Query(
        None, description="排序字段，如 -title", example=["-title"]
    ),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    service: CollectionService = Depends(get_collection_service),
    current_user: User = Depends(get_current_user),
):
    # page/size 到 offset 的转换在路由层完成，非常正确！
    offset = (page - 1) * size

    collections = await service.get_collections(
        limit=size,  # 👈 注意这里是 size
        offset=offset,
        search=search,
        order_by=order_by,
        current_user=current_user,
    )
    return collections


@router.get(
    "/{collection_id}",
    response_model=DetailResponse[CollectionResponseDetail],  # 👈 修正 response_model
    summary="获取收藏集详情",
)
async def get_collection(
    collection_id: int,
    service: CollectionService = Depends(get_collection_service),
    current_user: User = Depends(get_current_user),
):
    collection = await service.get_collection(
        collection_id=collection_id, current_user=current_user
    )
    return collection


@router.patch(
    "/{collection_id}",
    response_model=DetailResponse[CollectionResponse],  # 👈 修正 response_model
    summary="更新收藏集",
)
async def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    service: CollectionService = Depends(get_collection_service),
    current_user: User = Depends(get_current_user),
):
    updated_collection = await service.update_collection(
        collection_id=collection_id, obj_in=data, current_user=current_user
    )
    logger.info(f"User {current_user.id} updated collection {collection_id}")
    return updated_collection


@router.delete(
    "/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除收藏集"
)
async def delete_collection(
    collection_id: int,
    service: CollectionService = Depends(get_collection_service),
    current_user: User = Depends(get_current_user),
):
    await service.delete_collection(
        collection_id=collection_id, current_user=current_user
    )
    logger.info(f"User {current_user.id} deleted collection {collection_id}")


@router.post(
    "/{collection_id}/heroes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="把 hero 加入收藏集",
)
async def add_hero_to_collection(
    collection_id: int,
    payload: HeroAttachRequest,
    service: CollectionService = Depends(get_collection_service),
    current_user: User = Depends(get_current_user),
):
    # 👇 更新服务层调用，使用关键字参数
    await service.add_hero_to_collection(
        collection_id=collection_id, hero_id=payload.hero_id, current_user=current_user
    )
