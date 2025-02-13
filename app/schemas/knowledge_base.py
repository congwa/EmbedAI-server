from typing import Optional, Dict, Any, List
from pydantic import Field
from .base import CustomBaseModel

class LLMConfig(CustomBaseModel):
    llm: Dict[str, Any]
    embeddings: Dict[str, Any]

class KnowledgeBaseBase(CustomBaseModel):
    """知识库基础模型"""
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")

class KnowledgeBaseCreate(KnowledgeBaseBase):
    """知识库创建模型"""
    domain: str = Field("通用知识领域", description="知识库领域")
    example_queries: List[str] = []
    entity_types: List[str] = []
    llm_config: LLMConfig

class KnowledgeBaseUpdate(CustomBaseModel):
    """知识库更新模型"""
    name: Optional[str] = Field(None, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    domain: Optional[str] = Field(None, description="知识库领域")
    example_queries: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    llm_config: Optional[LLMConfig] = None

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

class KnowledgeBaseResponse(KnowledgeBaseInDB):
    """知识库响应模型"""
    pass

class QueryRequest(CustomBaseModel):
    """查询请求模型"""
    query: str = Field(..., description="查询内容")
    with_references: bool = Field(True, description="是否返回参考资料")
    only_context: bool = Field(False, description="是否只返回上下文")
    entities_max_tokens: int = Field(4000, description="实体最大token数")
    relationships_max_tokens: int = Field(3000, description="关系最大token数")
    chunks_max_tokens: int = Field(9000, description="块最大token数")

class QueryResponse(CustomBaseModel):
    """查询响应模型"""
    response: str
    context: Optional[Dict[str, Any]] = None