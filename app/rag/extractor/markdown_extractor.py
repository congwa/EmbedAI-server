"""Markdown提取器，负责从Markdown文件中提取内容"""
import os
from typing import List, Dict, Any
import chardet

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class MarkdownExtractor(BaseExtractor):
    """Markdown提取器，负责从Markdown文件中提取内容"""
    
    def __init__(self, autodetect_encoding: bool = True):
        """初始化Markdown提取器
        
        Args:
            autodetect_encoding: 是否自动检测编码
        """
        self.autodetect_encoding = autodetect_encoding
        
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从Markdown文件中提取内容
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
                
            # 读取文件内容
            encoding = 'utf-8'
            if self.autodetect_encoding:
                # 检测文件编码
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] or 'utf-8'
                    
            # 读取文件内容
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                
            # 返回提取的内容
            return [{
                "text": content,
                "metadata": {
                    "source_type": "markdown",
                    "file_path": file_path,
                    "encoding": encoding
                }
            }]
            
        except Exception as e:
            Logger.error(f"Error extracting text from Markdown file {file_path}: {str(e)}")
            return []