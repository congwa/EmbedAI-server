from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str
    is_admin: bool = False
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    email: str
    is_admin: bool
    is_active: bool
    sdk_key: Optional[str]
    secret_key: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(UserBase):
    password: Optional[str] = None
    class Config:
        from_attributes = True

class UserInDB(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    class Config:
        from_attributes = True

class UserInfo(BaseModel):
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    class Config:
        from_attributes = True

class UserListItem(BaseModel):
    id: int
    email: str
    sdk_key: Optional[str]
    secret_key: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    email: Optional[str] = None

    class Config:
        from_attributes = True

class AdminChangeUserPasswordRequest(BaseModel):
    """管理员修改用户密码请求模型"""
    new_password: str = Field(..., min_length=6, description="新密码，最小长度为6个字符")

    class Config:
        from_attributes = True