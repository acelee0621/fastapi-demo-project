# app/domains/heroes/heroes_repository.py
from sqlalchemy import select, func, or_, desc, asc, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsException, NotFoundException
from app.models.collections import Collection, CollectionHero
from app.schemas.collections import CollectionCreate, CollectionUpdate


class CollectionRepository:
    """Repository for handling hero database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, obj_create: CollectionCreate, *, current_user) -> Collection:
        create_dict = obj_create.model_dump()
        create_dict["user_id"] = current_user.id  # 注入 owner
        obj = Collection(**create_dict)
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except IntegrityError:
            await self.session.rollback()
            raise AlreadyExistsException(
                f"Collection with title {obj_create.title} already exists"
            )

    async def get_by_id(self, obj_id: int, *, current_user) -> Collection:
        query = (
            select(Collection).where(
                Collection.id == obj_id, Collection.user_id == current_user.id
            )
            # .options(selectinload(Collection.heroes))  #  models里定义了lazy属性就无需这条
        )
        result = await self.session.scalars(query)
        obj = result.one_or_none()
        if not obj:
            raise NotFoundException(f"Collection with id {obj_id} not found")
        return obj

    async def get_all(
        self,
        *,
        search: str | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        current_user,
    ) -> list[Collection]:
        # tuple[int, list[Collection]]
        query = select(Collection).where(Collection.user_id == current_user.id)

        # 1. 搜索
        if search:
            query = query.where(
                or_(
                    Collection.title.ilike(f"%{search}%"),
                    Collection.description.ilike(f"%{search}%"),
                )
            )

        # 2. 排序
        ordering_clauses = []

        if order_by:
            for field in order_by:
                is_desc = field.startswith("-")
                field_name = field.lstrip("-")
                if not hasattr(Collection, field_name):
                    continue  # 跳过非法字段
                column = getattr(Collection, field_name)
                ordering_clauses.append(desc(column) if is_desc else asc(column))

        # 固定追加 id ASC 以保证排序稳定
        ordering_clauses.append(asc(Collection.id))

        # 应用排序
        query = query.order_by(*ordering_clauses)

        # 3. 总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.scalar(count_query)) or 0

        # 4. 分页
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        items = list(await self.session.scalars(query))

        return items

    async def update(
        self, obj_update: CollectionUpdate, obj_id: int, *, current_user
    ) -> Collection:
        query = select(Collection).where(
            Collection.id == obj_id, Collection.user_id == current_user.id
        )
        result = await self.session.scalars(query)
        obj = result.one_or_none()
        if not obj:
            raise NotFoundException(f"Collection with id {obj_id} not found")

        update_data = obj_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("No fields to update")
        for key, value in update_data.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj_id: int, *, current_user) -> None:
        obj = await self.session.get(Collection, obj_id)
        if not obj or obj.user_id != current_user.id:
            raise NotFoundException(f"Collection with id {obj_id} not found")

        await self.session.delete(obj)
        await self.session.commit()
        
        
    async def add_hero(self, collection_id: int, hero_id: int) -> None:
        stmt = insert(CollectionHero).values(
            collection_id=collection_id,
            hero_id=hero_id,
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise AlreadyExistsException("Hero already in this collection")
