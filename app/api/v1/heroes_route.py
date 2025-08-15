# app/api/v1/heroes_route.py
from loguru import logger
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_filter import FilterDepends

from app.core.database import get_db
from app.domains.heroes.heroes_repository import HeroRepository
from app.domains.heroes.heroes_services import HeroService
from app.schemas.heroes import (
    HeroCreate,
    HeroUpdate,
    HeroResponse,
    HeroStoryResponse,
    HeroListResponse,
    Pagination,
    Sort,
    Filters,
    OrderByRule, 
)
from app.schemas.heroes_filter import HeroFilter



router = APIRouter(prefix="/heroes", tags=["Heroes"])


def get_hero_service(session: AsyncSession = Depends(get_db)) -> HeroService:
    """Dependency for getting HeroService instance."""
    repository = HeroRepository(session)
    return HeroService(repository)


@router.post("", response_model=HeroResponse, status_code=status.HTTP_201_CREATED)
async def create_hero(
    data: HeroCreate, service: HeroService = Depends(get_hero_service)
) -> HeroResponse:
    """Create new hero."""
    try:
        created_hero = await service.create_hero(data=data)
        logger.info(f"Created hero {created_hero.id}")
        return created_hero
    except Exception as e:
        logger.error(f"Failed to create hero: {str(e)}")
        raise

# 单字段排序路由层
# @router.get("", response_model=HeroListResponse)
# async def list_heroes(
#     search: str | None = Query(None, description="按名称、别名、能力进行模糊搜索"),
#     order_by: str = Query("id", description="排序字段：name, alias, id"),
#     direction: str = Query("asc", description="排序方向", regex="^(asc|desc)$"),
#     page: int = Query(1, ge=1, description="页码"),
#     limit: int = Query(10, ge=1, le=100, description="每页数量"),
#     service: HeroService = Depends(get_hero_service),
# ) -> HeroListResponse:
#     try:
#         offset = (page - 1) * limit
#         total, heroes = await service.get_heroes(
#             search=search,
#             order_by=order_by,
#             direction=direction,
#             limit=limit,
#             offset=offset,
#         )
#         total_pages = (total + limit - 1) // limit

#         return HeroListResponse(
#             data=heroes,
#             pagination=Pagination(
#                 currentPage=page,
#                 totalPages=total_pages,
#                 totalItems=total,
#                 limit=limit,
#                 hasMore=page < total_pages,
#                 previousPage=page - 1 if page > 1 else None,
#                 nextPage=page + 1 if page < total_pages else None,
#             ),
#             sort=Sort(field=order_by, direction=direction),
#             filters=Filters(search=search),
#         )
#     except Exception as e:
#         logger.error(f"Failed to fetch heroes: {e}")
#         raise


# 手动多字段排序路由层
@router.get("", response_model=HeroListResponse)
async def list_heroes(
    search: str | None = Query(
        None,
        description="按名称、别名、能力进行模糊搜索",
        max_length=100,
    ),    
    order_by: list[str] | None = Query(
        None,
        description="排序字段，如 -name,alias,powers(-表示倒序，默认正序)",
        example=["-name", "alias"],
    ),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    service: HeroService = Depends(get_hero_service),
) -> HeroListResponse:
    try:
        offset = (page - 1) * limit
        # 1. 将原始的字符串列表 ['-name', 'alias'] 直接传给服务层
        total, heroes = await service.get_heroes(
            search=search,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )
        total_pages = (total + limit - 1) // limit

        # 2. 将字符串列表转换为结构化的 OrderByRule 列表，用于最终返回
        order_rules = [
            OrderByRule(field=field.lstrip("-"), dir="desc" if field.startswith("-") else "asc")
            for field in (order_by or [])
        ]
        # 3. 组装最终响应
        return HeroListResponse(
            data=heroes,
            pagination=Pagination(
                currentPage=page,
                totalPages=total_pages,
                totalItems=total,
                limit=limit,
                hasMore=page < total_pages,
                previousPage=page - 1 if page > 1 else None,
                nextPage=page + 1 if page < total_pages else None,
            ),
            sort=Sort(fields=order_rules),
            filters=Filters(search=search),
        )
    except Exception as e:
        logger.error(f"Failed to fetch heroes: {e}")
        raise



# 使用了 fastapi-filter 库的路由
# @router.get("", response_model=HeroListResponse)
# async def list_heroes(
#     hero_filter: HeroFilter = FilterDepends(HeroFilter),   # 核心一行
#     page: int = Query(1, ge=1, description="页码"),
#     limit: int = Query(10, ge=1, le=100, description="每页数量"),
#     service: HeroService = Depends(get_hero_service),
# ) -> HeroListResponse:
#     try:
#         offset = (page - 1) * limit
#         total, heroes = await service.get_heroes(
#             hero_filter=hero_filter,
#             limit=limit,
#             offset=offset,
#         )
#         total_pages = (total + limit - 1) // limit

#         # 为了返回给前端，把字符串列表转成 OrderByRule
#         order_rules = [
#             OrderByRule(field=f.lstrip("-"), dir="desc" if f.startswith("-") else "asc")
#             for f in (hero_filter.order_by or [])
#         ]

#         return HeroListResponse(
#             data=heroes,
#             pagination=Pagination(
#                 currentPage=page,
#                 totalPages=total_pages,
#                 totalItems=total,
#                 limit=limit,
#                 hasMore=page < total_pages,
#                 previousPage=page - 1 if page > 1 else None,
#                 nextPage=page + 1 if page < total_pages else None,
#             ),
#             sort=Sort(fields=order_rules),
#             filters=Filters(search=hero_filter.search),
#         )
#     except Exception as e:
#         logger.error(f"Failed to fetch heroes: {e}")
#         raise



@router.get("/{hero_id}", response_model=HeroResponse)
async def get_hero(
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
) -> HeroResponse:
    """Get hero by id."""
    try:
        hero = await service.get_hero(hero_id=hero_id)
        logger.info(f"Retrieved hero {hero_id}")
        return hero
    except Exception as e:
        logger.error(f"Failed to get hero {hero_id}: {str(e)}")
        raise


@router.patch("/{hero_id}", response_model=HeroResponse, status_code=status.HTTP_200_OK)
async def update_hero(
    data: HeroUpdate,
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
) -> HeroResponse:
    """Update hero."""
    try:
        updated_hero = await service.update_hero(data=data, hero_id=hero_id)
        logger.info(f"Updated hero {hero_id}")
        return updated_hero
    except Exception as e:
        logger.error(f"Failed to update hero {hero_id}: {str(e)}")
        raise


@router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hero(
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
) -> None:
    """Delete hero."""
    try:
        await service.delete_hero(hero_id=hero_id)
        logger.info(f"Deleted hero {hero_id}")
    except Exception as e:
        logger.error(f"Failed to delete hero {hero_id}: {str(e)}")
        raise


@router.get("/{hero_id}/story", response_model=HeroStoryResponse)
async def generate_hero_story(
    hero_id: int,
    service: HeroService = Depends(get_hero_service),
) -> HeroResponse:
    """Generate hero story."""
    try:
        story = await service.get_hero_with_story(hero_id=hero_id)
        logger.info(f"Generated story for hero {hero_id}")
        return story
    except Exception as e:
        logger.error(f"Failed to generate hero's story. {hero_id}: {str(e)}")
        raise
