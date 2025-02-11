from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class LLMConfig(BaseModel):
    llm: Dict[str, Any]
    embeddings: Dict[str, Any]

class KnowledgeBaseCreate(BaseModel):
    name: str
    domain: str = "通用知识领域"
    example_queries: List[str] = []
    entity_types: List[str] = []
    llm_config: LLMConfig

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    example_queries: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    llm_config: Optional[LLMConfig] = None

class KnowledgeBaseInDB(BaseModel):
    id: int
    name: str
    owner_id: int
    domain: str
    example_queries: List[str]
    entity_types: List[str]
    llm_config: LLMConfig
    working_dir: str

    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    query: str
    with_references: bool = False
    only_context: bool = False
    entities_max_tokens: int = 4000
    relationships_max_tokens: int = 3000
    chunks_max_tokens: int = 9000

class QueryResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None