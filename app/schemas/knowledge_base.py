from typing import Optional, Dict, Any, List
from pydantic import Field, BaseModel, ConfigDict
from .base import CustomBaseModel
from datetime import datetime
from app.models.knowledge_base import TrainingStatus, PermissionType
from .llm import LLMConfig


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    domain: str
    example_queries: Optional[List[str]] = []
    entity_types: Optional[List[str]] = []
    llm_config: Optional[LLMConfig] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "测试知识库",
                "domain": "通用领域",
                "example_queries": ["问题1", "问题2"],
                "entity_types": ["实体1", "实体2"],
                "llm_config": {
                    "llm": {
                        "model": "gpt-3.5-turbo",
                        "base_url": "https://api.openai.com/v1",
                        "api_key": "your-api-key"
                    },
                    "embeddings": {
                        "model": "text-embedding-3-small",
                        "base_url": "https://api.openai.com/v1",
                        "api_key": "your-api-key",
                        "embedding_dim": 1536
                    }
                }
            }
        }
    )

class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = None
    domain: Optional[str] = None
    example_queries: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    llm_config: Optional[LLMConfig] = None


class QueryRequest(BaseModel):
    """查询请求"""
    query: str
    top_k: int = 5

class QueryResponse(BaseModel):
    """查询响应"""
    query: str
    results: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeBasePermissionCreate(CustomBaseModel):
    user_id: int
    permission: PermissionType = PermissionType.VIEWER

class KnowledgeBasePermissionUpdate(CustomBaseModel):
    permission: PermissionType

class KnowledgeBasePermission(CustomBaseModel):
    user_id: int
    knowledge_base_id: int
    permission: PermissionType
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class KnowledgeBase(CustomBaseModel):
    id: int
    name: str
    owner_id: int
    domain: str
    example_queries: List[str]
    entity_types: List[str]
    llm_config: Optional[LLMConfig]
    working_dir: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    training_status: TrainingStatus
    training_started_at: Optional[datetime]
    training_finished_at: Optional[datetime]
    training_error: Optional[str]
    queued_at: Optional[datetime]
    members: Optional[List[Dict[str, Any]]] = None
    model_config = ConfigDict(from_attributes=True)

class KnowledgeBaseMemberInfo(CustomBaseModel):
    """知识库成员信息"""
    id: int
    email: str
    permission: PermissionType
    is_owner: bool
    is_admin: bool
    created_at: Optional[datetime] = None

class KnowledgeBaseMemberCreate(CustomBaseModel):
    """添加知识库成员请求"""
    user_id: int
    permission: PermissionType = PermissionType.VIEWER
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "permission": "viewer"
            }
        }
    )

class KnowledgeBaseMemberUpdate(CustomBaseModel):
    """更新知识库成员权限请求"""
    permission: PermissionType
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "permission": "editor"
            }
        }
    )

class KnowledgeBaseMemberList(CustomBaseModel):
    """知识库成员列表响应"""
    members: List[KnowledgeBaseMemberInfo]
    total: int
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "members": [
                    {
                        "id": 1,
                        "email": "user@example.com",
                        "permission": "viewer",
                        "is_owner": False,
                        "is_admin": False,
                        "created_at": "2024-02-17T10:00:00"
                    }
                ],
                "total": 1
            }
        }
    )