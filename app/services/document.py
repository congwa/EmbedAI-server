from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc
from app.models.document import Document, DocumentType
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentPagination, DocumentResponse
from app.core.exceptions import NotFoundError
from sqlalchemy.sql import select, func
from app.models.knowledge_base import KnowledgeBase, TrainingStatus

class DocumentService:
    """文档服务类

    处理文档相关的业务逻辑，包括文档的创建、查询、更新和软删除
    """
    def __init__(self, db: Session):
        """初始化文档服务

        Args:
            db (Session): 数据库会话对象
        """
        self.db = db

    async def create(self, doc_in: DocumentCreate, knowledge_base_id: int, created_by_id: int) -> Document:
        """创建新文档

        Args:
            doc_in (DocumentCreate): 文档创建模型
            knowledge_base_id (int): 知识库ID
            created_by_id (int): 创建者用户ID

        Returns:
            Document: 创建成功的文档对象
        """
        # 获取知识库
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id)
        )).scalar_one_or_none()
        if not kb:
            raise ValueError("Knowledge base not found")

        # 创建文档
        doc = Document(
            title=doc_in.title,
            content=doc_in.content,
            doc_type=doc_in.doc_type,
            knowledge_base_id=knowledge_base_id,
            created_by_id=created_by_id
        )
        self.db.add(doc)
        
        # 更新知识库状态为 INIT
        kb.training_status = TrainingStatus.INIT
        kb.training_started_at = None
        kb.training_finished_at = None
        kb.training_error = None
        kb.queued_at = None
        
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get(self, doc_id: int) -> Optional[Document]:
        """获取指定ID的文档

        Args:
            doc_id (int): 文档ID

        Returns:
            Optional[Document]: 文档对象，如果不存在则返回None
        """
        return (await self.db.execute(
            select(Document).filter(
                Document.id == doc_id,
                Document.is_deleted == False
            )
        )).scalar_one_or_none()

    async def get_multi(
        self,
        knowledge_base_id: int,
        skip: int = 0,
        limit: int = 10,
        title: Optional[str] = None,
        doc_type: Optional[DocumentType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> DocumentPagination:
        """获取文档列表

        Args:
            knowledge_base_id (int): 知识库ID
            skip (int): 分页偏移量
            limit (int): 每页数量
            title (Optional[str]): 文档标题（模糊搜索）
            doc_type (Optional[DocumentType]): 文档类型
            start_time (Optional[datetime]): 创建时间范围开始
            end_time (Optional[datetime]): 创建时间范围结束

        Returns:
            DocumentPagination: 分页的文档列表
        """
        query = select(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.is_deleted == False
        )

        # 添加可选的查询条件
        if title:
            query = query.filter(Document.title.ilike(f"%{title}%"))
        if doc_type:
            query = query.filter(Document.doc_type == doc_type)
        if start_time:
            query = query.filter(Document.created_at >= start_time)
        if end_time:
            query = query.filter(Document.created_at <= end_time)

        total = (await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar()

        items = (await self.db.execute(
            query.order_by(desc(Document.created_at)).offset(skip).limit(limit)
        )).scalars().all()

        return DocumentPagination(
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            items=[DocumentResponse.model_validate(item) for item in items]
        )

    async def update(self, doc_id: int, doc_in: DocumentUpdate) -> Document:
        """更新文档

        Args:
            doc_id (int): 文档ID
            doc_in (DocumentUpdate): 文档更新模型

        Returns:
            Document: 更新后的文档对象

        Raises:
            NotFoundError: 文档不存在时抛出此异常
        """
        doc = await self.get(doc_id)
        if not doc:
            raise NotFoundError("Document not found")

        for field, value in doc_in.model_dump(exclude_unset=True).items():
            setattr(doc, field, value)

        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def delete(self, doc_id: int) -> Document:
        """软删除文档

        Args:
            doc_id (int): 文档ID

        Returns:
            Document: 被删除的文档对象

        Raises:
            NotFoundError: 文档不存在时抛出此异常
        """
        doc = await self.get(doc_id)
        if not doc:
            raise NotFoundError("Document not found")

        doc.is_deleted = True
        await self.db.commit()
        await self.db.refresh(doc)
        return doc