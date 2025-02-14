from typing import Optional, Dict, Any, List
from pydantic import Field, BaseModel
from .base import CustomBaseModel
from datetime import datetime
from app.models.knowledge_base import TrainingStatus, PermissionType

class LLMConfig(CustomBaseModel):
    llm: Dict[str, Any]
    embeddings: Dict[str, Any]

class KnowledgeBaseBase(CustomBaseModel):
    """知识库基础模型"""
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    domain: str
    example_queries: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    llm_config: Optional[Dict[str, Any]] = None

class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = None
    domain: Optional[str] = None
    example_queries: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    llm_config: Optional[Dict[str, Any]] = None

class KnowledgeBaseInDB(KnowledgeBaseBase):
    """数据库中的知识库模型"""
    id: int = Field(..., description="知识库ID")
    user_id: int = Field(..., description="所属用户ID")
    is_deleted: bool = Field(False, description="是否已删除")
    domain: str
    example_queries: List[str]
    entity_types: List[str]
    llm_config: LLMConfig
    working_dir: str
    training_status: TrainingStatus
    training_started_at: Optional[datetime]
    training_finished_at: Optional[datetime]
    training_error: Optional[str]
    queued_at: Optional[datetime]

class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    domain: str
    owner_id: int
    example_queries: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    llm_config: Optional[Dict[str, Any]] = None
    working_dir: Optional[str] = None
    training_status: TrainingStatus
    training_started_at: Optional[datetime] = None
    training_finished_at: Optional[datetime] = None
    training_error: Optional[str] = None
    queued_at: Optional[datetime] = None

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class KnowledgeBase(CustomBaseModel):
    id: int
    name: str
    owner_id: int
    domain: str
    example_queries: List[str]
    entity_types: List[str]
    llm_config: Optional[Dict[str, Any]]
    working_dir: Optional[str]
    training_status: TrainingStatus
    training_started_at: Optional[datetime]
    training_finished_at: Optional[datetime]
    training_error: Optional[str]
    queued_at: Optional[datetime]

    class Config:
        from_attributes = True