"""关键词索引处理器"""
from typing import List, Dict, Any, Optional
import uuid
import jieba
import re
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logger import Logger
from app.core.config import settings
from app.schemas.llm import LLMConfig
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document as DBDocument
from app.models.document_chunk import DocumentChunk
from app.rag.models.document import Document
from app.rag.index_processor.index_processor_base import BaseIndexProcessor
from app.rag.extractor.extract_processor import ExtractProcessor
from app.rag.cleaner.clean_processor import TextCleaner
from app.rag.splitter.fixed_text_splitter import FixedTextSplitter

class KeywordIndexProcessor(BaseIndexProcessor):
    """关键词索引处理器
    
    使用经济型的关键词索引实现
    """
    
    def __init__(self):
        """初始化关键词索引处理器"""
        self.extractor = ExtractProcessor()
        self.cleaner = TextCleaner()
        self.splitter = FixedTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP
        )
        
        # 记录关键词索引处理器初始化
        Logger.debug(f"初始化关键词索引处理器:")
        Logger.debug(f"  - 分块大小: {settings.RAG_CHUNK_SIZE}")
        Logger.debug(f"  - 分块重叠: {settings.RAG_CHUNK_OVERLAP}")
        Logger.debug(f"  - 索引类型: 关键词索引（经济型）")
        
        # 记录初始化性能指标
        Logger.rag_performance_metrics(
            operation="keyword_index_processor_init",
            duration=0.0,
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            index_type="keyword"
        )
        
    async def extract(self, document: DBDocument) -> List[Document]:
        """从文档中提取内容
        
        Args:
            document: 数据库文档对象
            
        Returns:
            List[Document]: 提取的文档对象列表
        """
        try:
            # 提取文档内容
            extracted_documents = await self.extractor.process_document(document)
            
            # 如果没有提取到内容，返回空列表
            if not extracted_documents:
                return []
                
            # 为每个文档添加知识库ID
            for doc in extracted_documents:
                doc.metadata["knowledge_base_id"] = document.knowledge_base_id
                
            return extracted_documents
            
        except Exception as e:
            Logger.error(f"提取文档内容失败: {str(e)}")
            return []
            
    async def transform(self, documents: List[Document], **kwargs) -> List[Document]:
        """转换文档
        
        Args:
            documents: 文档对象列表
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 转换后的文档对象列表
        """
        try:
            transformed_documents = []
            
            for doc in documents:
                # 清理文本内容
                cleaned_content = self.cleaner.clean(doc.page_content)
                
                # 分割文本
                chunks = self.splitter.split_text(cleaned_content)
                
                # 创建文档对象
                for i, chunk in enumerate(chunks):
                    # 生成唯一ID
                    doc_id = doc.metadata.get("doc_id") or str(uuid.uuid4())
                    chunk_id = f"{doc_id}_{i}"
                    
                    # 提取关键词
                    keywords = self._extract_keywords(chunk)
                    
                    # 创建文档对象
                    transformed_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "doc_id": chunk_id,
                            "chunk_index": i,
                            "original_doc_id": doc_id,
                            "keywords": keywords
                        }
                    )
                    transformed_documents.append(transformed_doc)
                    
            return transformed_documents
            
        except Exception as e:
            Logger.error(f"转换文档失败: {str(e)}")
            return documents
            
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 关键词列表
        """
        start_time = time.time()
        
        try:
            # 使用jieba分词
            segmentation_start = time.time()
            words = list(jieba.cut_for_search(text))
            segmentation_time = time.time() - segmentation_start
            
            # 过滤停用词和标点符号
            filter_start = time.time()
            filtered_words = []
            for word in words:
                # 过滤单个字符和标点符号
                if len(word) > 1 and not re.match(r'[^\w\s]', word):
                    filtered_words.append(word)
            filter_time = time.time() - filter_start
            
            # 去重
            unique_keywords = list(set(filtered_words))
            
            # 计算处理时间
            total_time = time.time() - start_time
            
            # 记录关键词提取统计
            Logger.debug(f"关键词提取完成:")
            Logger.debug(f"  - 文本长度: {len(text)}")
            Logger.debug(f"  - 原始词数: {len(words)}")
            Logger.debug(f"  - 过滤后词数: {len(filtered_words)}")
            Logger.debug(f"  - 唯一关键词数: {len(unique_keywords)}")
            Logger.debug(f"  - 分词耗时: {segmentation_time:.3f}秒")
            Logger.debug(f"  - 过滤耗时: {filter_time:.3f}秒")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="keyword_extraction",
                duration=total_time,
                text_length=len(text),
                original_word_count=len(words),
                filtered_word_count=len(filtered_words),
                unique_keyword_count=len(unique_keywords),
                segmentation_time=segmentation_time,
                filter_time=filter_time,
                processing_speed=len(text) / total_time if total_time > 0 else 0
            )
                    
            return unique_keywords
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"提取关键词失败:")
            Logger.error(f"  - 文本长度: {len(text)}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="keyword_extraction_failed",
                duration=total_time,
                text_length=len(text),
                error=str(e),
                error_type=type(e).__name__
            )
            
            return []
            
    async def load(self, knowledge_base: KnowledgeBase, documents: List[Document], **kwargs) -> None:
        """加载文档到索引
        
        Args:
            knowledge_base: 知识库对象
            documents: 文档对象列表
            **kwargs: 其他参数
        """
        try:
            # 获取数据库会话
            db: Session = kwargs.get("db")
            if not db:
                raise ValueError("缺少数据库会话")
                
            # 保存到数据库
            for doc in documents:
                # 创建文档分块
                chunk = DocumentChunk(
                    document_id=doc.metadata.get("document_id"),
                    content=doc.page_content,
                    chunk_index=doc.metadata.get("chunk_index", 0),
                    metadata=doc.metadata
                )
                db.add(chunk)
                
            # 提交事务
            await db.commit()
            
        except Exception as e:
            Logger.error(f"加载文档到索引失败: {str(e)}")
            raise
            
    async def clean(self, knowledge_base: KnowledgeBase, document_ids: Optional[List[str]] = None, **kwargs) -> None:
        """清理索引
        
        Args:
            knowledge_base: 知识库对象
            document_ids: 文档ID列表，如果为None则清理整个索引
            **kwargs: 其他参数
        """
        try:
            # 获取数据库会话
            db: Session = kwargs.get("db")
            if not db:
                raise ValueError("缺少数据库会话")
                
            if document_ids:
                # 从数据库中删除
                chunks = await db.execute(
                    select(DocumentChunk).filter(
                        DocumentChunk.document_id.in_(document_ids)
                    )
                )
                for chunk in chunks.scalars().all():
                    await db.delete(chunk)
            else:
                # 从数据库中删除
                chunks = await db.execute(
                    select(DocumentChunk).join(
                        DBDocument,
                        DocumentChunk.document_id == DBDocument.id
                    ).filter(
                        DBDocument.knowledge_base_id == knowledge_base.id
                    )
                )
                for chunk in chunks.scalars().all():
                    await db.delete(chunk)
                    
            # 提交事务
            await db.commit()
            
        except Exception as e:
            Logger.error(f"清理索引失败: {str(e)}")
            raise
            
    async def retrieve(
        self,
        knowledge_base: KnowledgeBase,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """检索文档
        
        Args:
            knowledge_base: 知识库对象
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[Document]: 检索结果
        """
        try:
            # 获取数据库会话
            db: Session = kwargs.get("db")
            if not db:
                raise ValueError("缺少数据库会话")
                
            # 提取查询关键词
            keywords = self._extract_keywords(query)
            
            if not keywords:
                return []
                
            # 构建查询条件
            conditions = []
            for keyword in keywords:
                conditions.append(f"content LIKE '%{keyword}%'")
                
            # 执行查询
            query_str = f"""
                SELECT id, document_id, content, chunk_index, metadata
                FROM document_chunks
                WHERE document_id IN (
                    SELECT id FROM documents
                    WHERE knowledge_base_id = {knowledge_base.id}
                    AND is_deleted = FALSE
                )
                AND ({" OR ".join(conditions)})
                LIMIT {top_k}
            """
            
            result = await db.execute(query_str)
            rows = result.fetchall()
            
            # 处理结果
            documents = []
            for row in rows:
                doc = Document(
                    page_content=row.content,
                    metadata={
                        **row.metadata,
                        "document_id": row.document_id,
                        "chunk_id": row.id,
                        "chunk_index": row.chunk_index,
                        "score": self._calculate_score(row.content, keywords)
                    }
                )
                documents.append(doc)
                
            # 按相关性排序
            documents.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
            
            return documents[:top_k]
            
        except Exception as e:
            Logger.error(f"检索文档失败: {str(e)}")
            return []
            
    def _calculate_score(self, text: str, keywords: List[str]) -> float:
        """计算相关性分数
        
        Args:
            text: 文本内容
            keywords: 关键词列表
            
        Returns:
            float: 相关性分数
        """
        try:
            score = 0.0
            for keyword in keywords:
                count = text.count(keyword)
                score += count * (len(keyword) / 10)  # 长关键词权重更高
                
            return min(score, 1.0)  # 归一化到0-1之间
            
        except Exception as e:
            Logger.error(f"计算相关性分数失败: {str(e)}")
            return 0.0