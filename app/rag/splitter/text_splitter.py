"""文本分块器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional
import time

from app.core.logger import Logger
from app.rag.models.document import Document

class TextSplitter(ABC):
    """文本分块器基类
    
    所有具体的文本分块器都应该继承这个基类
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
    ):
        """初始化文本分块器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            length_function: 计算文本长度的函数
        """
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"分块重叠大小 ({chunk_overlap}) 大于分块大小 ({chunk_size})，应该更小。"
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """将文本分割为多个块
        
        Args:
            text: 要分割的文本
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        raise NotImplementedError
        
    def create_documents(
        self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Document]:
        """从文本列表创建文档对象
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表，与texts一一对应
            
        Returns:
            List[Document]: 文档对象列表
        """
        start_time = time.time()
        
        # 记录文档创建开始
        total_text_length = sum(len(text) for text in texts)
        Logger.debug(f"开始创建文档对象: {len(texts)} 个文本, 总长度 {total_text_length}")
        
        try:
            _metadatas = metadatas or [{}] * len(texts)
            documents = []
            total_chunks = 0
            
            for i, text in enumerate(texts):
                text_start_time = time.time()
                chunks = self.split_text(text)
                text_process_time = time.time() - text_start_time
                
                Logger.debug(f"文本 {i+1}/{len(texts)} 分块完成: {len(chunks)} 个分块, 耗时 {text_process_time:.3f}秒")
                
                for chunk_idx, chunk in enumerate(chunks):
                    metadata = _metadatas[i].copy()
                    # 添加分块相关的元数据
                    metadata.update({
                        'chunk_index': chunk_idx,
                        'chunk_length': len(chunk),
                        'source_text_index': i,
                        'source_text_length': len(text)
                    })
                    doc = Document(page_content=chunk, metadata=metadata)
                    documents.append(doc)
                    
                total_chunks += len(chunks)
                
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 统计信息
            doc_lengths = [len(doc.page_content) for doc in documents]
            avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
            
            # 记录文档创建成功
            Logger.debug(f"文档对象创建完成:")
            Logger.debug(f"  - 输入文本数: {len(texts)}")
            Logger.debug(f"  - 输出文档数: {len(documents)}")
            Logger.debug(f"  - 总分块数: {total_chunks}")
            Logger.debug(f"  - 平均文档长度: {avg_doc_length:.1f}")
            Logger.debug(f"  - 处理耗时: {process_time:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="create_documents",
                duration=process_time,
                input_text_count=len(texts),
                total_text_length=total_text_length,
                output_document_count=len(documents),
                total_chunk_count=total_chunks,
                avg_document_length=avg_doc_length,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                processing_speed=total_text_length / process_time if process_time > 0 else 0.0
            )
                
            return documents
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"文档对象创建失败:")
            Logger.error(f"  - 输入文本数: {len(texts)}")
            Logger.error(f"  - 总文本长度: {total_text_length}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="create_documents_failed",
                duration=process_time,
                input_text_count=len(texts),
                total_text_length=total_text_length,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """分割文档对象
        
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档对象列表
        """
        start_time = time.time()
        
        # 记录文档分割开始
        total_content_length = sum(len(doc.page_content) for doc in documents)
        Logger.debug(f"开始分割文档对象: {len(documents)} 个文档, 总内容长度 {total_content_length}")
        
        try:
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # 为每个元数据添加原始文档信息
            enhanced_metadatas = []
            for i, metadata in enumerate(metadatas):
                enhanced_metadata = metadata.copy()
                enhanced_metadata.update({
                    'original_document_index': i,
                    'original_document_length': len(texts[i])
                })
                enhanced_metadatas.append(enhanced_metadata)
            
            result = self.create_documents(texts, enhanced_metadatas)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录文档分割成功
            Logger.debug(f"文档对象分割完成:")
            Logger.debug(f"  - 输入文档数: {len(documents)}")
            Logger.debug(f"  - 输出文档数: {len(result)}")
            Logger.debug(f"  - 分割比例: {len(result)/len(documents):.2f}")
            Logger.debug(f"  - 处理耗时: {process_time:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="split_documents",
                duration=process_time,
                input_document_count=len(documents),
                output_document_count=len(result),
                total_content_length=total_content_length,
                split_ratio=len(result)/len(documents) if documents else 0.0,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                processing_speed=total_content_length / process_time if process_time > 0 else 0.0
            )
            
            return result
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"文档对象分割失败:")
            Logger.error(f"  - 输入文档数: {len(documents)}")
            Logger.error(f"  - 总内容长度: {total_content_length}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="split_documents_failed",
                duration=process_time,
                input_document_count=len(documents),
                total_content_length=total_content_length,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise