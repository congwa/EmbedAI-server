from typing import Optional, Dict, Any
import os
import hashlib
import shutil
from pathlib import Path as FilePath
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from datetime import datetime
from sqlalchemy import select, and_
from typing import Optional, Dict, Any
import os
import hashlib
import shutil
import asyncio
from pathlib import Path as FilePath
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime

from app.core.config import settings
from app.core.logger import Logger
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.knowledge_base import KnowledgeBase, PermissionType
from app.rag.extractor.extract_processor import ExtractProcessor
from app.schemas.document import DocumentCreate, DocumentUpdate
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
        kb_id: int,
        user_id: int
    ) -> Document:
        """创建新文档
        
        Args:
            document: 文档创建模型，目前仅支持文本类型
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            Document: 创建的文档对象
            
        Raises:
            HTTPException: 当知识库不存在或文档类型不支持时抛出
        """
        Logger.info(f"Creating new document '{document.title}' for knowledge base {kb_id}")
        
        # 检查文档类型
        # 允许创建所有在 DocumentType 枚举中定义的类型
        if document.doc_type not in DocumentType:
            Logger.error(f"Document creation failed: Unsupported document type {document.doc_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目前仅支持文本类型文档"
            )
        
        # 检查知识库是否存在
        kb = (await self.db.execute(
            select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
        )).scalar_one_or_none()
        
        if not kb:
            Logger.error(f"Document creation failed: Knowledge base {kb_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )

        # 创建文档记录
        db_document = Document(
            title=document.title,
            content=document.content,
            doc_type=DocumentType.TEXT,
            knowledge_base_id=kb_id,
            created_by_id=user_id
        )

        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)
        
        Logger.info(f"Document '{document.title}' (ID: {db_document.id}) created successfully")
        return db_document

    async def reprocess_document(self, document_id: int, user_id: int) -> Document:
        """重新处理指定文档"""
        Logger.info(f"Reprocessing document {document_id} requested by user {user_id}")

        doc = await self.get(document_id)

        # 动态导入以避免循环依赖
        from app.services.knowledge_base import KnowledgeBaseService

        kb_service = KnowledgeBaseService(self.db)
        permission_granted = await kb_service.check_permission(
            doc.knowledge_base_id, user_id, PermissionType.EDITOR
        )
        if not permission_granted:
            Logger.warning(
                f"Reprocess rejected: User {user_id} lacks EDITOR permission for KB {doc.knowledge_base_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有足够的权限执行此操作"
            )

        if not doc.storage_path or not os.path.exists(doc.storage_path):
            Logger.error(
                f"Reprocess failed: Document {document_id} has no file or file is missing."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该文档不支持重新处理（非文件上传或文件已丢失）",
            )

        # 重置状态并触发处理
        doc.processing_status = ProcessingStatus.PROCESSING
        doc.content = None
        doc.error_message = None
        doc.word_count = 0
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        try:
            extractor = ExtractProcessor(self.db)
            asyncio.create_task(extractor.extract_and_save(doc.id))
            Logger.info(f"Queued reprocessing task for document {doc.id}")
        except Exception as e:
            doc.processing_status = ProcessingStatus.FAILED
            doc.error_message = f"Failed to trigger reprocessing: {str(e)}"
            self.db.add(doc)
            await self.db.commit()
            Logger.error(f"Failed to queue reprocessing for document {doc.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="触发文档重新处理失败",
            )

        return doc

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

        # 检查文档类型，允许更新为任何有效的文档类型
        if document.doc_type and document.doc_type not in DocumentType:
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

    async def create_from_upload(
        self, kb_id: int, user_id: int, file: UploadFile
    ) -> Document:
        """从上传的文件创建新文档"""
        storage_path = FilePath(settings.FILE_STORAGE_PATH)
        os.makedirs(storage_path, exist_ok=True)

        contents = await file.read()
        file_hash = hashlib.sha256(contents).hexdigest()

        existing_doc = (
            await self.db.execute(
                select(Document).filter(
                    and_(
                        Document.knowledge_base_id == kb_id,
                        Document.file_hash == file_hash,
                        Document.is_deleted == False,
                    )
                )
            )
        ).scalar_one_or_none()

        if existing_doc:
            raise HTTPException(status_code=409, detail="相同的文件已存在")

        file_location = storage_path / f"{file_hash}_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(contents)

        file_extension = FilePath(file.filename).suffix
        doc_type = DocumentType.from_extension(file_extension)

        db_document = Document(
            title=file.filename,
            doc_type=doc_type,
            knowledge_base_id=kb_id,
            created_by_id=user_id,
            file_name=file.filename,
            file_size=len(contents),
            file_hash=file_hash,
            mime_type=file.content_type,
            storage_path=str(file_location),
            processing_status=ProcessingStatus.PROCESSING,
        )
        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)

        try:
            extractor = ExtractProcessor(self.db)
            asyncio.create_task(extractor.extract_and_save(db_document.id))
            Logger.info(f"Queued extraction task for document {db_document.id}")
        except Exception as e:
            db_document.processing_status = ProcessingStatus.FAILED
            db_document.error_message = f"Failed to trigger extraction: {str(e)}"
            self.db.add(db_document)
            await self.db.commit()
            Logger.error(
                f"Failed to queue extraction for document {db_document.id}: {str(e)}"
            )

        return db_document
        """从上传的文件创建新文档"""
        # 确保存储目录存在
        storage_path = FilePath(settings.FILE_STORAGE_PATH)
        os.makedirs(storage_path, exist_ok=True)

        # 读取文件内容并计算哈希
        contents = await file.read()
        file_hash = hashlib.sha256(contents).hexdigest()

        # 检查知识库中是否已存在相同的文件
        existing_doc = (await self.db.execute(
            select(Document).filter(
                and_(
                    Document.knowledge_base_id == kb_id,
                    Document.file_hash == file_hash,
                    Document.is_deleted == False
                )
            )
        )).scalar_one_or_none()

        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"相同的文件 '{file.filename}' 已存在于此知识库中。"
            )

        # 保存文件到存储路径
        file_location = storage_path / f"{file_hash}_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(contents)

        # 从文件扩展名推断文档类型
        file_extension = FilePath(file.filename).suffix
        doc_type = DocumentType.from_extension(file_extension)

        # 创建文档记录
        db_document = Document(
            title=file.filename,
            doc_type=doc_type,
            knowledge_base_id=kb_id,
            created_by_id=user_id,
            file_name=file.filename,
            file_size=len(contents),
            file_hash=file_hash,
            mime_type=file.content_type,
            storage_path=str(file_location),
            processing_status=ProcessingStatus.PROCESSING,
        )
        self.db.add(db_document)
        # 提交一次即可，后续由异步任务更新状态
        await self.db.commit()
        await self.db.refresh(db_document)

        # 提取文件内容
        try:
            extractor = ExtractProcessor()
            extracted_content = await extractor.extract(str(file_location))
            
            # 更新文档内容和状态
            db_document.content = extracted_content
            db_document.processing_status = 'completed'
            Logger.info(f"文件 '{file.filename}' (ID: {db_document.id}) 内容提取成功。")

        except Exception as e:
            db_document.processing_status = 'failed'
            db_document.processing_error = str(e)
            Logger.error(f"文件 '{file.filename}' (ID: {db_document.id}) 内容提取失败: {str(e)}")
        
        # 提交最终状态
        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)

        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)

        if db_document.processing_status == 'failed':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件 '{file.filename}' 内容提取失败: {db_document.processing_error}"
            )

        Logger.info(f"文件 '{file.filename}' 已成功上传并处理 (ID: {db_document.id})。")
        return db_document