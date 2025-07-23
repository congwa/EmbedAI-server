"""文档提取器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseExtractor(ABC):
    """文档提取器基类
    
    所有具体的文档提取器都应该继承这个基类
    """
    
    @abstractmethod
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从文档中提取文本内容
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表，每个元素包含文本内容和元数据
        """
        raise NotImplementedError