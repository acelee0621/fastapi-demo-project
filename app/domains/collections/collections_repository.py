# app/domains/collections/collections_repository.py
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.repository import RepositoryBase
from app.models.collections import Collection, CollectionHero
from app.schemas.collections import CollectionCreate, CollectionUpdate
from app.core.exceptions import AlreadyExistsException, ForbiddenException
from app.models.users import User


class CollectionRepository(
    RepositoryBase[Collection, CollectionCreate, CollectionUpdate]
):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Collection, session=session)
        self.session = session

    async def create_for_user(
        self, *, obj_in: CollectionCreate, current_user: User
    ) -> Collection:
        """
        为特定用户创建一个 Collection。
        业务逻辑：将 current_user.id 注入到创建数据中。
        """
        # 步骤 1: 将输入的 Pydantic Schema 转换为字典
        obj_in_data = obj_in.model_dump()

        # 步骤 2: 在字典中添加或覆盖业务所需的数据
        obj_in_data["user_id"] = current_user.id

        # 步骤 3: 使用更新后的字典，重新创建一个 CreateSchemaType 的实例。
        # 这是为了满足父类 create 方法的类型要求。
        final_obj_in = CollectionCreate(**obj_in_data)

        try:
            # 步骤 4: 调用父类的 create 方法，传入这个最终构造好的 Pydantic Schema 对象
            return await super().create(session=self.session, obj_in=final_obj_in)
        except IntegrityError:
            await self.session.rollback()
            # 异常信息可以从原始的 obj_in 中获取，对用户更友好
            raise AlreadyExistsException(
                f"Collection with title '{obj_in.title}' already exists for this user."
            )

    async def get_for_user(self, *, id: int, current_user: User) -> Collection:
        """
        获取单个属于特定用户的 Collection。
        业务逻辑：获取对象后，检查其所有权。
        """
        # 1. 调用基类的 get 方法获取对象
        db_obj = await super().get(id=id)

        # 2. 在子类中执行特定的业务规则检查
        if db_obj.user_id != current_user.id:
            # 抛出具体的业务异常
            raise ForbiddenException(
                "You do not have permission to access this collection."
            )

        return db_obj

    async def get_list_for_user(
        self,
        *,
        limit: int | None,
        offset: int | None,
        current_user: User,
        search: str | None = None,
        order_by: list[str] | None = None,
    ) -> tuple[int, list[Collection]]:
        """
        获取特定用户的 Collection 列表。

        业务逻辑：在调用基类方法时，将 user_id 作为一个过滤条件传入。
        返回一个包含 (总数, Collection ORM 对象列表) 的元组。
        """
        return await super().get_list(
            limit=limit,
            offset=offset,
            search=search,
            search_fields=["title", "description"],
            order_by=order_by,
            # 👇 将所有权作为过滤条件，优雅地注入到基类方法中
            user_id=current_user.id,
        )

    async def update_for_user(
        self, *, id: int, obj_in: CollectionUpdate, current_user: User
    ) -> Collection:
        """更新一个属于特定用户的 Collection。"""
        # 1. 先获取并验证所有权
        db_obj_to_update = await self.get_for_user(id=id, current_user=current_user)

        # 2. 调用基类的 update 方法
        return await super().update(db_obj=db_obj_to_update, obj_in=obj_in)

    async def delete_for_user(self, *, id: int, current_user: User) -> None:
        """删除一个属于特定用户的 Collection。"""
        # 1. 先获取并验证所有权
        await self.get_for_user(id=id, current_user=current_user)

        # 2. 调用基类的 delete 方法
        await super().delete(id=id)

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
