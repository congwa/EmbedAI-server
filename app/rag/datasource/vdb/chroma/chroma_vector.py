"""Chroma向量存储实现"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.core.logger import Logger
from app.core.config import settings
from app.rag.datasource.vdb.vector_base import BaseVector
from app.rag.datasource.vdb.vector_type import VectorType
from app.rag.embedding.embedding_base import Embeddings
from app.rag.models.document import Document

class ChromaVector(BaseVector):
    """Chroma向量存储实现"""
    
    def __init__(
        self,
        collection_name: str,
        embedding_service: Embeddings,
        attributes: Optional[List[str]] = None
    ):
        """初始化Chroma向量存储
        
        Args:
            collection_name: 集合名称
            embedding_service: 嵌入服务
            attributes: 属性列表
        """
        super().__init__(collection_name)
        self.embedding_service = embedding_service
        self.attributes = attributes or ["doc_id", "document_id", "chunk_id", "knowledge_base_id"]
        
        # 创建Chroma客户端
        persist_directory = os.path.join(settings.VECTOR_STORE_PATH, "chroma")
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
    def get_type(self) -> str:
        """获取向量存储类型
        
        Returns:
            str: 向量存储类型
        """
        return VectorType.CHROMA
        
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
            ids = []
            documents = []
            metadatas = []
            
            for text, embedding in zip(texts, embeddings):
                # 获取文档ID
                doc_id = text.metadata.get("doc_id")
                if not doc_id:
                    continue
                    
                # 添加数据
                ids.append(doc_id)
                documents.append(text.page_content)
                
                # 提取元数据
                metadata = {}
                for attr in self.attributes:
                    if attr in text.metadata:
                        metadata[attr] = text.metadata[attr]
                metadatas.append(metadata)
                
            # 添加到集合
            if ids:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                
        except Exception as e:
            Logger.error(f"创建Chroma向量存储失败: {str(e)}")
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
            result = self.collection.get(ids=[id], include=[])
            return len(result["ids"]) > 0
        except Exception:
            return False
            
    async def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除文本
        
        Args:
            ids: ID列表
        """
        try:
            self.collection.delete(ids=ids)
        except Exception as e:
            Logger.error(f"删除文本失败: {str(e)}")
            
    async def delete_by_metadata_field(self, key: str, value: str) -> None:
        """根据元数据字段删除文本
        
        Args:
            key: 字段名
            value: 字段值
        """
        try:
            # 查询匹配的文档
            result = self.collection.get(
                where={key: value},
                include=[]
            )
            
            # 删除文档
            if result["ids"]:
                self.collection.delete(ids=result["ids"])
                
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
            where = kwargs.get("where", {})
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # 处理结果
            documents = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # 创建文档对象
                document = Document(
                    page_content=doc,
                    metadata={
                        **metadata,
                        "score": 1.0 - distance  # 转换距离为相似度分数
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
            where = kwargs.get("where", {})
            
            # 执行搜索
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # 处理结果
            documents = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # 创建文档对象
                document = Document(
                    page_content=doc,
                    metadata={
                        **metadata,
                        "score": 1.0 - distance  # 转换距离为相似度分数
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
            self.client.delete_collection(self.collection_name)
        except Exception as e:
            Logger.error(f"删除集合失败: {str(e)}")
            raise