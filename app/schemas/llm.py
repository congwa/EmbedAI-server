from typing import Optional, Dict, Any, List
from .base import CustomBaseModel

class LLMServiceConfig(CustomBaseModel):
    """LLM 服务配置"""
    model: str
    base_url: str
    api_key: str

class EmbeddingServiceConfig(CustomBaseModel):
    """Embedding 服务配置"""
    model: str
    base_url: str
    api_key: str
    embedding_dim: int

class LLMConfig(CustomBaseModel):
    """LLM 完整配置"""
    llm: LLMServiceConfig
    embeddings: EmbeddingServiceConfig
    domain: Optional[str] = "通用知识领域"
    example_queries: Optional[List[str]] = []
    entity_types: Optional[List[str]] = []
    
    def model_dump(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = super().model_dump()
        # 确保 llm 和 embeddings 也被转换为字典
        data["llm"] = self.llm.model_dump() if self.llm else {}
        data["embeddings"] = self.embeddings.model_dump() if self.embeddings else {}
        return data 