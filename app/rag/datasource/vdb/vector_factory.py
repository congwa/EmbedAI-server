"""向量存储工厂"""
from typing import Dict, Any, Optional, Type

from app.core.logger import Logger
from app.core.config import settings
from app.schemas.llm import LLMConfig
from app.models.knowledge_base import KnowledgeBase
from app.rag.datasource.vdb.vector_base import BaseVector
from app.rag.datasource.vdb.vector_type import VectorType
from app.rag.embedding.cached_embedding import CacheEmbedding

class VectorFactory:
    """向量存储工厂
    
    负责创建不同类型的向量存储实例
    """
    
    @staticmethod
    def create_vector_store(
        knowledge_base: KnowledgeBase,
        llm_config: LLMConfig,
        attributes: Optional[list] = None
    ) -> BaseVector:
        """创建向量存储
        
        Args:
            knowledge_base: 知识库
            llm_config: LLM配置
            attributes: 属性列表
            
        Returns:
            BaseVector: 向量存储实例
        """
        if attributes is None:
            attributes = ["doc_id", "document_id", "chunk_id", "knowledge_base_id"]
            
        # 获取向量存储类型
        vector_type = knowledge_base.vector_store_type or settings.RAG_VECTOR_STORE_TYPE
        
        # 创建嵌入服务
        embedding_service = CacheEmbedding(llm_config)
        
        # 创建集合名称
        collection_name = f"kb_{knowledge_base.id}"
        
        # 根据类型创建向量存储
        try:
            if vector_type == VectorType.CHROMA:
                from app.rag.datasource.vdb.chroma.chroma_vector import ChromaVector
                return ChromaVector(collection_name, embedding_service, attributes)
            elif vector_type == VectorType.QDRANT:
                from app.rag.datasource.vdb.qdrant.qdrant_vector import QdrantVector
                return QdrantVector(collection_name, embedding_service, attributes)
            elif vector_type == VectorType.MILVUS:
                from app.rag.datasource.vdb.milvus.milvus_vector import MilvusVector
                return MilvusVector(collection_name, embedding_service, attributes)
            elif vector_type == VectorType.PGVECTOR:
                from app.rag.datasource.vdb.pgvector.pgvector import PGVector
                return PGVector(collection_name, embedding_service, attributes)
            elif vector_type == VectorType.FAISS:
                from app.rag.datasource.vdb.faiss.faiss_vector import FAISSVector
                return FAISSVector(collection_name, embedding_service, attributes)
            else:
                # 默认使用Chroma
                Logger.warning(f"未知的向量存储类型: {vector_type}，使用默认的Chroma")
                from app.rag.datasource.vdb.chroma.chroma_vector import ChromaVector
                return ChromaVector(collection_name, embedding_service, attributes)
        except ImportError as e:
            Logger.error(f"导入向量存储模块失败: {str(e)}，使用默认的Chroma")
            from app.rag.datasource.vdb.chroma.chroma_vector import ChromaVector
            return ChromaVector(collection_name, embedding_service, attributes)
        except Exception as e:
            Logger.error(f"创建向量存储失败: {str(e)}，使用默认的Chroma")
            from app.rag.datasource.vdb.chroma.chroma_vector import ChromaVector
            return ChromaVector(collection_name, embedding_service, attributes)