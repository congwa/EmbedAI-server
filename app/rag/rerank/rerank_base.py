"""重排序基类"""
from abc import ABC, abstractmethod
from typing import Optional

from app.rag.models.document import Document


class BaseRerankRunner(ABC):
    """重排序运行器基类"""
    
    @abstractmethod
    def run(
        self,
        query: str,
        documents: list[Document],
        score_threshold: Optional[float] = None,
        top_n: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> list[Document]:
        """
        运行重排序
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            score_threshold: 分数阈值，低于此分数的文档将被过滤
            top_n: 返回的最大文档数量
            user_id: 用户ID（如果需要）
            
        Returns:
            重排序后的文档列表
        """
        raise NotImplementedError 