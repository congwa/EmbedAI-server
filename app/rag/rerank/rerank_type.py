"""重排序类型枚举"""
from enum import Enum

class RerankMode(str, Enum):
    """重排序模式枚举"""
    RERANKING_MODEL = "reranking_model"  # 使用重排序模型
    WEIGHTED_SCORE = "weighted_score"    # 使用加权分数 