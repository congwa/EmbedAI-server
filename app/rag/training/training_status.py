"""训练状态和结果类"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TrainingError(Enum):
    """训练错误类型枚举"""
    NO_DOCUMENTS = "no_documents"  # 没有文档
    DOCUMENT_PROCESSING_ERROR = "document_processing_error"  # 文档处理错误
    EMBEDDING_ERROR = "embedding_error"  # 向量化错误
    INDEX_BUILDING_ERROR = "index_building_error"  # 索引构建错误
    TIMEOUT = "timeout"  # 超时
    UNKNOWN = "unknown"  # 未知错误


class TrainingResult(BaseModel):
    """训练结果类"""
    success: bool = Field(default=False, description="是否成功")
    error_type: Optional[TrainingError] = Field(default=None, description="错误类型")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    document_count: int = Field(default=0, description="处理的文档数量")
    chunk_count: int = Field(default=0, description="生成的文档块数量")
    embedding_count: int = Field(default=0, description="生成的向量数量")
    processing_time: float = Field(default=0.0, description="处理时间(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = self.model_dump()
        if result.get("error_type") and isinstance(result["error_type"], TrainingError):
            result["error_type"] = result["error_type"].value
        return result 