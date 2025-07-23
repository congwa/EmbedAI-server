"""HTML提取器，负责从HTML文件中提取内容"""
import os
from typing import List, Dict, Any
import chardet
from bs4 import BeautifulSoup

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class HtmlExtractor(BaseExtractor):
    """HTML提取器，负责从HTML文件中提取内容"""
    
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从HTML文件中提取内容
        
        Args:
            file_path: HTML文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
                
            # 读取文件内容
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                
            # 解析HTML
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                html_content = f.read()
                
            # 使用BeautifulSoup提取文本
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = soup.title.string if soup.title else ""
            
            # 提取正文
            # 移除script和style元素
            for script in soup(["script", "style"]):
                script.extract()
                
            # 获取文本
            text = soup.get_text(separator="\n", strip=True)
            
            # 返回提取的内容
            return [{
                "text": text,
                "metadata": {
                    "source_type": "html",
                    "file_path": file_path,
                    "title": title,
                    "encoding": encoding
                }
            }]
            
        except Exception as e:
            Logger.error(f"Error extracting text from HTML file {file_path}: {str(e)}")
            return []