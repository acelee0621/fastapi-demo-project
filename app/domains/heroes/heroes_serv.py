# app/domains/heroes/heroes_services.py

import math
from redis.asyncio import Redis

# 导入我们的标准化响应模型
from app.schemas.response import DetailResponse, ListResponse, Meta, PaginationInfo
from app.schemas.heroes import HeroCreate, HeroUpdate, HeroResponse, HeroStoryResponse
from app.domains.heroes.heroes_repo import HeroRepository

CACHE_TTL = 60 * 15  # 15分钟缓存


class HeroService:
    """服务层，负责处理英雄相关的业务逻辑。"""

    def __init__(self, repository: HeroRepository, redis: Redis):
        """
        初始化服务层。

        Args:
            repository: HeroRepository 的实例。
            redis: Redis 客户端的异步实例。
        """
        self.repository = repository
        self.redis = redis

    async def create_hero(self, *, obj_in: HeroCreate) -> DetailResponse[HeroResponse]:
        """
        创建一个新的 Hero。

        Args:
            obj_in: 创建 Hero 所需的数据。

        Returns:
            包含新创建 Hero 数据的标准响应体。
        """
        # 调用仓库层的 create 方法，它现在是类型安全的
        new_hero_orm = await self.repository.create(obj_in=obj_in)
        
        # 将 ORM 对象转换为 Pydantic Schema
        hero_dto = HeroResponse.model_validate(new_hero_orm)
        
        # 使用标准响应模型包装返回
        return DetailResponse(data=hero_dto)

    async def get_hero(self, *, hero_id: int) -> DetailResponse[HeroResponse]:
        """
        获取单个 Hero，优先从缓存中读取。

        Args:
            hero_id: Hero 的 ID。

        Returns:
            包含 Hero 数据的标准响应体。
        """
        key = f"hero:{hero_id}"
        cached = await self.redis.get(key)
        
        if cached:
            # 命中缓存，直接验证并包装返回
            hero_dto = HeroResponse.model_validate_json(cached)
            return DetailResponse(data=hero_dto)

        # 缓存未命中，从数据库查询
        hero_orm = await self.repository.get(id=hero_id)
        hero_dto = HeroResponse.model_validate(hero_orm)

        # 写回缓存
        await self.redis.set(key, hero_dto.model_dump_json(), ex=CACHE_TTL)
        
        return DetailResponse(data=hero_dto)

    async def get_heroes(
        self,
        *,
        limit: int | None,
        offset: int | None,
        search: str | None = None,
        order_by: list[str] | None = None,
    ) -> ListResponse[HeroResponse]:
        """
        获取 Hero 列表。
        
        此方法接收 limit 和 offset，并负责将仓库层返回的原始数据
        组装成标准的 ListResponse 响应体。
        """
        # 1. 从仓库层获取原始数据元组 (总数, ORM对象列表)
        total, heroes_orm = await self.repository.get_list(
            limit=limit,
            offset=offset,
            search=search,
            order_by=order_by,
        )
        
        # 2. 将列表中的 ORM 对象 (Hero) 转换为 Pydantic Schema (HeroResponse)
        items_dto = [HeroResponse.model_validate(h) for h in heroes_orm]
        
        # 3. 在服务层组装最终的 ListResponse 对象
        pagination_info = None
        if limit is not None and offset is not None:
            size = limit
            # 👇 从 limit 和 offset 反向计算出 page，用于在响应中返回
            page = offset // size + 1
            pages = math.ceil(total / size) if size > 0 else 0
            pagination_info = PaginationInfo(
                total=total, page=page, size=size, pages=pages
            )
            
        return ListResponse(
            data=items_dto,
            meta=Meta(pagination=pagination_info)
        )

    async def update_hero(self, *, hero_id: int, obj_in: HeroUpdate) -> DetailResponse[HeroResponse]:
        """
        更新一个 Hero，并清除相关缓存。

        Args:
            hero_id: 要更新的 Hero 的 ID。
            obj_in: 更新所需的数据。
        """
        # 步骤 1: 先通过 id 获取要更新的数据库对象。
        # 仓库的 get 方法已经内置了 "Not Found" 异常处理。
        db_obj_to_update = await self.repository.get(id=hero_id)

        # (这里是执行额外业务逻辑的最佳位置, 例如权限检查)
        # if db_obj_to_update.owner_id != current_user.id:
        #     raise PermissionDeniedException(...)

        # 步骤 2: 将获取到的对象和更新数据传递给 update 方法。
        updated_hero_orm = await self.repository.update(
            db_obj=db_obj_to_update, 
            obj_in=obj_in
        )
        
        # 将更新后的 ORM 对象转换为 Pydantic Schema
        hero_dto = HeroResponse.model_validate(updated_hero_orm)
        
        # 关键：执行写操作后，必须让缓存失效！
        key = f"hero:{hero_id}"
        await self.redis.delete(key)

        # 使用标准响应模型包装返回
        return DetailResponse(data=hero_dto)

    async def delete_hero(self, *, hero_id: int) -> None:
        """
        删除一个 Hero，并清除相关缓存。
        """
        # 调用仓库层的 delete 方法
        await self.repository.delete(id=hero_id)

        # ----------------------------------------------------
        # 关键：执行写操作后，必须让缓存失效！
        key = f"hero:{hero_id}"
        await self.redis.delete(key)
        # ----------------------------------------------------

    async def get_hero_with_story(self, hero_id: int) -> HeroStoryResponse:
        """
        获取英雄信息，并动态生成一段背景故事。
        这个方法完美展示了服务层的业务逻辑处理能力。
        """
        # 1. 调用仓库层，获取最原始的数据库数据
        hero_orm = await self.get_hero(hero_id=hero_id)
        # 2. 在服务层中应用“业务逻辑”
        # 这里的逻辑是：根据英雄的名字和别名，虚构一段故事
        story_template = (
            f"在繁华的都市背后，流传着一个传说……那就是“{hero_orm.data.alias}”！"
            f"很少有人知道，这位在暗夜中守护光明的英雄，其真实身份是 {hero_orm.data.name}。"
            f"每一个被TA拯救的人，都会在心中默默记下这个名字。"
        )
        # 3. 构造并返回一个新的、带有附加信息的数据模型
        return HeroStoryResponse(
            id=hero_orm.data.id,
            name=hero_orm.data.name,
            alias=hero_orm.data.alias,
            powers=hero_orm.data.powers,
            story=story_template,
        )
