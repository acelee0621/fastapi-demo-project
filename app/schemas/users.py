# app/schemas/user.py
from pydantic import BaseModel

# 基础模型，包含所有用户共有的字段
class UserBase(BaseModel):
    username: str

# 创建用户时，从请求体中读取的模型
# 需要提供密码
class UserCreate(UserBase):
    password: str

# 从数据库读取并返回给客户端的模型
# 不应该包含密码，但应该包含 id
class UserResponse(UserBase):
    id: int
    # Pydantic V2 的新配置方式
    class Config:
        from_attributes = True  # 告诉 Pydantic 模型可以从 ORM 对象属性中读取数据