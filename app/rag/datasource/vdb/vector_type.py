"""向量存储类型"""
from enum import Enum

class VectorType(str, Enum):
    """向量存储类型枚举"""
    CHROMA = "chroma"
    QDRANT = "qdrant"
    MILVUS = "milvus"
    PGVECTOR = "pgvector"
    FAISS = "faiss"
    # 可以添加更多向量存储类型