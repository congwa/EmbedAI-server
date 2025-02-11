from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from fast_graphrag import GraphRAG
from app.core.logger import Logger

class GraphRAGSession:
    def __init__(self, kb_id: str, llm_config: dict):
        self.kb_id = kb_id
        self.grag = self._init_graphrag(llm_config)
        self.last_active = datetime.now()
    
    def _init_graphrag(self, llm_config: dict) -> GraphRAG:
        from fast_graphrag import GraphRAG
        from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService
        import instructor
        
        return GraphRAG(
            working_dir=f"workspaces/kb_{self.kb_id}",
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
        return cls._instance
    
    def __init__(self):
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
    
    async def get_session(self, kb_id: str, llm_config: dict) -> GraphRAGSession:
        if kb_id not in self.sessions:
            self.sessions[kb_id] = GraphRAGSession(kb_id, llm_config)
        self.sessions[kb_id].last_active = datetime.now()
        return self.sessions[kb_id]
    
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