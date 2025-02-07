from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc
from app.models.document import Document, DocumentType
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentPagination, DocumentResponse
from app.core.exceptions import NotFoundError

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
        doc = Document(
            **doc_in.model_dump(),
            knowledge_base_id=knowledge_base_id,
            created_by_id=created_by_id
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    async def get(self, doc_id: int) -> Optional[Document]:
        """获取指定ID的文档

        Args:
            doc_id (int): 文档ID

        Returns:
            Optional[Document]: 文档对象，如果不存在则返回None
        """
        return self.db.query(Document).filter(
            Document.id == doc_id,
            Document.is_deleted == False
        ).first()

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
        query = self.db.query(Document).filter(
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

        total = query.count()
        items = query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()

        return DocumentPagination(
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            items=[DocumentResponse.from_orm(item) for item in items]
        )

    async def update(self, doc_id: int, doc_in: DocumentUpdate) -> Document:
        """更新文档

        Args:
            doc_id (int): 文档ID
            doc_in (DocumentUpdate): 文档更新模型

        Returns:
            Document: 更新后的文档对象

        Raises:
            NotFoundError: 当文档不存在时抛出
        """
        doc = await self.get(doc_id)
        if not doc:
            raise NotFoundError("Document not found")

        update_data = doc_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc, field, value)

        self.db.commit()
        self.db.refresh(doc)
        return doc

    async def delete(self, doc_id: int) -> Document:
        """软删除文档

        将文档标记为已删除状态，而不是真正从数据库中删除

        Args:
            doc_id (int): 文档ID

        Returns:
            Document: 被删除的文档对象

        Raises:
            NotFoundError: 当文档不存在时抛出
        """
        doc = await self.get(doc_id)
        if not doc:
            raise NotFoundError("Document not found")

        doc.is_deleted = True
        self.db.commit()
        self.db.refresh(doc)
        return doc