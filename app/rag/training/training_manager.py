"""RAG训练管理器

负责管理RAG知识库的训练流程，包括文档处理、向量化、索引构建等
"""
import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.knowledge_base import KnowledgeBase, TrainingStatus
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.core.logger import Logger
from app.core.config import settings
from app.core.redis_manager import redis_manager
from app.schemas.llm import LLMConfig
from app.rag.training.training_status import TrainingResult, TrainingError
from app.rag.extractor.extract_processor import DocumentProcessor
from app.rag.splitter.text_splitter import TextSplitter
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.index_processor.index_builder import IndexBuilder


class RAGTrainingManager:
    """RAG训练管理器"""
    
    def __init__(self, db: Session):
        """
        初始化
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
    async def train(self, kb_id: int) -> TrainingResult:
        """
        训练知识库
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            TrainingResult: 训练结果
        """
        Logger.info(f"开始训练知识库 {kb_id}")
        start_time = time.time()
        result = TrainingResult()
        
        try:
            # 获取知识库
            kb = (await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )).scalar_one_or_none()
            
            if not kb:
                Logger.error(f"训练失败: 知识库 {kb_id} 不存在")
                result.error_type = TrainingError.UNKNOWN
                result.error_message = f"知识库 {kb_id} 不存在"
                return result
            
            # 获取知识库的所有未删除文档
            documents = (await self.db.execute(
                select(Document).filter(
                    Document.knowledge_base_id == kb_id,
                    Document.is_deleted == False
                )
            )).scalars().all()
            
            if not documents:
                Logger.error(f"训练失败: 知识库 {kb_id} 没有可用文档")
                result.error_type = TrainingError.NO_DOCUMENTS
                result.error_message = "没有可用于训练的文档"
                return result
            
            result.document_count = len(documents)
            Logger.info(f"找到 {len(documents)} 个文档用于训练知识库 {kb_id}")
            
            # 更新知识库状态
            kb.training_status = TrainingStatus.TRAINING
            kb.training_started_at = datetime.now()
            kb.training_error = None
            await self.db.commit()
            await self.db.refresh(kb)
            
            # 创建工作目录
            if not kb.working_dir:
                kb.working_dir = f"workspaces/kb_{kb.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await self.db.commit()
                await self.db.refresh(kb)
            
            work_dir = Path(kb.working_dir)
            os.makedirs(work_dir, exist_ok=True)
            
            # 解析LLM配置
            llm_config = LLMConfig.model_validate(kb.llm_config)
            
            # 处理文档
            chunk_results = await self._process_documents(kb, documents, llm_config)
            result.chunk_count = chunk_results[0]
            result.embedding_count = chunk_results[1]
            
            # 构建索引
            await self._build_index(kb, llm_config)
            
            # 更新训练状态
            kb.training_status = TrainingStatus.TRAINED
            kb.training_finished_at = datetime.now()
            kb.training_error = None
            await self.db.commit()
            
            # 设置结果
            result.success = True
            result.processing_time = time.time() - start_time
            result.metadata = {
                "kb_id": kb.id,
                "kb_name": kb.name,
                "training_time": (kb.training_finished_at - kb.training_started_at).total_seconds() if kb.training_finished_at and kb.training_started_at else 0
            }
            
            Logger.info(f"知识库 {kb_id} 训练完成，耗时 {result.processing_time:.2f} 秒")
            return result
            
        except Exception as e:
            Logger.error(f"训练知识库 {kb_id} 时发生错误: {str(e)}")
            
            # 更新知识库状态
            try:
                kb = (await self.db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )).scalar_one_or_none()
                
                if kb:
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = str(e)
                    await self.db.commit()
            except Exception as db_error:
                Logger.error(f"更新知识库状态时发生错误: {str(db_error)}")
            
            # 设置结果
            result.success = False
            result.error_type = TrainingError.UNKNOWN
            result.error_message = str(e)
            result.processing_time = time.time() - start_time
            
            return result
    
    async def _process_documents(
        self, 
        kb: KnowledgeBase, 
        documents: List[Document],
        llm_config: LLMConfig
    ) -> Tuple[int, int]:
        """
        处理文档，包括文档提取、分块和向量化
        
        Args:
            kb: 知识库
            documents: 文档列表
            llm_config: LLM配置
            
        Returns:
            Tuple[int, int]: (分块数量, 向量数量)
        """
        Logger.info(f"开始处理知识库 {kb.id} 的 {len(documents)} 个文档")
        
        # 创建文档处理器
        doc_processor = DocumentProcessor()
        
        # 创建文本分块器
        text_splitter = TextSplitter()
        
        # 创建向量引擎
        embedding_engine = EmbeddingEngine(llm_config)
        
        total_chunks = 0
        total_embeddings = 0
        
        # 处理每个文档
        for doc in documents:
            try:
                Logger.info(f"处理文档: {doc.title} (ID: {doc.id})")
                
                # 提取文本
                text_content = doc.content
                
                # 分块
                chunks = text_splitter.split_text(text_content)
                Logger.info(f"文档 {doc.id} 分成了 {len(chunks)} 个块")
                
                # 存储分块
                for i, chunk_text in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        content=chunk_text,
                        chunk_index=i,
                        metadata={
                            "title": doc.title,
                            "doc_id": doc.id,
                            "chunk_index": i
                        }
                    )
                    self.db.add(chunk)
                
                await self.db.commit()
                
                # 获取刚刚创建的分块
                db_chunks = (await self.db.execute(
                    select(DocumentChunk).filter(DocumentChunk.document_id == doc.id)
                )).scalars().all()
                
                # 向量化
                for chunk in db_chunks:
                    # 计算向量
                    embeddings = await embedding_engine.get_embeddings([chunk.content])
                    if embeddings and len(embeddings) > 0:
                        # 存储向量
                        embedding = DocumentEmbedding(
                            chunk_id=chunk.id,
                            embedding=embeddings[0],
                            model=f"{llm_config.embeddings.provider}/{llm_config.embeddings.model}"
                        )
                        self.db.add(embedding)
                        total_embeddings += 1
                
                await self.db.commit()
                total_chunks += len(db_chunks)
                
            except Exception as e:
                Logger.error(f"处理文档 {doc.id} 时发生错误: {str(e)}")
                await self.db.rollback()
                raise
        
        return total_chunks, total_embeddings
    
    async def _build_index(self, kb: KnowledgeBase, llm_config: LLMConfig) -> None:
        """
        构建索引
        
        Args:
            kb: 知识库
            llm_config: LLM配置
        """
        Logger.info(f"开始为知识库 {kb.id} 构建索引")
        
        # 创建索引构建器
        index_builder = IndexBuilder(llm_config)
        
        # 获取所有分块和向量
        chunks_with_embeddings = (await self.db.execute(
            select(DocumentChunk, DocumentEmbedding).join(
                DocumentEmbedding, 
                DocumentChunk.id == DocumentEmbedding.chunk_id
            ).join(
                Document,
                DocumentChunk.document_id == Document.id
            ).filter(
                Document.knowledge_base_id == kb.id,
                Document.is_deleted == False
            )
        )).all()
        
        if not chunks_with_embeddings:
            Logger.warning(f"知识库 {kb.id} 没有可用的分块和向量")
            return
        
        # 准备索引数据
        texts = []
        vectors = []
        metadatas = []
        
        for chunk, embedding in chunks_with_embeddings:
            texts.append(chunk.content)
            vectors.append(embedding.embedding)
            metadatas.append(chunk.metadata)
        
        # 构建索引
        index_path = Path(kb.working_dir) / "index"
        os.makedirs(index_path, exist_ok=True)
        
        await index_builder.build_index(
            texts=texts,
            vectors=vectors,
            metadatas=metadatas,
            index_path=str(index_path)
        )
        
        Logger.info(f"知识库 {kb.id} 索引构建完成")
    
    async def check_queue(self) -> Optional[int]:
        """
        检查训练队列
        
        Returns:
            Optional[int]: 下一个要训练的知识库ID
        """
        Logger.info("检查训练队列")
        
        # 检查是否有正在训练的知识库
        training_kb = (await self.db.execute(
            select(KnowledgeBase).filter(
                KnowledgeBase.training_status == TrainingStatus.TRAINING
            )
        )).scalar_one_or_none()
        
        if training_kb:
            Logger.info(f"知识库 {training_kb.id} 正在训练中")
            return None
        
        # 获取下一个待训练的知识库
        next_kb = (await self.db.execute(
            select(KnowledgeBase).filter(
                KnowledgeBase.training_status == TrainingStatus.QUEUED
            ).order_by(
                KnowledgeBase.queued_at
            )
        )).scalar_one_or_none()
        
        if next_kb:
            Logger.info(f"找到下一个要训练的知识库: {next_kb.id}")
            return next_kb.id
        
        return None
    
    async def update_training_status(
        self, 
        kb_id: int, 
        status: TrainingStatus, 
        error: Optional[str] = None
    ) -> None:
        """
        更新训练状态
        
        Args:
            kb_id: 知识库ID
            status: 新状态
            error: 错误信息
        """
        Logger.info(f"更新知识库 {kb_id} 的训练状态为 {status}")
        
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            Logger.error(f"更新状态失败: 知识库 {kb_id} 不存在")
            return
        
        kb.training_status = status
        
        if status == TrainingStatus.TRAINING:
            kb.training_started_at = datetime.now()
            kb.training_error = None
            kb.queued_at = None
        elif status == TrainingStatus.TRAINED:
            kb.training_finished_at = datetime.now()
            kb.training_error = None
        elif status == TrainingStatus.FAILED:
            kb.training_error = error
        elif status == TrainingStatus.QUEUED:
            kb.queued_at = datetime.now()
            kb.training_error = None
        
        await self.db.commit()
        await self.db.refresh(kb)
        
    async def add_to_queue(self, kb_id: int) -> bool:
        """
        将知识库添加到训练队列
        
        Args:
            kb_id: 知识库ID
            
        Returns:
            bool: 是否成功添加到队列
        """
        Logger.info(f"将知识库 {kb_id} 添加到训练队列")
        
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            Logger.error(f"添加到队列失败: 知识库 {kb_id} 不存在")
            return False
        
        if kb.training_status == TrainingStatus.QUEUED:
            Logger.warning(f"知识库 {kb_id} 已经在队列中")
            return True
        
        if not kb.can_train:
            Logger.warning(f"知识库 {kb_id} 当前状态({kb.training_status})不允许训练")
            return False
        
        # 更新状态
        kb.training_status = TrainingStatus.QUEUED
        kb.queued_at = datetime.now()
        kb.training_error = None
        await self.db.commit()
        await self.db.refresh(kb)
        
        # 添加到Redis队列
        await redis_manager.add_training_task(kb_id)
        
        return True 