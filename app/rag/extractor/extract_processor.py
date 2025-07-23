"""文档处理器，负责处理多种格式的文档"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import tempfile

from app.core.logger import Logger
from app.models.document import Document as DBDocument
from app.rag.models.document import Document
from app.rag.extractor.extractor_base import BaseExtractor
from app.rag.extractor.text_extractor import TextExtractor
from app.rag.extractor.pdf_extractor import PdfExtractor
from app.rag.extractor.word_extractor import WordExtractor
from app.rag.extractor.excel_extractor import ExcelExtractor
from app.rag.extractor.markdown_extractor import MarkdownExtractor
from app.rag.extractor.html_extractor import HtmlExtractor

class ExtractProcessor:
    """文档处理器，负责处理多种格式的文档"""
    
    def __init__(self):
        """初始化文档处理器"""
        self.extractors = {
            ".txt": TextExtractor(),
            ".pdf": PdfExtractor(),
            ".docx": WordExtractor(),
            ".doc": WordExtractor(),
            ".xlsx": ExcelExtractor(),
            ".xls": ExcelExtractor(),
            ".md": MarkdownExtractor(),
            ".markdown": MarkdownExtractor(),
            ".html": HtmlExtractor(),
            ".htm": HtmlExtractor(),
        }
        
    async def process_document(self, document: DBDocument) -> List[Document]:
        """处理数据库中的文档
        
        Args:
            document: 数据库中的文档对象
            
        Returns:
            List[Document]: 处理后的文档对象列表
        """
        try:
            # 如果是文本类型，直接处理内容
            if document.doc_type == "text":
                return [Document(
                    page_content=document.content,
                    metadata={
                        "document_id": document.id,
                        "title": document.title,
                        "source": "database"
                    }
                )]
            
            # 如果有文件路径，处理文件
            if document.doc_metadata and "file_path" in document.doc_metadata:
                file_path = document.doc_metadata["file_path"]
                return await self.process_file(file_path, document.id, document.title)
                
            # 如果没有文件路径，返回空列表
            Logger.warning(f"Document {document.id} has no file_path in metadata")
            return []
            
        except Exception as e:
            Logger.error(f"Error processing document {document.id}: {str(e)}")
            return []
            
    async def process_file(self, file_path: str, document_id: int, title: str) -> List[Document]:
        """处理文件
        
        Args:
            file_path: 文件路径
            document_id: 文档ID
            title: 文档标题
            
        Returns:
            List[Document]: 处理后的文档对象列表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
                
            # 获取文件扩展名
            file_extension = Path(file_path).suffix.lower()
            
            # 选择合适的提取器
            extractor = self.extractors.get(file_extension)
            if not extractor:
                Logger.warning(f"No extractor found for file extension: {file_extension}, using TextExtractor")
                extractor = TextExtractor()
                
            # 提取文本内容
            extracted_contents = await extractor.extract(file_path)
            
            # 转换为Document对象
            documents = []
            for i, content in enumerate(extracted_contents):
                documents.append(Document(
                    page_content=content["text"],
                    metadata={
                        "document_id": document_id,
                        "title": title,
                        "page": i + 1,
                        "source": "file",
                        "file_path": file_path,
                        "file_type": file_extension[1:],  # 去掉点号
                        **content.get("metadata", {})
                    }
                ))
                
            return documents
            
        except Exception as e:
            Logger.error(f"Error processing file {file_path}: {str(e)}")
            return []