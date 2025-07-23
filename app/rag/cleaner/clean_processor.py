"""文本清理处理器"""
import re
from typing import List

from app.core.logger import Logger
from app.rag.cleaner.cleaner_base import BaseCleaner

class TextCleaner(BaseCleaner):
    """文本清理器，负责清理和预处理文本内容"""
    
    def clean(self, content: str) -> str:
        """清理文本内容
        
        Args:
            content: 原始文本内容
            
        Returns:
            str: 清理后的文本内容
        """
        try:
            # 去除多余的空白字符
            content = re.sub(r'\s+', ' ', content)
            
            # 去除特殊控制字符
            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
            
            # 规范化换行符
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            # 去除连续的换行符
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # 去除首尾空白
            content = content.strip()
            
            return content
            
        except Exception as e:
            Logger.error(f"Error cleaning text: {str(e)}")
            return content  # 如果清理失败，返回原始内容