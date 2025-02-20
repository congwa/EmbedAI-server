from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import select, and_
from app.models.document import Document, DocumentType
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.models.knowledge_base import KnowledgeBase
from fastapi import HTTPException, status
from app.core.logger import Logger

class DocumentService:
    """文档服务类

    处理文档相关的业务逻辑，包括文档的创建、查询、更新和软删除
    目前仅支持文本类型文档
    """
    def __init__(self, db: Session):
        """初始化文档服务

        Args:
            db (Session): 数据库会话对象
        """
        self.db = db

    async def create(
        self,
        document: DocumentCreate,
    ) -> Document:
        """创建新文档
        
        Args:
            document (DocumentCreate): 文档创建模型，目前仅支持文本类型
            
        Returns:
            Document: 创建的文档对象
            
        Raises:
            HTTPException: 当知识库不存在或文档类型不支持时抛出
        """
        Logger.info(f"Creating new document '{document.title}' for knowledge base {document.knowledge_base_id}")
        
        # 检查文档类型
        if document.doc_type != DocumentType.TEXT:
            Logger.error(f"Document creation failed: Unsupported document type {document.doc_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目前仅支持文本类型文档"
            )
        
        # 检查知识库是否存在
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == document.knowledge_base_id)
        )).scalar_one_or_none()
        
        if not kb:
            Logger.error(f"Document creation failed: Knowledge base {document.knowledge_base_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 创建文档记录
        db_document = Document(
            title=document.title,
            content=document.content,
            doc_type=DocumentType.TEXT,
            knowledge_base_id=document.knowledge_base_id
        )

        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)
        
        Logger.info(f"Document '{document.title}' (ID: {db_document.id}) created successfully")
        return db_document

    async def get(self, document_id: int) -> Document:
        """获取文档详情"""
        Logger.debug(f"Retrieving document {document_id}")
        
        document = (await self.db.execute(
            select(Document).filter(
                and_(
                    Document.id == document_id,
                    Document.is_deleted == False
                )
            )
        )).scalar_one_or_none()
        
        if not document:
            Logger.warning(f"Document retrieval failed: Document {document_id} not found or deleted")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在或已删除"
            )
            
        return document

    async def get_multi(
        self,
        knowledge_base_id: int,
        skip: int = 0,
        limit: int = 10,
        title: Optional[str] = None,
        doc_type: Optional[DocumentType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取文档列表"""
        Logger.info(f"Retrieving documents for knowledge base {knowledge_base_id}")
        
        # 构建查询条件
        conditions = [
            Document.knowledge_base_id == knowledge_base_id,
            Document.is_deleted == False
        ]
        
        if title:
            conditions.append(Document.title.ilike(f"%{title}%"))
        if doc_type:
            conditions.append(Document.doc_type == doc_type)
        if start_time:
            conditions.append(Document.created_at >= start_time)
        if end_time:
            conditions.append(Document.created_at <= end_time)
            
        # 执行查询
        try:
            total = (await self.db.execute(
                select(Document).filter(and_(*conditions))
            )).scalars().all()
            
            documents = (await self.db.execute(
                select(Document)
                .filter(and_(*conditions))
                .offset(skip)
                .limit(limit)
            )).scalars().all()
            
            Logger.debug(f"Retrieved {len(documents)} documents (total: {len(total)}) for knowledge base {knowledge_base_id}")
            
            return {
                "total": len(total),
                "items": documents
            }
        except Exception as e:
            Logger.error(f"Document retrieval failed for knowledge base {knowledge_base_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文档列表失败: {str(e)}"
            )

    async def update(
        self,
        document_id: int,
        document: DocumentUpdate
    ) -> Document:
        """更新文档"""
        Logger.info(f"Updating document {document_id}")
        
        # 查找现有文档
        db_document = (await self.db.execute(
            select(Document).filter(Document.id == document_id)
        )).scalar_one_or_none()
        
        if not db_document:
            Logger.error(f"Document update failed: Document {document_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )

        # 检查文档类型
        if document.doc_type and document.doc_type != DocumentType.TEXT:
            Logger.error(f"Document update failed: Unsupported document type {document.doc_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目前仅支持文本类型文档"
            )

        # 更新文档字段
        update_data = document.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_document, field, value)
            
        try:
            await self.db.commit()
            await self.db.refresh(db_document)
            Logger.info(f"Document {document_id} updated successfully")
            return db_document
        except Exception as e:
            Logger.error(f"Document update failed for document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文档更新失败: {str(e)}"
            )

    async def delete(self, document_id: int) -> None:
        """删除文档"""
        Logger.info(f"Deleting document {document_id}")
        
        # 查找文档
        db_document = (await self.db.execute(
            select(Document).filter(Document.id == document_id)
        )).scalar_one_or_none()
        
        if not db_document:
            Logger.warning(f"Document deletion skipped: Document {document_id} not found")
            return

        try:
            # 软删除
            db_document.is_deleted = True
            db_document.deleted_at = datetime.now()
            await self.db.commit()
            Logger.info(f"Document {document_id} marked as deleted successfully")
        except Exception as e:
            Logger.error(f"Document deletion failed for document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文档删除失败: {str(e)}"
            )