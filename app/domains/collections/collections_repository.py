# app/domains/collections/collections_repository.py
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import RepositoryBase
from app.models.collections import Collection, CollectionHero
from app.schemas.collections import CollectionCreate, CollectionUpdate
from app.core.exceptions import AlreadyExistsException


class CollectionRepository(
    RepositoryBase[Collection, CollectionCreate, CollectionUpdate]
):
    """
    一个纯粹的、无状态的仓库，只负责 Collection 模型的数据操作。
    所有权逻辑将由服务层的代理来处理。
    """

    def __init__(self, session: AsyncSession):
        """
        初始化 CollectionRepository。
        """
        super().__init__(model=Collection, session=session)

    # get, create, update, delete, get_list 都会被直接继承
    # 我们只需要在这里定义 Collection 真正特殊的方法
    async def add_hero(self, *, collection_id: int, hero_id: int) -> None:
        """向 Collection 添加 Hero (多对多关系)。"""
        stmt = insert(CollectionHero).values(
            collection_id=collection_id, hero_id=hero_id
        )
        try:
            await self.session.execute(stmt)
            # 注意：按照我们的 Unit of Work 模式，这里不应该 commit
            # 让上层的事务管理器来处理
            await self.session.flush()
        except IntegrityError:
            # 同样，rollback 也由上层处理
            raise AlreadyExistsException("Hero already in this collection")

    # 我们仍然可以重写 get_list 来提供搜索策略，但不再需要 user_id
    async def get_list(
        self,
        *,
        limit: int | None,
        offset: int | None,
        search: str | None = None,
        order_by: list[str] | None = None,
        **filters,
    ) -> tuple[int, list[Collection]]:
        """获取 Collection 列表，并定义搜索策略。"""
        return await super().get_list(
            limit=limit,
            offset=offset,
            search=search,
            search_fields=["title", "description"],
            order_by=order_by,
            **filters,
        )
