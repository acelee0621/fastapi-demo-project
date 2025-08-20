# app/api/v1/heroes_route.py

from fastapi import APIRouter, Depends, status, Query
from loguru import logger

# 导入我们标准化的响应模型和所有需要的 Schema
from app.schemas.response import DetailResponse, ListResponse
from app.schemas.heroes import HeroCreate, HeroUpdate, HeroResponse, HeroStoryResponse

# 导入服务层和依赖项
from app.domains.heroes.heroes_serv import HeroService
from app.core.dependencies import get_hero_service


router = APIRouter(
    prefix="/new_heroes",
    tags=["New Heroes"],
    # 这是一个公开路由，所以我们不在 router 级别添加 `get_current_user` 依赖
)


@router.post(
    "",
    response_model=DetailResponse[HeroResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建一个新的英雄"
)
async def create_hero(
    data: HeroCreate,
    service: HeroService = Depends(get_hero_service),
):
    """
    创建一条新的英雄记录。
    - **name**: 英雄的真实姓名
    - **alias**: 英雄的别名/代号 (必须唯一)
    """
    created_hero = await service.create_hero(obj_in=data)
    logger.info(f"Created hero {created_hero.data.id}")
    return created_hero


@router.get(
    "",
    response_model=ListResponse[HeroResponse],
    summary="获取英雄列表"
)
async def list_heroes(
    search: str | None = Query(None, description="按姓名、别名、能力进行模糊搜索", max_length=100),
    order_by: list[str] | None = Query(None, description="排序字段，如 -name,alias (-表示倒序)", example=["-name"]),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    service: HeroService = Depends(get_hero_service),
):
    """
    获取英雄列表，支持分页、排序和搜索。
    """
    offset = (page - 1) * size
    
    heroes_list = await service.get_heroes(
        limit=size,
        offset=offset,
        search=search,
        order_by=order_by,
    )
    return heroes_list


@router.get(
    "/{hero_id}",
    response_model=DetailResponse[HeroResponse],
    summary="获取英雄详情"
)
async def get_hero(
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
):
    """
    根据 ID 获取单个英雄的详细信息。
    """
    hero_detail = await service.get_hero(hero_id=hero_id)
    return hero_detail


@router.patch(
    "/{hero_id}",
    response_model=DetailResponse[HeroResponse],
    summary="更新英雄信息"
)
async def update_hero(
    hero_id: int,
    data: HeroUpdate,
    service: HeroService = Depends(get_hero_service),
):
    """
    局部更新一个英雄的信息。
    """
    updated_hero = await service.update_hero(hero_id=hero_id, obj_in=data)
    logger.info(f"Updated hero {hero_id}")
    return updated_hero


@router.delete(
    "/{hero_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除一个英雄"
)
async def delete_hero(
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
):
    """
    根据 ID 删除一个英雄。
    """
    await service.delete_hero(hero_id=hero_id)
    logger.info(f"Deleted hero {hero_id}")
    # 204 状态码不返回任何响应体


@router.get(
    "/{hero_id}/story",
    response_model=HeroStoryResponse, # 👈 注意：这里直接使用业务特定的响应模型
    summary="获取英雄的背景故事"
)
async def get_hero_story(
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
):
    """
    一个特殊的业务端点，返回英雄信息和一段动态生成的背景故事。
    这个端点展示了为什么服务层处理业务逻辑很重要。
    """
    # 它的返回结构不符合通用的 DetailResponse，所以我们直接返回服务层构建的特殊模型
    hero_story = await service.get_hero_with_story(hero_id=hero_id)
    return hero_story