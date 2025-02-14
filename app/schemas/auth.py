from pydantic import EmailStr
from .base import CustomBaseModel

class OAuth2EmailPasswordRequestForm(CustomBaseModel):
    """管理员登录请求模型"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@example.com",
                "password": "admin123"
            }
        }

class TokenData(CustomBaseModel):
    """Token数据模型"""
    email: str | None = None 