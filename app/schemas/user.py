from typing import Optional
from datetime import datetime
from pydantic import EmailStr, Field
from .base import CustomBaseModel

class UserBase(CustomBaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

class UserResponse(UserBase):
    id: int
    email: str
    is_admin: bool
    is_active: bool
    sdk_key: Optional[str]
    secret_key: Optional[str]
    created_at: datetime

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_admin: bool
    is_active: bool

class UserInfo(CustomBaseModel):
    id: int
    email: str
    is_admin: bool
    created_at: datetime

# Pydantic模型(UserListItem)只返回安全的字段：
class UserListItem(CustomBaseModel):
    id: int
    email: str

class Token(CustomBaseModel):
    """Token响应模型"""
    access_token: str
    user: UserInfo

class AdminChangeUserPasswordRequest(CustomBaseModel):
    """管理员修改用户密码请求模型"""
    new_password: str = Field(..., min_length=6, description="新密码，最小长度为6个字符")