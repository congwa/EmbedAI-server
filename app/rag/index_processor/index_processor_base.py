"""索引处理器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document as DBDocument
from app.rag.models.document import Document

class BaseIndexProcessor(ABC):
    """索引处理器基类
    
    所有具体的索引处理器都应该继承这个基类
    """
    
    @abstractmethod
    async def extract(self, document: DBDocument) -> List[Document]:
        """从文档中提取内容
        
        Args:
            document: 数据库文档对象
            
        Returns:
            List[Document]: 提取的文档对象列表
        """
        raise NotImplementedError
        
    @abstractmethod
    async def transform(self, documents: List[Document], **kwargs) -> List[Document]:
        """转换文档
        
        Args:
            documents: 文档对象列表
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 转换后的文档对象列表
        """
        raise NotImplementedError
        
    @abstractmethod
    async def load(self, knowledge_base: KnowledgeBase, documents: List[Document], **kwargs) -> None:
        """加载文档到索引
        
        Args:
            knowledge_base: 知识库对象
            documents: 文档对象列表
            **kwargs: 其他参数
        """
        raise NotImplementedError
        
    @abstractmethod
    async def clean(self, knowledge_base: KnowledgeBase, document_ids: Optional[List[str]] = None, **kwargs) -> None:
        """清理索引
        
        Args:
            knowledge_base: 知识库对象
            document_ids: 文档ID列表，如果为None则清理整个索引
            **kwargs: 其他参数
        """
        raise NotImplementedError
        
    @abstractmethod
    async def retrieve(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """检索文档
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        raise NotImplementedError