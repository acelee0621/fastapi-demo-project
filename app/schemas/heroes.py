# app/schemas/heroes.py
from pydantic import BaseModel


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
