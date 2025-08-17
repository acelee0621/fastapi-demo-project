# app/schemas/auth.py
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
    
class LoginData(BaseModel):
    username: str
    password: str