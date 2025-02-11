from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 默认模型配置
    DEFAULT_LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DEFAULT_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    DEFAULT_API_BASE: str = "https://api.siliconflow.cn/v1"
    
    # 训练配置
    ENABLE_TRAINING_QUEUE: bool = True  # 是否启用训练队列（同一时间只允许一个知识库训练）
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    # 优先加载环境变量的配置
    return Settings()

settings = get_settings()