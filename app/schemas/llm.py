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
    """LLM 完整配置

    该类用于配置大语言模型（LLM）及其嵌入服务的相关参数。它包含以下属性：
    
    - llm: LLM 服务的配置，包括模型名称、基础 URL 和 API 密钥。
    - embeddings: 嵌入服务的配置，包括模型名称、基础 URL、API 密钥和嵌入维度。
    - domain: 可选的领域描述，默认为"通用知识领域"。
    - example_queries: 可选的示例查询列表，帮助用户理解如何使用该服务。
    - entity_types: 可选的实体类型列表，用于指定模型处理的特定实体类型。

    此类还提供了将配置转换为字典格式的方法，以便于序列化和存储。
    """
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