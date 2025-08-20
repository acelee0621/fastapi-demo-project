# app/repository/base.py
from typing import Generic, TypeVar, Type, Any
from pydantic import BaseModel

from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.core.exceptions import NotFoundException, AlreadyExistsException

# 为 SQLAlchemy 模型、Pydantic 创建/更新 Schema 定义类型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


# 👇 将 CreateSchemaType 和 UpdateSchemaType 添加到泛型签名中
class RepositoryBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, *, id: Any) -> ModelType:
        """
        根据 ID 高效获取单个记录。
        如果未找到，则直接抛出 NotFoundException 异常。
        """
        db_obj = await self.session.get(self.model, id)
        if not db_obj:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")        
        return db_obj

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        从 Pydantic Schema 创建一个新对象，并处理唯一性约束异常。
        """
        # 👇 逻辑内聚：将 .model_dump() 封装在基类内部
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        self.session.add(db_obj)
        try:            
            await self.session.flush()
            await self.session.refresh(db_obj)
            return db_obj
        except IntegrityError:            
            raise AlreadyExistsException(
                f"{self.model.__name__} with conflicting data already exists."
            )

    async def update(
        self, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        从 Pydantic Schema 更新一个已存在的对象。
        """
        # 👇 逻辑内聚：将 .model_dump(exclude_unset=True) 封装在基类内部
        update_data = obj_in.model_dump(exclude_unset=True)
        
        if not update_data:
            return db_obj  # 没有字段需要更新，直接返回原对象
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: Any) -> ModelType:
        """删除一个对象"""
        # 👇 优化：get 方法已经处理了 Not Found，所以这里的检查是多余的
        obj = await self.get(id=id)
        await self.session.delete(obj)
        await self.session.flush()
        return obj

    async def get_list(
        self,
        *,
        limit: int | None,
        offset: int | None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        order_by: list[str] | None = None,
        **filters,
    ) -> tuple[int, list[ModelType]]:
        """
        获取记录列表，返回 (总数, 项目列表) 的元组。
        支持可选的分页、搜索、排序和任意数量的精确过滤。
        """
        
        query = select(self.model)

        # 1. 应用任意数量的精确过滤条件 (例如: user_id=1, is_active=True)
        if filters:
            query = query.filter_by(**filters)

        # 2. 应用模糊搜索条件
        if search and search_fields:
            search_clauses = [
                getattr(self.model, field).ilike(f"%{search}%")
                for field in search_fields if hasattr(self.model, field)
            ]
            if search_clauses:
                query = query.where(or_(*search_clauses))

        # 3. 应用排序
        if order_by:
            ordering_clauses = []
            for field in order_by:
                is_desc = field.startswith("-")
                field_name = field.lstrip("-")
                if hasattr(self.model, field_name):
                    column = getattr(self.model, field_name)
                    ordering_clauses.append(desc(column) if is_desc else asc(column))
            if ordering_clauses:
                query = query.order_by(*ordering_clauses)
        
        # 4. 获取总数 (必须在分页之前)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.scalar(count_query)) or 0

        # 5. 应用分页
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        # 6. 执行查询
        result = await self.session.scalars(query)
        items = list(result.all())
        
        return total, items