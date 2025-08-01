# app/api/v1/heroes_route.py
from loguru import logger
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repository.heroes import HeroRepository
from app.service.heroes import HeroService
from app.schemas.heroes import HeroCreate, HeroUpdate, HeroResponse


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


@router.get("", response_model=list[HeroResponse])
async def get_all_heroes(
    service: HeroService = Depends(get_hero_service),
) -> list[HeroResponse]:
    """Get all heroes."""
    try:
        all_heroes = await service.get_heroes()
        logger.info(f"Retrieved {len(all_heroes)} heroes")
        return all_heroes
    except Exception as e:
        logger.error(f"Failed to fetch all heroes: {str(e)}")
        raise


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
