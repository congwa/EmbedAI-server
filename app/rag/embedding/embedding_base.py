"""向量化基类"""
from abc import ABC, abstractmethod
from typing import List

class Embeddings(ABC):
    """向量化基类
    
    所有具体的向量化实现都应该继承这个基类
    """
    
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """向量化文档
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        raise NotImplementedError
        
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """向量化查询
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 查询向量
        """
        raise NotImplementedError