from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str
    is_admin: bool = False
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