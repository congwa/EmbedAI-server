"""向量存储基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.rag.models.document import Document

class BaseVector(ABC):
    """向量存储基类
    
    所有具体的向量存储实现都应该继承这个基类
    """
    
    def __init__(self, collection_name: str):
        """初始化向量存储
        
        Args:
            collection_name: 集合名称
        """
        self._collection_name = collection_name
        
    @abstractmethod
    def get_type(self) -> str:
        """获取向量存储类型
        
        Returns:
            str: 向量存储类型
        """
        raise NotImplementedError
        
    @abstractmethod
    async def create(self, texts: List[Document], embeddings: List[List[float]], **kwargs):
        """创建向量存储
        
        Args:
            texts: 文档列表
            embeddings: 向量列表
            **kwargs: 其他参数
        """
        raise NotImplementedError
        
    @abstractmethod
    async def add_texts(self, documents: List[Document], embeddings: List[List[float]], **kwargs):
        """添加文本
        
        Args:
            documents: 文档列表
            embeddings: 向量列表
            **kwargs: 其他参数
        """
        raise NotImplementedError
        
    @abstractmethod
    async def text_exists(self, id: str) -> bool:
        """检查文本是否存在
        
        Args:
            id: 文本ID
            
        Returns:
            bool: 是否存在
        """
        raise NotImplementedError
        
    @abstractmethod
    async def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除文本
        
        Args:
            ids: ID列表
        """
        raise NotImplementedError
        
    @abstractmethod
    async def delete_by_metadata_field(self, key: str, value: str) -> None:
        """根据元数据字段删除文本
        
        Args:
            key: 字段名
            value: 字段值
        """
        raise NotImplementedError
        
    @abstractmethod
    async def search_by_vector(self, query_vector: List[float], **kwargs: Any) -> List[Document]:
        """根据向量搜索
        
        Args:
            query_vector: 查询向量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 搜索结果
        """
        raise NotImplementedError
        
    @abstractmethod
    async def search_by_full_text(self, query: str, **kwargs: Any) -> List[Document]:
        """全文搜索
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 搜索结果
        """
        raise NotImplementedError
        
    @abstractmethod
    async def delete(self) -> None:
        """删除向量存储"""
        raise NotImplementedError
        
    async def _filter_duplicate_texts(self, texts: List[Document]) -> List[Document]:
        """过滤重复文本
        
        Args:
            texts: 文档列表
            
        Returns:
            List[Document]: 过滤后的文档列表
        """
        filtered_texts = []
        for text in texts:
            if text.metadata and "doc_id" in text.metadata:
                doc_id = text.metadata["doc_id"]
                exists = await self.text_exists(doc_id)
                if not exists:
                    filtered_texts.append(text)
            else:
                filtered_texts.append(text)
                
        return filtered_texts
        
    def _get_uuids(self, texts: List[Document]) -> List[str]:
        """获取UUID列表
        
        Args:
            texts: 文档列表
            
        Returns:
            List[str]: UUID列表
        """
        return [
            text.metadata["doc_id"]
            for text in texts
            if text.metadata and "doc_id" in text.metadata
        ]
        
    @property
    def collection_name(self) -> str:
        """获取集合名称
        
        Returns:
            str: 集合名称
        """
        return self._collection_name