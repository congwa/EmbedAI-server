from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from fast_graphrag import GraphRAG
from fast_graphrag._llm import OpenAIEmbeddingService
from .custom_openai_llm import CustomOpenAILLMService
import instructor
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.core.logger import Logger
from app.schemas.llm import LLMConfig
import fast_graphrag._services._state_manager as state_manager

from fast_graphrag._storage._namespace import Workspace

from functools import wraps
from fast_graphrag._storage._namespace import Workspace
import os

from fast_graphrag._storage._namespace import Workspace

# 猴子补丁：修复GraphRAG在加载时无法正确获取检查点的问题
def custom_get_load_path(self) -> Optional[str]:
    # 自定义加载路径的逻辑
    self.checkpoints = sorted(
        (int(x.name) for x in os.scandir(self.working_dir) if x.is_dir() and not x.name.startswith("0__err_")),
        reverse=True,
    )
    if self.checkpoints and not self.current_load_checkpoint:
        self.current_load_checkpoint = self.checkpoints[0]
        
    load_path = self.get_path(self.working_dir, self.current_load_checkpoint)
    if load_path == self.working_dir and len([x for x in os.scandir(load_path) if x.is_file()]) == 0:
        return None
    return load_path

# 替换原方法
Workspace.get_load_path = custom_get_load_path

# 定义会话类型
SessionType = Tuple[GraphRAG, datetime]

# 添加自定义进度条类
class CustomTqdm:
    """自定义进度条类
    
    用于替换 fast-graphrag 中的 tqdm 进度条
    实现了必要的接口：__init__, __iter__, update, set_description
    """
    def __init__(self, iterable=None, desc=None, total=None, disable=False):
        self.iterable = iterable
        self.desc = desc
        self.total = total
        self.disable = disable
        self.n = 0
        
        if desc and total:
            Logger.info(f"Starting {desc} - Total: {total}")
        
    def __iter__(self):
        if self.disable:
            yield from self.iterable
            return
            
        for item in self.iterable:
            self.n += 1
            if self.total:
                percentage = (self.n / self.total) * 100
                Logger.info(f"{self.desc}: {self.n}/{self.total} ({percentage:.1f}%)")
            else:
                Logger.info(f"{self.desc}: {self.n}")
            yield item
            
    def update(self, n=1):
        if self.disable:
            return
            
        self.n += n
        if self.total:
            percentage = (self.n / self.total) * 100
            Logger.info(f"{self.desc}: {self.n}/{self.total} ({percentage:.1f}%)")
        else:
            Logger.info(f"{self.desc}: {self.n}")
        
    def set_description(self, desc):
        if not self.disable:
            self.desc = desc
            Logger.info(f"Progress: {desc}")
            
    def close(self):
        if not self.disable and self.desc:
            Logger.info(f"Completed: {self.desc}")

class SessionManager:
    """会话管理器
    
    管理知识库的 GraphRAG 会话实例，提供：
    1. 会话创建和获取
    2. 自动清理过期会话
    3. 统一的配置管理
    """
    
    _instance = None
    sessions: Dict[str, SessionType]
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
    
    def _create_graphrag_config(self, llm_config: LLMConfig) -> GraphRAG.Config:
        """创建 GraphRAG 配置
        
        Args:
            llm_config: LLM 配置
            
        Returns:
            GraphRAG.Config: GraphRAG 配置对象
        """
        Logger.info(f"Creating GraphRAG config with LLM model: {llm_config.llm.model}")
        Logger.info(f"Creating GraphRAG config with Embedding model: {llm_config.embeddings.model}")
        Logger.info(f"Creating GraphRAG config with Embedding dim: {llm_config.embeddings.embedding_dim}")
        Logger.info(f"Creating GraphRAG config with Embedding base_url: {llm_config.embeddings.base_url}")
        Logger.info(f"Creating GraphRAG config with Embedding api_key: {llm_config.embeddings.api_key}")
        Logger.info(f"Creating GraphRAG config with LLM base_url: {llm_config.llm.base_url}")
        Logger.info(f"Creating GraphRAG config with LLM api_key: {llm_config.llm.api_key}")
        Logger.info(f"Creating GraphRAG config with LLM model: {llm_config.llm.model}")
        return GraphRAG.Config(
            llm_service=CustomOpenAILLMService(
                model=llm_config.llm.model,
                base_url=llm_config.llm.base_url,
                api_key=llm_config.llm.api_key,
                mode=instructor.Mode.JSON,
                client="openai"
            ),
            embedding_service=OpenAIEmbeddingService(
                model=llm_config.embeddings.model,
                base_url=llm_config.embeddings.base_url,
                api_key=llm_config.embeddings.api_key,
                client="openai",
                embedding_dim=llm_config.embeddings.embedding_dim
            ),
        )
    
    async def _init_graphrag(self, kb_id: str, llm_config: LLMConfig) -> GraphRAG:
        """初始化 GraphRAG 实例
        
        Args:
            kb_id: 知识库ID
            llm_config: LLM 配置
            
        Returns:
            GraphRAG: 初始化好的 GraphRAG 实例
            
        Raises:
            ValueError: 当知识库配置无效时
        """
        Logger.info(f"_init_graphrag for knowledge base {kb_id}")
        if not self.db:
            raise ValueError("Database session not initialized")
            
        result = await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )
        kb = result.scalars().first()
        
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")
        
        if not kb.working_dir:
            raise ValueError(f"Knowledge base {kb_id} has no working directory")
        
        import fast_graphrag._utils
        fast_graphrag._utils.logger = Logger
        state_manager.tqdm = CustomTqdm
        # 创建 GraphRAG 实例
        grag = GraphRAG(
            working_dir=kb.working_dir,
            domain=llm_config.domain,
            example_queries="\n".join(llm_config.example_queries or []),
            entity_types=llm_config.entity_types or [],
            config=self._create_graphrag_config(llm_config)
        )
        
        
        return grag
    
    async def get_session(self, kb_id: str, llm_config: Optional[LLMConfig] = None) -> GraphRAG:
        """获取或创建会话"""
        if kb_id not in self.sessions:
            # 获取知识库信息
            result = await self.db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
            kb = result.scalars().first()
            
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")
                
            Logger.info(f"Initializing GraphRAG for knowledge base {kb_id}")
            
            # 使用知识库配置或默认配置
            config = LLMConfig.model_validate(kb.llm_config if llm_config is None else llm_config)
            
            # 创建新会话
            grag = await self._init_graphrag(kb_id, config)
            self.sessions[kb_id] = (grag, datetime.now())
            
        return self.sessions[kb_id][0]
    
    def get_session_sync(self, kb_id: str, llm_config: Optional[LLMConfig] = None) -> GraphRAG:
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