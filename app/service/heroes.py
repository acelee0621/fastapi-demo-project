from app.repository.heroes import HeroRepository
from app.schemas.heroes import HeroCreate, HeroUpdate, HeroResponse


class HeroService:
    def __init__(self, repository: HeroRepository):
        """Service layer for hero operations."""

        self.repository = repository

    async def create_hero(self, data: HeroCreate) -> HeroResponse:
        new_hero = await self.repository.create(data)
        return HeroResponse.model_validate(new_hero)

    async def get_hero(self, hero_id: int) -> HeroResponse:
        hero = await self.repository.get_by_id(hero_id)
        return HeroResponse.model_validate(hero)

    async def get_heroes(
        self,
    ) -> list[HeroResponse]:
        heroes = await self.repository.get_all()
        for hero in heroes:
            print(f"hero {hero.id} alias: {hero.alias}")
        return [HeroResponse.model_validate(hero) for hero in heroes]

    async def update_hero(self, data: HeroUpdate, hero_id: int) -> HeroResponse:
        hero = await self.repository.update(data, hero_id)
        return HeroResponse.model_validate(hero)

    async def delete_hero(self, hero_id: int) -> None:
        await self.repository.delete(hero_id)