from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ModelConfig(BaseModel):
    domain: str
    example_queries: List[str]
    entity_types: List[str]
    llm: Dict[str, Any]
    embeddings: Dict[str, Any]

class KnowledgeBaseCreate(BaseModel):
    name: str
    model_config: ModelConfig

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    model_config: Optional[ModelConfig] = None

class KnowledgeBaseInDB(BaseModel):
    id: int
    name: str
    owner_id: int
    model_config: ModelConfig
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