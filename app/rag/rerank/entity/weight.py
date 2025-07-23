"""重排序权重实体类"""
from typing import Optional
from pydantic import BaseModel, Field


class VectorSetting(BaseModel):
    """向量设置"""
    vector_weight: float = Field(default=1.0, description="向量权重")
    model_name: Optional[str] = Field(default=None, description="模型名称")
    model_provider: Optional[str] = Field(default=None, description="模型提供商")


class KeywordSetting(BaseModel):
    """关键词设置"""
    keyword_weight: float = Field(default=1.0, description="关键词权重")
    k1: float = Field(default=1.5, description="BM25参数k1")
    b: float = Field(default=0.75, description="BM25参数b")


class Weights(BaseModel):
    """重排序权重"""
    vector_setting: VectorSetting = Field(default_factory=VectorSetting, description="向量设置")
    keyword_setting: KeywordSetting = Field(default_factory=KeywordSetting, description="关键词设置") 