from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    QueryRequest,
    QueryResponse
)
from app.utils.session import SessionManager
from datetime import timedelta
from app.utils.rate_limit import rate_limit

class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db
        self.session_manager = SessionManager()

    async def create(self, kb_in: KnowledgeBaseCreate, owner_id: int) -> KnowledgeBase:
        # 检查用户是否已经绑定了知识库
        existing_kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == owner_id).first()
        if existing_kb:
            raise ValueError("User already has a knowledge base")
            
        # 创建工作目录
        working_dir = Path(f"workspaces/kb_{owner_id}_{kb_in.name}")
        working_dir.mkdir(parents=True, exist_ok=True)
        
        kb = KnowledgeBase(
            name=kb_in.name,
            owner_id=owner_id,
            domain=kb_in.domain,
            example_queries=kb_in.example_queries,
            entity_types=kb_in.entity_types,
            model_config=kb_in.model_config.model_dump(),
            working_dir=str(working_dir)
        )
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    async def update(
        self,
        kb_id: int,
        kb_in: KnowledgeBaseUpdate,
        owner_id: int
    ) -> Optional[KnowledgeBase]:
        kb = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == owner_id
        ).first()
        
        if not kb:
            return None
            
        update_data = kb_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if isinstance(value, dict):
                current_value = getattr(kb, field) or {}
                current_value.update(value)
                value = current_value
            setattr(kb, field, value)
            
        self.db.commit()
        self.db.refresh(kb)
        
        # 如果更新了模型配置，需要清理会话
        if "model_config" in update_data:
            await self.session_manager.remove_session(str(kb_id))
            
        return kb

    async def query(self, kb_id: int, request: QueryRequest) -> QueryResponse:
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise ValueError("Knowledge base not found")
            
        # 获取或创建会话
        session = await self.session_manager.get_session(
            str(kb_id),
            kb.model_config
        )
        
        # 执行查询
        result = session.grag.query(
            request.query,
            params=request.dict(exclude={'query'})
        )
        
        return QueryResponse(
            response=result.response,
            context={
                "entities": [str(e) for e in result.context.entities],
                "relationships": [str(r) for r in result.context.relationships],
                "chunks": [str(c) for c in result.context.chunks]
            } if result.context else None
        )

    async def get_by_id(self, kb_id: int) -> Optional[KnowledgeBase]:
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()