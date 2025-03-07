from typing import Optional
from datetime import datetime
from pydantic import EmailStr, Field
from .base import CustomBaseModel
from pydantic import ConfigDict

class UserStatusUpdate(CustomBaseModel):
    """用户状态更新请求模型"""
    is_active: bool

class UserBase(CustomBaseModel):
    """用户基础模型"""
    email: EmailStr

class UserCreate(UserBase):
    """用户创建请求模型"""
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
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(CustomBaseModel):
    """用户更新请求模型"""
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    model_config = ConfigDict(from_attributes=True)

class UserInfo(CustomBaseModel):
    """用户信息响应模型"""
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Pydantic模型(UserListItem)只返回安全的字段：
class UserListItem(CustomBaseModel):
    """用户列表项响应模型"""
    id: int
    email: str
    is_active: bool
    sdk_key: Optional[str]
    secret_key: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(CustomBaseModel):
    """登录令牌响应模型"""
    access_token: str
    user: UserInfo
    model_config = ConfigDict(from_attributes=True)

class AdminChangeUserPasswordRequest(CustomBaseModel):
    """管理员修改用户密码请求模型"""
    new_password: str = Field(..., min_length=6, description="新密码，最小长度为6个字符")
    model_config = ConfigDict(from_attributes=True)
