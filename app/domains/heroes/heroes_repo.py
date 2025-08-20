# app/domains/heroes/heroes_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.repository import RepositoryBase
from app.models.heroes import Hero
from app.schemas.heroes import HeroCreate, HeroUpdate
from app.core.exceptions import AlreadyExistsException


class HeroRepository(RepositoryBase[Hero, HeroCreate, HeroUpdate]):
    """
    HeroRepository 继承自通用的 RepositoryBase，
    并提供了针对 Hero 模型的特定实现和策略。
    """

    def __init__(self, session: AsyncSession):
        """
        初始化 HeroRepository。

        Args:
            session: SQLAlchemy 的异步会话实例。
        """
        super().__init__(model=Hero, session=session)
        self.session = session

    async def create(self, *, obj_in: HeroCreate) -> Hero:
        """
        创建一个新的 Hero。

        重写此方法以提供针对 'alias' 字段的、更具体的唯一性冲突错误信息。
        """
        try:
            # 直接调用父类的 create 方法，它包含了核心的创建逻辑
            return await super().create(obj_in=obj_in)
        except IntegrityError:
            # 这里不再需要手动回滚。
            # 外层的 `async with session.begin():` 会在捕获到异常时自动处理回滚。
            # 我们在这里的唯一职责，就是将数据库异常“翻译”成我们的业务异常。            
            raise AlreadyExistsException(f"Hero with alias '{obj_in.alias}' already exists")
            # 如果不打算抛出这个精确的异常，可以使用父类的通用异常，你甚至都不需要重写这个方法。

    async def get_list(
        self,
        *,
        limit: int | None,
        offset: int | None,
        search: str | None = None,
        order_by: list[str] | None = None,    
    ) -> tuple[int, list[Hero]]:
        """
        获取 Hero 列表，并定义此仓库的特定搜索策略。

        此方法调用父类的通用列表查询，并返回一个包含 (总数, Hero ORM 对象列表) 的元组。
        """
        # 调用父类的 get_list 方法，并传入本模型允许被搜索的字段列表
        return await super().get_list(            
            limit=limit,
            offset=offset,
            search=search,
            # 👇 这就是注入 Hero 模型的搜索策略，每个模型搜索策略不同，这个方法必须重写以便定制
            search_fields=["name", "alias", "powers"], # 策略定义
            order_by=order_by,
        )

    # get, update, delete 方法被直接继承，无需在此定义。
    # - get: 基类已处理 "Not Found" 异常。
    # - update: 基类已处理 schema 到 dict 的转换。
    # - delete: 基类已处理 "Not Found" 异常。