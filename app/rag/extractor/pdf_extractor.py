"""PDF提取器，负责从PDF文件中提取内容"""
import os
from typing import List, Dict, Any
import fitz  # PyMuPDF

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class PdfExtractor(BaseExtractor):
    """PDF提取器，负责从PDF文件中提取内容"""
    
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从PDF文件中提取内容
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表，每个元素对应一页
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
                
            # 打开PDF文件
            doc = fitz.open(file_path)
            
            # 提取每一页的内容
            results = []
            for page_num, page in enumerate(doc):
                # 提取文本
                text = page.get_text()
                
                # 提取元数据
                metadata = {
                    "source_type": "pdf",
                    "file_path": file_path,
                    "page_number": page_num + 1,
                    "total_pages": len(doc)
                }
                
                # 添加到结果列表
                results.append({
                    "text": text,
                    "metadata": metadata
                })
                
            # 关闭文档
            doc.close()
            
            return results
            
        except Exception as e:
            Logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return []