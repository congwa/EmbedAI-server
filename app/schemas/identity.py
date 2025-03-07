from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.base import CustomBaseModel
from pydantic import ConfigDict

class UserType(str, Enum):
    """用户类型枚举"""
    OFFICIAL = "official"  # 官方用户
    THIRD_PARTY = "third_party"  # 第三方用户

class UserContext(BaseModel):
    """用户上下文信息"""
    user_type: UserType
    user_id: int
    client_id: str
    identity_id: Optional[int] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_type": "third_party",
                "user_id": 123,
                "client_id": "client_xyz",
                "identity_id": 456
            }
        }
    )

