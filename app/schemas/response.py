# app/schemas/response.py

from typing import Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict

# 创建一个类型变量，可以代表任何 Pydantic 模型
T = TypeVar("T")


class PaginationInfo(BaseModel):
    """分页信息"""
    total: int = Field(..., description="总项目数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页大小")
    pages: int = Field(..., ge=0, description="总页数") # pages可以是0，当total为0时
    
    model_config = ConfigDict(
        from_attributes=True
    )


class Meta(BaseModel):
    """元数据容器"""
    pagination: PaginationInfo | None = None # 让分页信息变为可选
    # 未来可扩展 sort: SortInfo | None = None 等


class DetailResponse(BaseModel, Generic[T]):
    """
    通用单体响应结构 (例如: GET /items/{id})
    """
    data: T = Field(..., description="具体的业务数据")
    model_config = ConfigDict(
        from_attributes=True
    )
    

class ListResponse(BaseModel, Generic[T]):
    """
    通用列表响应结构 (例如: GET /items)
    """
    data: list[T] = Field(..., description="当前页的数据列表")
    meta: Meta = Field(..., description="元数据")
    model_config = ConfigDict(
        from_attributes=True
    )