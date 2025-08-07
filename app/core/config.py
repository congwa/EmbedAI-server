from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from functools import lru_cache
import os
from app.schemas.llm import LLMConfig, LLMServiceConfig, EmbeddingServiceConfig

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG Knowledge Base API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Debug configuration
    DEBUG: bool = True  # 调试模式
    
    # Admin configuration
    ADMIN_REGISTER_CODE: str = "123456"  # Add this line - you should change this in production
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./embed_ai.db"

    # 文件存储路径
    FILE_STORAGE_PATH: str = "storage/documents"
    
    # JWT配置
    SECRET_KEY: str = "123456"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 默认模型配置
    DEFAULT_LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DEFAULT_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    DEFAULT_API_BASE: str = "https://api.siliconflow.cn/v1"

    # 默认API密钥 必须在环境变量提供
    DEFAULT_API_KEY: str = os.getenv("ZHIPU_API_KEY", "sk-trczwprxbdczhgqhrnevtxesrympmeawffgkdopnyofqttsg")
    DEFAULT_EMBEDDING_DIM: int = 1024
    
    # 训练配置
    ENABLE_TRAINING_QUEUE: bool = True  # 是否启用训练队列（同一时间只允许一个知识库训练）
    
    # RAG配置
    RAG_CHUNK_SIZE: int = 1000  # 文本分块大小
    RAG_CHUNK_OVERLAP: int = 200  # 文本分块重叠大小
    RAG_VECTOR_STORE_TYPE: str = "chroma"  # 默认向量存储类型
    RAG_BATCH_SIZE: int = 100  # 批处理大小
    RAG_RERANK_MODEL: str = "bge-reranker-base"  # 重排序模型
    RAG_DEFAULT_RETRIEVAL_METHOD: str = "hybrid_search"  # 默认检索方法
    RAG_USE_RERANK: bool = True  # 是否默认使用重排序

    # 模型定价（美元/千Token）
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "Qwen/Qwen2.5-7B-Instruct": {"prompt": 0.001, "completion": 0.002},
        "BAAI/bge-m3": {"prompt": 0.0001, "completion": 0},  # Embedding models only have prompt cost
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    }
 
    @property
    def DEFAULT_LLM_CONFIG(self) -> LLMConfig:
        """默认的 LLM 配置，使用环境变量和默认值构建"""
        return LLMConfig(
            llm=LLMServiceConfig(
                model=self.DEFAULT_LLM_MODEL,
                base_url=self.DEFAULT_API_BASE,
                api_key=self.DEFAULT_API_KEY
            ),
            embeddings=EmbeddingServiceConfig(
                model=self.DEFAULT_EMBEDDING_MODEL,
                base_url=self.DEFAULT_API_BASE,
                api_key=self.DEFAULT_API_KEY,
                embedding_dim=self.DEFAULT_EMBEDDING_DIM
            )
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def validate_rag_config(settings: Settings) -> Dict[str, Any]:
    """验证RAG配置
    
    Args:
        settings: 配置对象
        
    Returns:
        Dict[str, Any]: 验证后的RAG配置
    """
    # 验证分块大小
    chunk_size = settings.RAG_CHUNK_SIZE
    if chunk_size < 100:
        chunk_size = 100
    elif chunk_size > 10000:
        chunk_size = 10000
        
    # 验证分块重叠大小
    chunk_overlap = settings.RAG_CHUNK_OVERLAP
    if chunk_overlap < 0:
        chunk_overlap = 0
    elif chunk_overlap > chunk_size // 2:
        chunk_overlap = chunk_size // 2
        
    # 验证向量存储类型
    vector_store_type = settings.RAG_VECTOR_STORE_TYPE
    supported_vector_stores = ["chroma", "qdrant"]
    if vector_store_type not in supported_vector_stores:
        vector_store_type = "chroma"
        
    # 验证批处理大小
    batch_size = settings.RAG_BATCH_SIZE
    if batch_size < 1:
        batch_size = 1
    elif batch_size > 1000:
        batch_size = 1000
        
    # 验证检索方法
    retrieval_method = settings.RAG_DEFAULT_RETRIEVAL_METHOD
    supported_methods = ["semantic_search", "keyword_search", "hybrid_search"]
    if retrieval_method not in supported_methods:
        retrieval_method = "hybrid_search"
        
    return {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "vector_store_type": vector_store_type,
        "batch_size": batch_size,
        "rerank_model": settings.RAG_RERANK_MODEL,
        "retrieval_method": retrieval_method,
        "use_rerank": settings.RAG_USE_RERANK
    }

@lru_cache()
def get_settings():
    settings = Settings()
    # 验证RAG配置
    # settings.rag_config = validate_rag_config(settings)
    return settings

settings = get_settings()