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
        import time
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"PDF文件不存在: {file_path}")
                return []
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            Logger.debug(f"开始提取PDF文件: {file_path}, 大小: {file_size} bytes")
                
            # 打开PDF文件
            open_start_time = time.time()
            doc = fitz.open(file_path)
            open_time = time.time() - open_start_time
            
            total_pages = len(doc)
            Logger.debug(f"PDF文件打开成功: 总页数 {total_pages}, 打开耗时: {open_time:.3f}秒")
            
            # 提取每一页的内容
            results = []
            total_text_length = 0
            
            for page_num, page in enumerate(doc):
                page_start_time = time.time()
                
                # 提取文本
                text = page.get_text()
                page_text_length = len(text)
                total_text_length += page_text_length
                
                page_time = time.time() - page_start_time
                
                # 记录页面处理进度
                if page_num % 10 == 0 or page_num == total_pages - 1:  # 每10页或最后一页记录一次
                    Logger.debug(f"PDF页面提取进度: {page_num + 1}/{total_pages}, 当前页文本长度: {page_text_length}")
                
                # 提取元数据
                metadata = {
                    "source_type": "pdf",
                    "file_path": file_path,
                    "page_number": page_num + 1,
                    "total_pages": total_pages,
                    "page_text_length": page_text_length,
                    "page_extraction_time": page_time
                }
                
                # 添加到结果列表
                results.append({
                    "text": text,
                    "metadata": metadata
                })
                
            # 关闭文档
            doc.close()
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录提取成功的详细信息
            Logger.debug(f"PDF提取完成: {file_path}")
            Logger.debug(f"  - 总页数: {total_pages}")
            Logger.debug(f"  - 总文本长度: {total_text_length}")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            Logger.debug(f"  - 平均每页耗时: {total_time/total_pages:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="pdf_extraction",
                duration=total_time,
                file_size=file_size,
                file_type="pdf",
                page_count=total_pages,
                content_length=total_text_length,
                avg_page_time=total_time/total_pages if total_pages > 0 else 0
            )
            
            return results
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"PDF提取失败: {file_path}")
            Logger.error(f"错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="pdf_extraction_failed",
                duration=total_time,
                file_size=file_size if 'file_size' in locals() else 0,
                file_type="pdf",
                error=str(e)
            )
            
            return []