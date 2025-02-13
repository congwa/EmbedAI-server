from pydantic import EmailStr
from .base import CustomBaseModel

class OAuth2EmailPasswordRequestForm(CustomBaseModel):
    """OAuth2 邮箱密码请求表单"""
    email: EmailStr
    password: str

class TokenData(CustomBaseModel):
    """Token数据模型"""
    email: str | None = None 