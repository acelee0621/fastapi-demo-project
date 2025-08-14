# app/schemas/heroes.py
from pydantic import BaseModel
from typing import Literal

class OrderByRule(BaseModel):
    field: str
    dir: Literal["asc", "desc"] = "asc"    
    

# 基础模型，包含所有用户共有的字段
class HeroBase(BaseModel):
    name: str
    alias: str
    powers: str | None = None


# 创建用户时，从请求体中读取的模型
# 需要提供密码
class HeroCreate(HeroBase):
    pass


class HeroUpdate(BaseModel):
    name: str | None = None
    alias: str | None = None
    powers: str | None = None


# 从数据库读取并返回给客户端的模型
class HeroResponse(HeroBase):
    id: int

    # Pydantic V2 的新配置方式
    class Config:
        from_attributes = True  # 告诉 Pydantic 模型可以从 ORM 对象属性中读取数据
        
        
# 新增一个用于返回带故事的英雄信息的模型
class HeroStoryResponse(HeroResponse):
    story: str


# 新增用于「分页、排序、过滤/搜索」三合一查询的模型
# 目前只有 Hero 在用这些模型，暂时写在这同一个文件里
# 后续可以将分页、排序、过滤/搜索的逻辑抽离出来

# 1.分页
class Pagination(BaseModel):
    currentPage: int
    totalPages: int
    totalItems: int
    limit: int
    hasMore: bool
    previousPage: int | None
    nextPage: int | None

# 2.排序
# class Sort(BaseModel):
#     field: str
#     direction: str   # asc | desc


class Sort(BaseModel):
    fields: list[OrderByRule]
    
    
    


# 3.过滤/搜索
class Filters(BaseModel):
    search: str | None

# 4.包装返回结构
class HeroListResponse(BaseModel):
    data: list[HeroResponse]
    pagination: Pagination
    sort: Sort
    filters: Filters