from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsException, NotFoundException
from app.models.heroes import Hero
from app.schemas.heroes import HeroCreate, HeroUpdate


class HeroRepository:
    """Repository for handling hero database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, hero_data: HeroCreate) -> Hero:
        """Create a new hero."""
        hero = Hero(**hero_data.model_dump())
        try:
            self.session.add(hero)
            await self.session.commit()
            await self.session.refresh(hero)
            return hero
        except IntegrityError:
            await self.session.rollback()
            raise AlreadyExistsException(
                f"Hero with alias {hero_data.alias} already exists"
            )

    async def get_by_id(self, hero_id: int) -> Hero:
        """Fetch a hero by id."""
        hero = await self.session.get(Hero, hero_id)
        if not hero:
            raise NotFoundException(f"Hero with id {hero_id} not found")
        return hero

    async def get_all(self) -> list[Hero]:
        """Fetch all heroes."""
        query = select(Hero)
        result = await self.session.scalars(query)
        return list(result.all())

    async def update(self, hero_data: HeroUpdate, hero_id: int) -> Hero:
        """Update an existing hero."""
        hero = await self.session.get(Hero, hero_id)
        if not hero:
            raise NotFoundException(f"Hero with id {hero_id} not found")

        update_data = hero_data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            raise ValueError("No fields to update")
        for key, value in update_data.items():
            setattr(hero, key, value)
        await self.session.commit()
        await self.session.refresh(hero)
        return hero
        

    async def delete(self, hero_id: int) -> None:
        """Delete a hero."""
        hero = await self.session.get(Hero, hero_id)
        if not hero:
            raise NotFoundException(f"Hero with id {hero_id} not found")

        await self.session.delete(hero)
        await self.session.commit()
