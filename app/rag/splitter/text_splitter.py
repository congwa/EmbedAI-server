"""文本分块器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional

from app.rag.models.document import Document

class TextSplitter(ABC):
    """文本分块器基类
    
    所有具体的文本分块器都应该继承这个基类
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
    ):
        """初始化文本分块器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            length_function: 计算文本长度的函数
        """
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"分块重叠大小 ({chunk_overlap}) 大于分块大小 ({chunk_size})，应该更小。"
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """将文本分割为多个块
        
        Args:
            text: 要分割的文本
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        raise NotImplementedError
        
    def create_documents(
        self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Document]:
        """从文本列表创建文档对象
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表，与texts一一对应
            
        Returns:
            List[Document]: 文档对象列表
        """
        _metadatas = metadatas or [{}] * len(texts)
        documents = []
        
        for i, text in enumerate(texts):
            for chunk in self.split_text(text):
                metadata = _metadatas[i].copy()
                doc = Document(page_content=chunk, metadata=metadata)
                documents.append(doc)
                
        return documents
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """分割文档对象
        
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档对象列表
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        return self.create_documents(texts, metadatas)