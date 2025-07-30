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
from app.rag.extractor.csv_extractor import CsvExtractor
from app.rag.extractor.pptx_extractor import PptxExtractor

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
            ".csv": CsvExtractor(),
            ".pptx": PptxExtractor(),
        }
        
    async def process_document(self, document: DBDocument) -> List[Document]:
        """处理数据库中的文档
        
        Args:
            document: 数据库中的文档对象
            
        Returns:
            List[Document]: 处理后的文档对象列表
        """
        import time
        start_time = time.time()
        
        # 记录文档处理开始
        Logger.rag_extraction_start(
            document_id=document.id,
            file_path=document.doc_metadata.get("file_path", "database") if document.doc_metadata else "database",
            file_type=document.doc_type or "unknown"
        )
        
        try:
            # 如果是文本类型，直接处理内容
            if document.doc_type == "text":
                Logger.debug(f"处理文本类型文档: ID {document.id}")
                
                result = [Document(
                    page_content=document.content,
                    metadata={
                        "document_id": document.id,
                        "title": document.title,
                        "source": "database"
                    }
                )]
                
                # 记录处理成功
                process_time = time.time() - start_time
                Logger.rag_extraction_success(
                    document_id=document.id,
                    content_length=len(document.content) if document.content else 0,
                    extraction_time=process_time
                )
                
                return result
            
            # 如果有文件路径，处理文件
            if document.doc_metadata and "file_path" in document.doc_metadata:
                file_path = document.doc_metadata["file_path"]
                Logger.debug(f"处理文件类型文档: ID {document.id}, 文件路径: {file_path}")
                
                result = await self.process_file(file_path, document.id, document.title)
                
                # 记录处理成功
                process_time = time.time() - start_time
                total_content_length = sum(len(doc.page_content) for doc in result)
                Logger.rag_extraction_success(
                    document_id=document.id,
                    content_length=total_content_length,
                    extraction_time=process_time
                )
                
                return result
                
            # 如果没有文件路径，返回空列表
            Logger.warning(f"Document {document.id} has no file_path in metadata")
            return []
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            Logger.error(f"Error processing document {document.id}: {str(e)}")
            
            # 记录处理失败的性能指标
            Logger.rag_performance_metrics(
                operation="document_extraction_failed",
                duration=process_time,
                document_id=document.id,
                error=str(e)
            )
            
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
        import time
        start_time = time.time()
        
        # 获取文件信息
        file_extension = Path(file_path).suffix.lower()
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        Logger.debug(f"开始处理文件: {file_path}, 大小: {file_size} bytes, 类型: {file_extension}")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
            
            # 选择合适的提取器
            extractor = self.extractors.get(file_extension)
            if not extractor:
                Logger.warning(f"No extractor found for file extension: {file_extension}, using TextExtractor")
                extractor = TextExtractor()
            else:
                Logger.debug(f"使用提取器: {extractor.__class__.__name__} for {file_extension}")
                
            # 提取文本内容
            extraction_start_time = time.time()
            extracted_contents = await extractor.extract(file_path)
            extraction_time = time.time() - extraction_start_time
            
            Logger.debug(f"文件提取完成: 耗时 {extraction_time:.3f}秒, 提取了 {len(extracted_contents)} 个内容块")
            
            # 转换为Document对象
            documents = []
            total_content_length = 0
            
            for i, content in enumerate(extracted_contents):
                page_content = content["text"]
                total_content_length += len(page_content)
                
                documents.append(Document(
                    page_content=page_content,
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
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录处理成功的性能指标
            Logger.rag_performance_metrics(
                operation="file_extraction",
                duration=total_time,
                document_id=document_id,
                file_size=file_size,
                file_type=file_extension[1:],
                content_length=total_content_length,
                page_count=len(documents),
                extraction_time=extraction_time
            )
            
            Logger.debug(f"文件处理完成: {len(documents)} 个文档对象, 总内容长度: {total_content_length}")
            return documents
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"Error processing file {file_path}: {str(e)}\n堆栈跟踪:\n{error_info}")
            
            # 记录处理失败的性能指标
            Logger.rag_performance_metrics(
                operation="file_extraction_failed",
                duration=total_time,
                document_id=document_id,
                file_size=file_size,
                file_type=file_extension[1:] if file_extension else "unknown",
                error=str(e)
            )
            
            return []
    
    async def extract(self, file_path: str) -> str:
        """提取文件内容（简化接口，用于训练管理器）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 提取的文本内容
        """
        import time
        start_time = time.time()
        
        try:
            # 获取文件信息
            file_extension = Path(file_path).suffix.lower()
            file_size = 0
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            
            Logger.debug(f"提取文件内容: {file_path}, 大小: {file_size} bytes, 类型: {file_extension}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return ""
            
            # 选择合适的提取器
            extractor = self.extractors.get(file_extension)
            if not extractor:
                Logger.warning(f"No extractor found for file extension: {file_extension}, using TextExtractor")
                extractor = TextExtractor()
            else:
                Logger.debug(f"使用提取器: {extractor.__class__.__name__} for {file_extension}")
                
            # 提取文本内容
            extraction_start_time = time.time()
            extracted_contents = await extractor.extract(file_path)
            extraction_time = time.time() - extraction_start_time
            
            # 合并所有内容
            combined_content = ""
            for content in extracted_contents:
                if isinstance(content, dict) and "text" in content:
                    combined_content += content["text"] + "\n"
                elif isinstance(content, str):
                    combined_content += content + "\n"
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            Logger.debug(f"文件内容提取完成: 耗时 {extraction_time:.3f}秒, 内容长度: {len(combined_content)}")
            
            # 记录处理成功的性能指标
            Logger.rag_performance_metrics(
                operation="simple_file_extraction",
                duration=total_time,
                file_size=file_size,
                file_type=file_extension[1:] if file_extension else "unknown",
                content_length=len(combined_content),
                extraction_time=extraction_time
            )
            
            return combined_content.strip()
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"Error extracting file {file_path}: {str(e)}\n堆栈跟踪:\n{error_info}")
            
            # 记录处理失败的性能指标
            Logger.rag_performance_metrics(
                operation="simple_file_extraction_failed",
                duration=total_time,
                file_size=file_size if 'file_size' in locals() else 0,
                file_type=file_extension[1:] if 'file_extension' in locals() and file_extension else "unknown",
                error=str(e)
            )
            
            return ""