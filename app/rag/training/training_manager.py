"""RAG训练管理器"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from app.core.logger import Logger
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.models.enums import TrainingStatus
from app.rag.extractor.extract_processor import ExtractProcessor
from app.rag.splitter.text_splitter import TextSplitter
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.datasource.vdb.vector_factory import VectorStoreFactory
from app.rag.index_processor.index_processor_factory import IndexProcessorFactory
from app.rag.exceptions import (
    DocumentProcessingException,
    EmbeddingException,
    IndexingException,
    TrainingException
)
from app.schemas.llm import LLMConfig


class TrainingResult:
    """训练结果"""
    
    def __init__(
        self,
        success: bool = True,
        document_count: int = 0,
        chunk_count: int = 0,
        embedding_count: int = 0,
        error_message: Optional[str] = None
    ):
        """初始化训练结果
        
        Args:
            success: 是否成功
            document_count: 处理的文档数量
            chunk_count: 生成的分块数量
            embedding_count: 生成的向量数量
            error_message: 错误信息
        """
        self.success = success
        self.document_count = document_count
        self.chunk_count = chunk_count
        self.embedding_count = embedding_count
        self.error_message = error_message


class RAGTrainingManager:
    """RAG训练管理器
    
    负责管理知识库的训练流程
    """
    
    def __init__(self, db: Session):
        """初始化训练管理器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.extract_processor = ExtractProcessor()
        
    async def train(self, kb_id: int) -> TrainingResult:
        """训练知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            TrainingResult: 训练结果
        """
        try:
            # 获取知识库
            knowledge_base = (await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )).scalar_one_or_none()
            
            if not knowledge_base:
                return TrainingResult(
                    success=False,
                    error_message=f"知识库 {kb_id} 不存在"
                )
                
            # 更新知识库状态为训练中
            await self.update_training_status(kb_id, TrainingStatus.TRAINING)
            
            # 获取知识库文档
            documents = (await self.db.execute(
                select(Document).filter(Document.knowledge_base_id == kb_id)
            )).scalars().all()
            
            if not documents:
                return TrainingResult(
                    success=False,
                    error_message=f"知识库 {kb_id} 没有文档"
                )
                
            # 创建LLM配置
            llm_config = LLMConfig.model_validate(knowledge_base.llm_config)
            
            # 处理文档
            result = await self._process_documents(knowledge_base, documents, llm_config)
            
            # 更新知识库状态为已训练
            if result.success:
                await self.update_training_status(kb_id, TrainingStatus.TRAINED)
            else:
                await self.update_training_status(kb_id, TrainingStatus.FAILED, result.error_message)
                
            return result
            
        except Exception as e:
            Logger.error(f"训练知识库 {kb_id} 失败: {str(e)}")
            # 更新知识库状态为训练失败
            await self.update_training_status(kb_id, TrainingStatus.FAILED, str(e))
            return TrainingResult(
                success=False,
                error_message=f"训练失败: {str(e)}"
            )
            
    async def _process_documents(
        self,
        knowledge_base: KnowledgeBase,
        documents: List[Document],
        llm_config: LLMConfig
    ) -> TrainingResult:
        """处理文档
        
        Args:
            knowledge_base: 知识库对象
            documents: 文档列表
            llm_config: LLM配置
            
        Returns:
            TrainingResult: 处理结果
        """
        document_count = 0
        chunk_count = 0
        embedding_count = 0
        failed_documents = []
        
        try:
            # 从配置中获取分块参数
            from app.core.config import settings
            chunk_size = getattr(settings, 'RAG_CHUNK_SIZE', 1000)
            chunk_overlap = getattr(settings, 'RAG_CHUNK_OVERLAP', 200)
            
            # 创建文本分块器
            text_splitter = TextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 创建向量引擎
            embedding_engine = EmbeddingEngine(llm_config)
            
            # 创建向量存储
            vector_store_type = knowledge_base.vector_store_type or getattr(settings, 'RAG_VECTOR_STORE_TYPE', "chroma")
            vector_store = VectorStoreFactory.create_vector_store(
                vector_store_type=vector_store_type,
                collection_name=f"kb_{knowledge_base.id}",
                embedding_engine=embedding_engine
            )
            
            # 创建索引处理器
            index_processor = IndexProcessorFactory.create_index_processor(knowledge_base)
            
            # 处理每个文档
            for document in documents:
                try:
                    Logger.info(f"开始处理文档 {document.id}: {document.title}")
                    
                    # 提取文档内容
                    try:
                        extracted_content = await self.extract_processor.extract(document.file_path)
                        
                        if not extracted_content:
                            raise DocumentProcessingException(
                                message=f"文档 {document.id} 提取内容为空",
                                document_id=document.id,
                                file_path=document.file_path
                            )
                    except Exception as e:
                        raise DocumentProcessingException(
                            message=f"提取文档内容失败: {str(e)}",
                            document_id=document.id,
                            file_path=document.file_path
                        )
                        
                    # 分块文本
                    try:
                        chunks = text_splitter.split_text(extracted_content)
                        
                        if not chunks:
                            raise DocumentProcessingException(
                                message=f"文档 {document.id} 分块为空",
                                document_id=document.id,
                                file_path=document.file_path
                            )
                    except Exception as e:
                        if not isinstance(e, DocumentProcessingException):
                            raise DocumentProcessingException(
                                message=f"分块文本失败: {str(e)}",
                                document_id=document.id,
                                file_path=document.file_path
                            )
                        raise
                        
                    # 删除现有分块
                    try:
                        await self.db.execute(
                            f"DELETE FROM document_chunks WHERE document_id = {document.id}"
                        )
                    except Exception as e:
                        raise IndexingException(
                            message=f"删除现有分块失败: {str(e)}",
                            knowledge_base_id=knowledge_base.id
                        )
                    
                    # 创建新分块
                    db_chunks = []
                    try:
                        for i, chunk_text in enumerate(chunks):
                            chunk = DocumentChunk(
                                document_id=document.id,
                                content=chunk_text,
                                chunk_index=i,
                                metadata={}
                            )
                            self.db.add(chunk)
                            chunk_count += 1
                            
                        # 提交分块
                        await self.db.commit()
                        
                        # 获取新创建的分块
                        db_chunks = (await self.db.execute(
                            select(DocumentChunk).filter(DocumentChunk.document_id == document.id)
                        )).scalars().all()
                    except Exception as e:
                        await self.db.rollback()
                        raise IndexingException(
                            message=f"创建分块失败: {str(e)}",
                            knowledge_base_id=knowledge_base.id
                        )
                    
                    # 向量化分块
                    try:
                        chunk_texts = [chunk.content for chunk in db_chunks]
                        embeddings = await embedding_engine.embed_documents(chunk_texts)
                        
                        if len(embeddings) != len(chunk_texts):
                            raise EmbeddingException(
                                message=f"向量化结果数量 ({len(embeddings)}) 与分块数量 ({len(chunk_texts)}) 不一致",
                                model_name=llm_config.embeddings.model_name
                            )
                    except Exception as e:
                        if not isinstance(e, EmbeddingException):
                            raise EmbeddingException(
                                message=f"向量化分块失败: {str(e)}",
                                model_name=llm_config.embeddings.model_name
                            )
                        raise
                    
                    # 存储向量
                    try:
                        for chunk, embedding in zip(db_chunks, embeddings):
                            # 创建向量记录
                            doc_embedding = DocumentEmbedding(
                                chunk_id=chunk.id,
                                embedding=embedding,
                                model=llm_config.embeddings.model_name
                            )
                            self.db.add(doc_embedding)
                            embedding_count += 1
                            
                        # 提交向量
                        await self.db.commit()
                    except Exception as e:
                        await self.db.rollback()
                        raise IndexingException(
                            message=f"存储向量失败: {str(e)}",
                            knowledge_base_id=knowledge_base.id
                        )
                    
                    # 构建索引
                    try:
                        await index_processor.build_index(knowledge_base, document, db_chunks, embeddings)
                    except Exception as e:
                        raise IndexingException(
                            message=f"构建索引失败: {str(e)}",
                            knowledge_base_id=knowledge_base.id,
                            index_type=getattr(index_processor, "index_type", None)
                        )
                    
                    document_count += 1
                    Logger.info(f"文档 {document.id} 处理完成，生成了 {len(db_chunks)} 个分块和 {len(embeddings)} 个向量")
                    
                except (DocumentProcessingException, EmbeddingException, IndexingException) as e:
                    Logger.error(f"处理文档 {document.id} 失败: {e.message}")
                    failed_documents.append({
                        "document_id": document.id,
                        "title": document.title,
                        "error": e.message,
                        "details": e.details
                    })
                    # 回滚事务
                    await self.db.rollback()
                    # 继续处理其他文档
                    continue
                except Exception as e:
                    Logger.error(f"处理文档 {document.id} 时发生未知错误: {str(e)}")
                    failed_documents.append({
                        "document_id": document.id,
                        "title": document.title,
                        "error": str(e)
                    })
                    # 回滚事务
                    await self.db.rollback()
                    # 继续处理其他文档
                    continue
                    
            # 返回处理结果
            if document_count > 0:
                return TrainingResult(
                    success=True,
                    document_count=document_count,
                    chunk_count=chunk_count,
                    embedding_count=embedding_count,
                    error_message=f"{len(failed_documents)} 个文档处理失败" if failed_documents else None
                )
            else:
                return TrainingResult(
                    success=False,
                    document_count=0,
                    chunk_count=0,
                    embedding_count=0,
                    error_message=f"所有文档处理失败: {failed_documents[0]['error'] if failed_documents else '未知错误'}"
                )
            
        except Exception as e:
            Logger.error(f"处理文档失败: {str(e)}")
            return TrainingResult(
                success=False,
                document_count=document_count,
                chunk_count=chunk_count,
                embedding_count=embedding_count,
                error_message=f"处理文档失败: {str(e)}"
            )
            
    async def update_training_status(
        self,
        kb_id: int,
        status: TrainingStatus,
        error_message: Optional[str] = None
    ) -> None:
        """更新训练状态
        
        Args:
            kb_id: 知识库ID
            status: 训练状态
            error_message: 错误信息
        """
        try:
            # 获取知识库
            knowledge_base = (await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )).scalar_one_or_none()
            
            if not knowledge_base:
                Logger.error(f"更新训练状态失败: 知识库 {kb_id} 不存在")
                return
                
            # 更新状态
            knowledge_base.training_status = status
            
            # 更新时间
            if status == TrainingStatus.TRAINING:
                knowledge_base.training_started_at = datetime.now()
            elif status == TrainingStatus.TRAINED or status == TrainingStatus.FAILED:
                knowledge_base.training_finished_at = datetime.now()
                
            # 更新错误信息
            if error_message and status == TrainingStatus.FAILED:
                knowledge_base.training_error = error_message
                
            # 提交更新
            await self.db.commit()
            
        except Exception as e:
            Logger.error(f"更新训练状态失败: {str(e)}")
            await self.db.rollback()
            
    async def add_to_queue(self, kb_id: int) -> bool:
        """将知识库添加到训练队列
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            bool: 是否成功添加到队列
        """
        try:
            # 获取知识库
            knowledge_base = (await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )).scalar_one_or_none()
            
            if not knowledge_base:
                Logger.error(f"将知识库添加到队列失败: 知识库 {kb_id} 不存在")
                return False
                
            # 更新状态为排队中
            knowledge_base.training_status = TrainingStatus.QUEUED
            knowledge_base.training_error = None
            await self.db.commit()
            
            Logger.info(f"知识库 {kb_id} 已添加到训练队列")
            return True
            
        except Exception as e:
            Logger.error(f"将知识库添加到队列失败: {str(e)}")
            await self.db.rollback()
            return False
    
    async def check_queue(self) -> Optional[int]:
        """检查训练队列
        
        Returns:
            Optional[int]: 下一个要训练的知识库ID，如果没有则返回None
        """
        try:
            # 检查是否有正在训练的知识库
            training_kb = (await self.db.execute(
                select(KnowledgeBase)
                .filter(KnowledgeBase.training_status == TrainingStatus.TRAINING)
            )).scalar_one_or_none()
            
            if training_kb:
                Logger.info(f"知识库 {training_kb.id} 正在训练中，不处理队列")
                return None
            
            # 查找状态为QUEUED的知识库
            queued_kb = (await self.db.execute(
                select(KnowledgeBase)
                .filter(KnowledgeBase.training_status == TrainingStatus.QUEUED)
                .order_by(desc(KnowledgeBase.updated_at))
                .limit(1)
            )).scalar_one_or_none()
            
            if queued_kb:
                return queued_kb.id
                
            return None
            
        except Exception as e:
            Logger.error(f"检查训练队列失败: {str(e)}")
            return None
            
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取训练队列状态
        
        Returns:
            Dict[str, Any]: 队列状态信息
        """
        try:
            # 获取正在训练的知识库
            training_kb = (await self.db.execute(
                select(KnowledgeBase)
                .filter(KnowledgeBase.training_status == TrainingStatus.TRAINING)
            )).scalar_one_or_none()
            
            # 获取排队中的知识库
            queued_kbs = (await self.db.execute(
                select(KnowledgeBase)
                .filter(KnowledgeBase.training_status == TrainingStatus.QUEUED)
                .order_by(desc(KnowledgeBase.updated_at))
            )).scalars().all()
            
            # 构建队列状态信息
            queue_status = {
                "training": None,
                "queue": [],
                "queue_length": len(queued_kbs)
            }
            
            if training_kb:
                queue_status["training"] = {
                    "id": training_kb.id,
                    "name": training_kb.name,
                    "started_at": training_kb.training_started_at
                }
                
            for kb in queued_kbs:
                queue_status["queue"].append({
                    "id": kb.id,
                    "name": kb.name,
                    "queued_at": kb.updated_at
                })
                
            return queue_status
            
        except Exception as e:
            Logger.error(f"获取训练队列状态失败: {str(e)}")
            return {
                "training": None,
                "queue": [],
                "queue_length": 0,
                "error": str(e)
            }