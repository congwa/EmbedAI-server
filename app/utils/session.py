from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.core.logger import Logger
from app.schemas.llm import LLMConfig
from app.rag.retrieval.retrieval_service import RetrievalService
from app.rag.embedding.embedding_engine import EmbeddingEngine
from app.rag.training.training_manager import RAGTrainingManager

# 定义RAG会话类型
RAGSessionType = Tuple[RetrievalService, EmbeddingEngine, datetime]


class SessionManager:
    """会话管理器

    管理知识库的RAG会话实例，提供：
    1. 检索服务会话创建和获取
    2. 向量化引擎会话管理
    3. 自动清理过期会话
    4. 统一的配置管理
    """

    _instance = None
    sessions: Dict[str, RAGSessionType]
    cleanup_task: Optional[asyncio.Task]
    db: Optional[Session]

    def __new__(cls, db: Session = None):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions = {}
            cls._instance.cleanup_task = None
            cls._instance.db = None
        if db is not None:
            cls._instance.db = db
        return cls._instance

    def __init__(self, db: Session = None):
        """初始化会话管理器

        Args:
            db: 数据库会话，用于获取知识库配置
        """
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        if db is not None:
            self.db = db

    async def _init_rag_session(
        self, kb_id: str, llm_config: LLMConfig
    ) -> Tuple[RetrievalService, EmbeddingEngine]:
        """初始化RAG会话实例

        Args:
            kb_id: 知识库ID
            llm_config: LLM配置

        Returns:
            Tuple[RetrievalService, EmbeddingEngine]: 检索服务和向量化引擎实例

        Raises:
            ValueError: 当知识库配置无效时
        """
        Logger.info(f"初始化RAG会话 for knowledge base {kb_id}")
        if not self.db:
            raise ValueError("Database session not initialized")

        result = await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )
        kb = result.scalars().first()

        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        Logger.info(f"创建RAG服务实例:")
        Logger.info(f"  - 知识库ID: {kb_id}")
        Logger.info(f"  - 知识库名称: {kb.name}")
        Logger.info(f"  - LLM模型: {llm_config.llm.model}")
        Logger.info(f"  - 向量化模型: {llm_config.embeddings.model}")

        # 创建检索服务
        retrieval_service = RetrievalService(self.db)

        # 创建向量化引擎
        embedding_engine = EmbeddingEngine(llm_config, self.db)

        Logger.info(f"RAG会话初始化完成")

        return retrieval_service, embedding_engine

    async def get_session(
        self, kb_id: str, llm_config: Optional[LLMConfig] = None
    ) -> Tuple[RetrievalService, EmbeddingEngine]:
        """获取或创建RAG会话

        Args:
            kb_id: 知识库ID
            llm_config: 可选的LLM配置

        Returns:
            Tuple[RetrievalService, EmbeddingEngine]: 检索服务和向量化引擎
        """
        if kb_id not in self.sessions:
            # 获取知识库信息
            result = await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
            kb = result.scalars().first()

            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")

            Logger.info(f"初始化RAG会话 for knowledge base {kb_id}")

            # 使用知识库配置或默认配置
            config = LLMConfig.model_validate(
                kb.llm_config if llm_config is None else llm_config
            )

            # 创建新会话
            retrieval_service, embedding_engine = await self._init_rag_session(
                kb_id, config
            )
            self.sessions[kb_id] = (retrieval_service, embedding_engine, datetime.now())

        # 更新最后访问时间
        retrieval_service, embedding_engine, _ = self.sessions[kb_id]
        self.sessions[kb_id] = (retrieval_service, embedding_engine, datetime.now())

        return retrieval_service, embedding_engine

    async def get_retrieval_service(
        self, kb_id: str, llm_config: Optional[LLMConfig] = None
    ) -> RetrievalService:
        """获取检索服务

        Args:
            kb_id: 知识库ID
            llm_config: 可选的LLM配置

        Returns:
            RetrievalService: 检索服务实例
        """
        retrieval_service, _ = await self.get_session(kb_id, llm_config)
        return retrieval_service

    async def get_embedding_engine(
        self, kb_id: str, llm_config: Optional[LLMConfig] = None
    ) -> EmbeddingEngine:
        """获取向量化引擎

        Args:
            kb_id: 知识库ID
            llm_config: 可选的LLM配置

        Returns:
            EmbeddingEngine: 向量化引擎实例
        """
        _, embedding_engine = await self.get_session(kb_id, llm_config)
        return embedding_engine

    async def get_training_manager(
        self, kb_id: str, llm_config: Optional[LLMConfig] = None
    ) -> RAGTrainingManager:
        """获取训练管理器

        Args:
            kb_id: 知识库ID
            llm_config: 可选的LLM配置

        Returns:
            RAGTrainingManager: 训练管理器实例
        """
        if not self.db:
            raise ValueError("Database session not initialized")

        # 获取知识库信息
        result = await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )
        kb = result.scalars().first()

        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        # 使用知识库配置或默认配置
        config = LLMConfig.model_validate(
            kb.llm_config if llm_config is None else llm_config
        )

        # 创建训练管理器
        training_manager = RAGTrainingManager(self.db, config)

        return training_manager

    async def remove_session(self, kb_id: str) -> None:
        """移除指定的会话

        Args:
            kb_id: 知识库ID
        """
        if kb_id in self.sessions:
            del self.sessions[kb_id]
            Logger.info(f"移除RAG会话 for knowledge base {kb_id}")

    async def _cleanup_inactive_sessions(self) -> None:
        """清理不活跃的会话

        定期检查并清理超过30分钟未使用的会话
        """
        while True:
            try:
                current_time = datetime.now()
                inactive_kbs = [
                    kb_id
                    for kb_id, (_, _, last_active) in self.sessions.items()
                    if (current_time - last_active) > timedelta(minutes=30)
                ]

                for kb_id in inactive_kbs:
                    await self.remove_session(kb_id)

                await asyncio.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                Logger.error(f"会话清理错误: {e}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试
