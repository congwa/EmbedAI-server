from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "GraphRAG Web API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT配置
    SECRET_KEY: str = "123456"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 默认模型配置
    DEFAULT_LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DEFAULT_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    DEFAULT_API_BASE: str = "https://api.siliconflow.cn/v1"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    # 优先加载环境变量的配置
    return Settings()

settings = get_settings()