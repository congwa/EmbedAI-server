"""向量化引擎"""
from typing import List, Dict, Any, Optional
import numpy as np

from app.core.logger import Logger
from app.schemas.llm import LLMConfig
from app.rag.embedding.cached_embedding import CacheEmbedding
from app.rag.models.document import Document

class EmbeddingEngine:
    """向量化引擎
    
    负责将文本转换为向量表示
    """
    
    def __init__(self, llm_config: LLMConfig):
        """初始化向量化引擎
        
        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config
        self.embedding_service = CacheEmbedding(llm_config)
        
    async def embed_documents(self, documents: List[Document]) -> List[Document]:
        """向量化文档
        
        Args:
            documents: 文档列表
            
        Returns:
            List[Document]: 向量化后的文档列表
        """
        try:
            # 提取文本内容
            texts = [doc.page_content for doc in documents]
            
            # 向量化
            embeddings = await self.embedding_service.embed_documents(texts)
            
            # 更新文档对象
            for doc, embedding in zip(documents, embeddings):
                doc.vector = embedding
                
            return documents
            
        except Exception as e:
            Logger.error(f"向量化文档失败: {str(e)}")
            raise
            
    async def embed_query(self, query: str) -> List[float]:
        """向量化查询
        
        Args:
            query: 查询文本
            
        Returns:
            List[float]: 查询向量
        """
        try:
            return await self.embedding_service.embed_query(query)
        except Exception as e:
            Logger.error(f"向量化查询失败: {str(e)}")
            raise
            
    async def batch_embed_documents(
        self, documents: List[Document], batch_size: int = 100
    ) -> List[Document]:
        """批量向量化文档
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
            
        Returns:
            List[Document]: 向量化后的文档列表
        """
        try:
            # 分批处理
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                await self.embed_documents(batch)
                Logger.info(f"已向量化 {i+len(batch)}/{len(documents)} 个文档")
                
            return documents
            
        except Exception as e:
            Logger.error(f"批量向量化文档失败: {str(e)}")
            raise
            
    async def compute_similarity(
        self, query_vector: List[float], document_vectors: List[List[float]]
    ) -> List[float]:
        """计算相似度
        
        Args:
            query_vector: 查询向量
            document_vectors: 文档向量列表
            
        Returns:
            List[float]: 相似度列表
        """
        try:
            # 转换为numpy数组
            query_array = np.array(query_vector)
            doc_arrays = np.array(document_vectors)
            
            # 计算余弦相似度
            similarities = np.dot(doc_arrays, query_array) / (
                np.linalg.norm(doc_arrays, axis=1) * np.linalg.norm(query_array)
            )
            
            return similarities.tolist()
            
        except Exception as e:
            Logger.error(f"计算相似度失败: {str(e)}")
            raise