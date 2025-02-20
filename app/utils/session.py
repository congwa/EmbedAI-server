from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from fast_graphrag import GraphRAG
from app.core.logger import Logger
from app.core.config import settings
import copy
from sqlalchemy import select
from app.models.knowledge_base import KnowledgeBase
from sqlalchemy.orm import Session

class GraphRAGSession:
    def __init__(self, kb_id: str, llm_config: dict):
        self.kb_id = kb_id
        self.grag = self._init_graphrag(llm_config)
        self.last_active = datetime.now()
    
    def _init_graphrag(self, llm_config: dict) -> GraphRAG:
        from fast_graphrag import GraphRAG
        from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService
        import instructor
        
        # 从数据库获取知识库信息
        kb = self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == self.kb_id)
        ).scalar_one_or_none()
        
        if not kb:
            raise ValueError(f"Knowledge base {self.kb_id} not found")
        
        if not kb.working_dir:
            raise ValueError(f"Knowledge base {self.kb_id} has no working directory")
        
        return GraphRAG(
            working_dir=kb.working_dir,  # 使用知识库的工作目录
            domain=llm_config.get("domain", "通用知识领域"),
            example_queries="\n".join(llm_config.get("example_queries", [])),
            entity_types=llm_config.get("entity_types", []),
            config=GraphRAG.Config(
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
            ),
        )

    async def train(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> Tuple[int, int, int]:
        """训练知识库

        Args:
            documents (List[str]): 要处理的文档内容列表
            metadata (Optional[List[Dict[str, Any]]], optional): 文档元数据列表. Defaults to None.

        Returns:
            Tuple[int, int, int]: 返回实体数量、关系数量和文本块数量
        """
        try:
            # 使用GraphRAG的insert方法处理文档
            return await self.grag.async_insert(
                content=documents,
                metadata=metadata,
                show_progress=True
            )
        except Exception as e:
            Logger.error(f"训练过程出错: {e}")
            raise e

class SessionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions = {}
            cls._instance.cleanup_task = None
            cls._instance.db = None
        return cls._instance
    
    def __init__(self, db: Optional[Session] = None):
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        if db is not None:
            self.db = db
    
    def _get_default_llm_config(self) -> Dict[str, Any]:
        """获取默认的 LLM 配置"""
        return copy.deepcopy(settings.DEFAULT_LLM_CONFIG)

    def _merge_llm_config(self, user_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """合并用户配置和默认配置
        
        Args:
            user_config: 用户提供的配置，可以为 None
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        config = self._get_default_llm_config()
        if user_config:
            # 合并 llm 配置
            if "llm" in user_config:
                config["llm"].update(user_config["llm"])
            # 合并 embeddings 配置
            if "embeddings" in user_config:
                config["embeddings"].update(user_config["embeddings"])
            # 合并其他顶级配置
            for key, value in user_config.items():
                if key not in ["llm", "embeddings"]:
                    config[key] = value
        return config

    def _init_graphrag(self, llm_config: dict) -> GraphRAG:
        from fast_graphrag import GraphRAG
        from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService
        import instructor
        
        # 从数据库获取知识库信息
        kb = self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == self.kb_id)
        ).scalar_one_or_none()
        
        if not kb:
            raise ValueError(f"Knowledge base {self.kb_id} not found")
        
        if not kb.working_dir:
            raise ValueError(f"Knowledge base {self.kb_id} has no working directory")
        
        return GraphRAG(
            working_dir=kb.working_dir,  # 使用知识库的工作目录
            domain=llm_config.get("domain", "通用知识领域"),
            example_queries="\n".join(llm_config.get("example_queries", [])),
            entity_types=llm_config.get("entity_types", []),
            config=GraphRAG.Config(
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
            ),
        )

    def get_session(self, kb_id: str, llm_config: Optional[Dict[str, Any]] = None):
        """获取会话实例
        
        Args:
            kb_id: 知识库 ID
            llm_config: 用户提供的配置，可以为 None
            
        Returns:
            GraphRAG: 配置好的 GraphRAG 实例
        """
        self.kb_id = kb_id
        if kb_id not in self.sessions:
            self.sessions[kb_id] = self._init_graphrag(llm_config)
        self.sessions[kb_id].last_active = datetime.now()
        return self.sessions[kb_id]

    def get_session_sync(self, kb_id: str, llm_config: Optional[Dict[str, Any]] = None):
        """同步方式获取会话实例"""
        return self.get_session(kb_id, llm_config)
    
    async def remove_session(self, kb_id: str):
        if kb_id in self.sessions:
            del self.sessions[kb_id]
    
    async def _cleanup_inactive_sessions(self):
        while True:
            await asyncio.sleep(300)
            current_time = datetime.now()
            inactive_sessions = [
                kb_id for kb_id, session in self.sessions.items()
                if (current_time - session.last_active) > timedelta(minutes=30)
            ]
            for kb_id in inactive_sessions:
                await self.remove_session(kb_id)