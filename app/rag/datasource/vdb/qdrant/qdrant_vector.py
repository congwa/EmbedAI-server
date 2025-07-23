"""Qdrant向量存储实现"""
from typing import List, Dict, Any, Optional
import qdrant_client
from qdrant_client.http import models

from app.core.logger import Logger
from app.core.config import settings
from app.rag.datasource.vdb.vector_base import BaseVector
from app.rag.datasource.vdb.vector_type import VectorType
from app.rag.embedding.embedding_base import Embeddings
from app.rag.models.document import Document

class QdrantVector(BaseVector):
    """Qdrant向量存储实现"""
    
    def __init__(
        self,
        collection_name: str,
        embedding_service: Embeddings,
        attributes: Optional[List[str]] = None
    ):
        """初始化Qdrant向量存储
        
        Args:
            collection_name: 集合名称
            embedding_service: 嵌入服务
            attributes: 属性列表
        """
        super().__init__(collection_name)
        self.embedding_service = embedding_service
        self.attributes = attributes or ["doc_id", "document_id", "chunk_id", "knowledge_base_id"]
        
        # 创建Qdrant客户端
        self.client = qdrant_client.QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        
        # 获取或创建集合
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if collection_name not in collection_names:
                # 创建集合
                vector_size = settings.DEFAULT_EMBEDDING_DIM  # 向量维度
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            Logger.error(f"初始化Qdrant集合失败: {str(e)}")
            raise
            
    def get_type(self) -> str:
        """获取向量存储类型
        
        Returns:
            str: 向量存储类型
        """
        return VectorType.QDRANT
        
    async def create(self, texts: List[Document], embeddings: List[List[float]], **kwargs):
        """创建向量存储
        
        Args:
            texts: 文档列表
            embeddings: 向量列表
            **kwargs: 其他参数
        """
        try:
            # 检查文档和向量数量是否一致
            if len(texts) != len(embeddings):
                raise ValueError(f"文档数量 ({len(texts)}) 与向量数量 ({len(embeddings)}) 不一致")
                
            # 准备数据
            points = []
            
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                # 获取文档ID
                doc_id = text.metadata.get("doc_id")
                if not doc_id:
                    continue
                    
                # 提取元数据
                payload = {
                    "text": text.page_content,
                }
                
                # 添加属性
                for attr in self.attributes:
                    if attr in text.metadata:
                        payload[attr] = text.metadata[attr]
                        
                # 创建点
                point = models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
                
            # 添加到集合
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
        except Exception as e:
            Logger.error(f"创建Qdrant向量存储失败: {str(e)}")
            raise
            
    async def add_texts(self, documents: List[Document], embeddings: List[List[float]], **kwargs):
        """添加文本
        
        Args:
            documents: 文档列表
            embeddings: 向量列表
            **kwargs: 其他参数
        """
        # 过滤重复文档
        if kwargs.get("duplicate_check", False):
            documents = await self._filter_duplicate_texts(documents)
            
        # 创建向量存储
        await self.create(documents, embeddings, **kwargs)
        
    async def text_exists(self, id: str) -> bool:
        """检查文本是否存在
        
        Args:
            id: 文本ID
            
        Returns:
            bool: 是否存在
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[id]
            )
            return len(result) > 0
        except Exception:
            return False
            
    async def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除文本
        
        Args:
            ids: ID列表
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
        except Exception as e:
            Logger.error(f"删除文本失败: {str(e)}")
            
    async def delete_by_metadata_field(self, key: str, value: str) -> None:
        """根据元数据字段删除文本
        
        Args:
            key: 字段名
            value: 字段值
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            Logger.error(f"根据元数据删除文本失败: {str(e)}")
            
    async def search_by_vector(self, query_vector: List[float], **kwargs: Any) -> List[Document]:
        """根据向量搜索
        
        Args:
            query_vector: 查询向量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 搜索结果
        """
        try:
            # 获取参数
            top_k = kwargs.get("top_k", 5)
            filter_condition = kwargs.get("filter", None)
            
            # 执行搜索
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filter_condition
            )
            
            # 处理结果
            documents = []
            for result in results:
                # 创建文档对象
                document = Document(
                    page_content=result.payload.get("text", ""),
                    metadata={
                        **{k: v for k, v in result.payload.items() if k != "text"},
                        "score": result.score
                    }
                )
                documents.append(document)
                
            return documents
            
        except Exception as e:
            Logger.error(f"向量搜索失败: {str(e)}")
            return []
            
    async def search_by_full_text(self, query: str, **kwargs: Any) -> List[Document]:
        """全文搜索
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 搜索结果
        """
        try:
            # 获取参数
            top_k = kwargs.get("top_k", 5)
            
            # 执行搜索
            results = self.client.search(
                collection_name=self.collection_name,
                query_text=query,
                limit=top_k
            )
            
            # 处理结果
            documents = []
            for result in results:
                # 创建文档对象
                document = Document(
                    page_content=result.payload.get("text", ""),
                    metadata={
                        **{k: v for k, v in result.payload.items() if k != "text"},
                        "score": result.score
                    }
                )
                documents.append(document)
                
            return documents
            
        except Exception as e:
            Logger.error(f"全文搜索失败: {str(e)}")
            return []
            
    async def delete(self) -> None:
        """删除向量存储"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except Exception as e:
            Logger.error(f"删除集合失败: {str(e)}")
            raise