"""文本清理器基类"""
from abc import ABC, abstractmethod

class BaseCleaner(ABC):
    """文本清理器基类
    
    所有具体的文本清理器都应该继承这个基类
    """
    
    @abstractmethod
    def clean(self, content: str) -> str:
        """清理文本内容
        
        Args:
            content: 原始文本内容
            
        Returns:
            str: 清理后的文本内容
        """
        raise NotImplementedError