"""检索方法枚举"""
from enum import Enum

class RetrievalMethod(str, Enum):
    """检索方法枚举"""
    SEMANTIC_SEARCH = "semantic_search"  # 语义搜索
    KEYWORD_SEARCH = "keyword_search"    # 关键词搜索
    HYBRID_SEARCH = "hybrid_search"      # 混合搜索