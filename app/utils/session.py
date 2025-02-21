from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from fast_graphrag import GraphRAG
from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService
import instructor
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.core.logger import Logger
from app.core.config import settings

class SessionManager:
    """会话管理器
    
    管理知识库的 GraphRAG 会话实例，提供：
    1. 会话创建和获取
    2. 自动清理过期会话
    3. 统一的配置管理
    """
    
    _instance = None
    
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
    
    def _create_graphrag_config(self, llm_config: dict) -> GraphRAG.Config:
        """创建 GraphRAG 配置
        
        Args:
            llm_config: LLM 配置字典
            
        Returns:
            GraphRAG.Config: GraphRAG 配置对象
        """
        return GraphRAG.Config(
            llm_service=OpenAILLMService(
                model=llm_config["llm"]["model"],
                base_url=llm_config["llm"]["base_url"],
                api_key=llm_config["llm"]["api_key"],
                mode=instructor.Mode.JSON,
                client="openai"
            ),
            embedding_service=OpenAIEmbeddingService(
                model=llm_config["embeddings"]["model"],
                base_url=llm_config["embeddings"]["base_url"],
                api_key=llm_config["embeddings"]["api_key"],
                client="openai",
                embedding_dim=llm_config["embeddings"]["embedding_dim"],
            ),
        )
    
    def _init_graphrag(self, kb_id: str, llm_config: dict) -> GraphRAG:
        """初始化 GraphRAG 实例
        
        Args:
            kb_id: 知识库ID
            llm_config: LLM 配置
            
        Returns:
            GraphRAG: 初始化好的 GraphRAG 实例
            
        Raises:
            ValueError: 当知识库配置无效时
        """
        if not self.db:
            raise ValueError("Database session not initialized")
            
        kb = self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        ).scalar_one_or_none()
        
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")
        
        if not kb.working_dir:
            raise ValueError(f"Knowledge base {kb_id} has no working directory")
        
        return GraphRAG(
            working_dir=kb.working_dir,
            domain=llm_config.get("domain", "通用知识领域"),
            example_queries="\n".join(llm_config.get("example_queries", [])),
            entity_types=llm_config.get("entity_types", []),
            config=self._create_graphrag_config(llm_config)
        )
    
    def get_session(self, kb_id: str, llm_config: Optional[Dict[str, Any]] = None) -> GraphRAG:
        """获取或创建 GraphRAG 会话
        
        Args:
            kb_id: 知识库ID
            llm_config: 可选的 LLM 配置，如果不提供则使用默认配置
            
        Returns:
            GraphRAG: GraphRAG 会话实例
        """
        if not llm_config:
            llm_config = settings.DEFAULT_LLM_CONFIG.model_dump()
            
        if kb_id not in self.sessions:
            grag = self._init_graphrag(kb_id, llm_config)
            self.sessions[kb_id] = (grag, datetime.now())
            Logger.info(f"Created new GraphRAG session for knowledge base {kb_id}")
        else:
            grag, _ = self.sessions[kb_id]
            self.sessions[kb_id] = (grag, datetime.now())
            Logger.debug(f"Retrieved existing GraphRAG session for knowledge base {kb_id}")
            
        return grag
    
    def get_session_sync(self, kb_id: str, llm_config: Optional[Dict[str, Any]] = None) -> GraphRAG:
        """同步方式获取 GraphRAG 会话
        
        Args:
            kb_id: 知识库ID
            llm_config: 可选的 LLM 配置
            
        Returns:
            GraphRAG: GraphRAG 会话实例
        """
        return self.get_session(kb_id, llm_config)
    
    async def remove_session(self, kb_id: str) -> None:
        """移除指定的会话
        
        Args:
            kb_id: 知识库ID
        """
        if kb_id in self.sessions:
            del self.sessions[kb_id]
            Logger.info(f"Removed GraphRAG session for knowledge base {kb_id}")
    
    async def _cleanup_inactive_sessions(self) -> None:
        """清理不活跃的会话
        
        定期检查并清理超过30分钟未使用的会话
        """
        while True:
            try:
                current_time = datetime.now()
                inactive_kbs = [
                    kb_id for kb_id, (_, last_active) in self.sessions.items()
                    if (current_time - last_active) > timedelta(minutes=30)
                ]
                
                for kb_id in inactive_kbs:
                    await self.remove_session(kb_id)
                    
                await asyncio.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                Logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试