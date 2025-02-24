from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from functools import lru_cache
import os
from app.schemas.llm import LLMConfig, LLMServiceConfig, EmbeddingServiceConfig

class Settings(BaseSettings):
    PROJECT_NAME: str = "GraphRAG Web API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Admin configuration
    ADMIN_REGISTER_CODE: str = "123456"  # Add this line - you should change this in production
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./embed_ai.db"
    
    # JWT配置
    SECRET_KEY: str = "123456"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 默认模型配置
    DEFAULT_LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DEFAULT_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    DEFAULT_API_BASE: str = "https://api.siliconflow.cn/v1"

    # 默认API密钥 必须在环境变量提供
    DEFAULT_API_KEY: str = os.getenv("OPENAI_API_KEY", "sk-trczwprxbdczhgqhrnevtxesrympmeawffgkdopnyofqttsg")
    DEFAULT_EMBEDDING_DIM: int = 1536
    
    # 训练配置
    ENABLE_TRAINING_QUEUE: bool = True  # 是否启用训练队列（同一时间只允许一个知识库训练）

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

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()