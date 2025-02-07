from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio
from fast_graphrag import GraphRAG
from app.core.config import settings

class GraphRAGSession:
    def __init__(self, kb_id: str, model_config: dict):
        self.kb_id = kb_id
        self.grag = self._init_graphrag(model_config)
        self.last_active = datetime.now()
    
    def _init_graphrag(self, model_config: dict) -> GraphRAG:
        from fast_graphrag import GraphRAG
        from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService
        import instructor
        
        return GraphRAG(
            working_dir=f"workspaces/kb_{self.kb_id}",
            domain=model_config.get("domain", "通用知识领域"),
            example_queries="\n".join(model_config.get("example_queries", [])),
            entity_types=model_config.get("entity_types", []),
            config=GraphRAG.Config(
                llm_service=OpenAILLMService(
                    model=model_config["llm"]["model"],
                    base_url=model_config["llm"]["base_url"],
                    api_key=model_config["llm"]["api_key"],
                    mode=instructor.Mode.JSON,
                    client="openai"
                ),
                embedding_service=OpenAIEmbeddingService(
                    model=model_config["embeddings"]["model"],
                    base_url=model_config["embeddings"]["base_url"],
                    api_key=model_config["embeddings"]["api_key"],
                    client="openai",
                    embedding_dim=model_config["embeddings"]["embedding_dim"],
                ),
            ),
        )

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
    
    async def get_session(self, kb_id: str, model_config: dict) -> GraphRAGSession:
        if kb_id not in self.sessions:
            self.sessions[kb_id] = GraphRAGSession(kb_id, model_config)
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