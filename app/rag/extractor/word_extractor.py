"""Word提取器，负责从Word文件中提取内容"""
import os
from typing import List, Dict, Any
import docx

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class WordExtractor(BaseExtractor):
    """Word提取器，负责从Word文件中提取内容"""
    
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从Word文件中提取内容
        
        Args:
            file_path: Word文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
                
            # 打开Word文件
            doc = docx.Document(file_path)
            
            # 提取文本内容
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():  # 忽略空段落
                    full_text.append(para.text)
                    
            # 提取表格内容
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():  # 忽略空单元格
                            row_text.append(cell.text.strip())
                    if row_text:  # 忽略空行
                        full_text.append(" | ".join(row_text))
                        
            # 合并文本
            content = "\n".join(full_text)
            
            # 返回提取的内容
            return [{
                "text": content,
                "metadata": {
                    "source_type": "word",
                    "file_path": file_path,
                    "paragraphs": len(doc.paragraphs),
                    "tables": len(doc.tables)
                }
            }]
            
        except Exception as e:
            Logger.error(f"Error extracting text from Word document {file_path}: {str(e)}")
            return []