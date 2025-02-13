from pydantic import EmailStr
from .base import CustomBaseModel

class AdminRegister(CustomBaseModel):
    """管理员注册请求模型"""
    email: EmailStr
    password: str
    register_code: str  # 管理员注册码，用于验证是否有权限注册管理员账户