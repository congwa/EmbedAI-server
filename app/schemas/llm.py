from typing import Optional
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