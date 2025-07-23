"""标准索引处理器"""
from typing import List, Dict, Any, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logger import Logger
from app.core.config import settings
from app.schemas.llm import LLMConfig
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document as DBDocument
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.rag.models.document import Document
from app.rag.index_processor.index_processor_base import BaseIndexProcessor
from app.rag.extractor.extract_processor import ExtractProcessor
from app.rag.cleaner.clean_processor import TextCleaner
from app.rag.splitter.recursive_character_text_splitter import RecursiveCharacterTextSplitter
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.datasource.vdb.vector_factory import VectorFactory

class StandardIndexProcessor(BaseIndexProcessor):
    """标准索引处理器
    
    使用高质量的向量索引实现
    """
    
    def __init__(self):
        """初始化标准索引处理器"""
        self.extractor = ExtractProcessor()
        self.cleaner = TextCleaner()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP
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
                    
                    # 创建文档对象
                    transformed_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "doc_id": chunk_id,
                            "chunk_index": i,
                            "original_doc_id": doc_id
                        }
                    )
                    transformed_documents.append(transformed_doc)
                    
            return transformed_documents
            
        except Exception as e:
            Logger.error(f"转换文档失败: {str(e)}")
            return documents
            
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
                
            # 获取LLM配置
            llm_config: LLMConfig = kwargs.get("llm_config")
            if not llm_config:
                raise ValueError("缺少LLM配置")
                
            # 创建向量化引擎
            embedding_engine = EmbeddingEngine(llm_config)
            
            # 向量化文档
            vectorized_documents = await embedding_engine.batch_embed_documents(documents)
            
            # 创建向量存储
            vector_store = VectorFactory.create_vector_store(knowledge_base, llm_config)
            
            # 添加到向量存储
            await vector_store.add_texts(
                vectorized_documents,
                [doc.vector for doc in vectorized_documents],
                duplicate_check=True
            )
            
            # 保存到数据库
            for doc in vectorized_documents:
                # 创建文档分块
                chunk = DocumentChunk(
                    document_id=doc.metadata.get("document_id"),
                    content=doc.page_content,
                    chunk_index=doc.metadata.get("chunk_index", 0),
                    metadata=doc.metadata
                )
                db.add(chunk)
                await db.flush()
                
                # 创建文档向量
                embedding = DocumentEmbedding(
                    chunk_id=chunk.id,
                    embedding=doc.vector,
                    model=knowledge_base.embedding_model
                )
                db.add(embedding)
                
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
                
            # 获取LLM配置
            llm_config: LLMConfig = kwargs.get("llm_config")
            if not llm_config:
                raise ValueError("缺少LLM配置")
                
            # 创建向量存储
            vector_store = VectorFactory.create_vector_store(knowledge_base, llm_config)
            
            if document_ids:
                # 删除指定文档
                await vector_store.delete_by_ids(document_ids)
                
                # 从数据库中删除
                chunks = await db.execute(
                    select(DocumentChunk).filter(
                        DocumentChunk.document_id.in_(document_ids)
                    )
                )
                for chunk in chunks.scalars().all():
                    await db.delete(chunk)
            else:
                # 删除整个索引
                await vector_store.delete()
                
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
            # 获取LLM配置
            llm_config: LLMConfig = kwargs.get("llm_config")
            if not llm_config:
                raise ValueError("缺少LLM配置")
                
            # 创建向量化引擎
            embedding_engine = EmbeddingEngine(llm_config)
            
            # 向量化查询
            query_vector = await embedding_engine.embed_query(query)
            
            # 创建向量存储
            vector_store = VectorFactory.create_vector_store(knowledge_base, llm_config)
            
            # 执行检索
            results = await vector_store.search_by_vector(
                query_vector,
                top_k=top_k,
                **kwargs
            )
            
            return results
            
        except Exception as e:
            Logger.error(f"检索文档失败: {str(e)}")
            return []