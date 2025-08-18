# app/schemas/collections.py
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.heroes import HeroResponse


class CollectionBase(BaseModel):
    title: str
    description: str | None = None


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


# 从数据库读取并返回给客户端的模型
class CollectionResponse(CollectionBase):
    id: int
    

    model_config = ConfigDict(from_attributes=True)
    
    
class CollectionResponseDetail(CollectionBase):
    id: int
    heroes: list["HeroResponse"] | None

    model_config = ConfigDict(from_attributes=True)
    
    
class HeroAttachRequest(BaseModel):
    hero_id: int = Field(..., gt=0, description="要加入收藏的英雄 id")
