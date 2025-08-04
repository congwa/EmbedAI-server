import asyncio
import csv
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, delete, update
from sqlalchemy.orm import selectinload

from app.models.content import (
    ContentModerationRule, ContentModerationLog, BulkOperation,
    ContentTag, ContentCategory, SearchIndex, ContentStatistics,
    DataExportTask, ContentStatus, ModerationAction, BulkOperationType
)
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.user import User
from app.schemas.content import (
    ContentModerationRuleCreate, ContentModerationRuleResponse,
    ContentModerationRequest, ContentModerationLogResponse,
    BulkOperationCreate, BulkOperationResponse,
    ContentTagCreate, ContentTagResponse, ContentCategoryCreate, ContentCategoryResponse,
    SearchRequest, SearchResponse, SearchResult,
    DataExportRequest, DataExportResponse,
    ContentDashboardResponse, AdvancedSearchFilters, BatchTagOperation
)
from app.core.logger import Logger
from app.core.redis_manager import redis_manager

class ContentService:
    """内容管理服务
    
    提供内容审核、批量操作、搜索、标签分类管理等功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 内容审核 ====================
    
    async def create_moderation_rule(
        self,
        rule_data: ContentModerationRuleCreate,
        created_by: int
    ) -> ContentModerationRuleResponse:
        """创建内容审核规则"""
        try:
            rule = ContentModerationRule(
                **rule_data.model_dump(),
                created_by=created_by
            )
            
            self.db.add(rule)
            await self.db.commit()
            await self.db.refresh(rule)
            
            return ContentModerationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                rule_type=rule.rule_type,
                conditions=rule.conditions,
                actions=rule.actions,
                priority=rule.priority,
                is_active=rule.is_active,
                auto_apply=rule.auto_apply,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                created_by=rule.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建内容审核规则失败: {str(e)}")
            raise
    
    async def moderate_content(
        self,
        moderation_request: ContentModerationRequest,
        moderator_id: int
    ) -> ContentModerationLogResponse:
        """审核内容"""
        try:
            # 记录审核日志
            log = ContentModerationLog(
                content_type=moderation_request.content_type,
                content_id=moderation_request.content_id,
                moderator_id=moderator_id,
                action=moderation_request.action.value,
                reason=moderation_request.reason,
                details=moderation_request.details,
                is_automated=False
            )
            
            self.db.add(log)
            
            # 根据内容类型和动作执行相应操作
            await self._apply_moderation_action(
                moderation_request.content_type,
                moderation_request.content_id,
                moderation_request.action,
                log
            )
            
            await self.db.commit()
            await self.db.refresh(log)
            
            return ContentModerationLogResponse(
                id=log.id,
                content_type=log.content_type,
                content_id=log.content_id,
                rule_id=log.rule_id,
                moderator_id=log.moderator_id,
                action=log.action,
                reason=log.reason,
                details=log.details,
                confidence_score=log.confidence_score,
                is_automated=log.is_automated,
                previous_status=log.previous_status,
                new_status=log.new_status,
                created_at=log.created_at
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"审核内容失败: {str(e)}")
            raise
    
    async def _apply_moderation_action(
        self,
        content_type: str,
        content_id: int,
        action: ModerationAction,
        log: ContentModerationLog
    ):
        """应用审核动作"""
        try:
            if content_type == "knowledge_base":
                kb = await self.db.get(KnowledgeBase, content_id)
                if kb:
                    log.previous_status = kb.status
                    if action == ModerationAction.APPROVE:
                        kb.status = "published"
                        log.new_status = "published"
                    elif action == ModerationAction.REJECT:
                        kb.status = "rejected"
                        log.new_status = "rejected"
                    elif action == ModerationAction.REMOVE:
                        kb.status = "deleted"
                        log.new_status = "deleted"
            
            elif content_type == "document":
                doc = await self.db.get(Document, content_id)
                if doc:
                    log.previous_status = doc.status
                    if action == ModerationAction.APPROVE:
                        doc.status = "processed"
                        log.new_status = "processed"
                    elif action == ModerationAction.REJECT:
                        doc.status = "failed"
                        log.new_status = "failed"
                    elif action == ModerationAction.REMOVE:
                        doc.status = "deleted"
                        log.new_status = "deleted"
            
        except Exception as e:
            Logger.error(f"应用审核动作失败: {str(e)}")
            raise
    
    # ==================== 批量操作 ====================
    
    async def create_bulk_operation(
        self,
        operation_data: BulkOperationCreate,
        created_by: int
    ) -> BulkOperationResponse:
        """创建批量操作"""
        try:
            operation = BulkOperation(
                name=operation_data.name,
                operation_type=operation_data.operation_type.value,
                target_type=operation_data.target_type,
                target_ids=operation_data.target_ids,
                parameters=operation_data.parameters,
                total_items=len(operation_data.target_ids),
                created_by=created_by
            )
            
            self.db.add(operation)
            await self.db.commit()
            await self.db.refresh(operation)
            
            # 异步执行批量操作
            asyncio.create_task(self._execute_bulk_operation(operation.id))
            
            return BulkOperationResponse(
                id=operation.id,
                name=operation.name,
                operation_type=operation.operation_type,
                target_type=operation.target_type,
                target_ids=operation.target_ids,
                parameters=operation.parameters,
                status=operation.status,
                progress=operation.progress,
                total_items=operation.total_items,
                processed_items=operation.processed_items,
                success_items=operation.success_items,
                failed_items=operation.failed_items,
                error_details=operation.error_details,
                result_data=operation.result_data,
                started_at=operation.started_at,
                completed_at=operation.completed_at,
                created_at=operation.created_at,
                created_by=operation.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建批量操作失败: {str(e)}")
            raise
    
    async def _execute_bulk_operation(self, operation_id: int):
        """执行批量操作"""
        from app.models.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                operation = await db.get(BulkOperation, operation_id)
                if not operation:
                    return
                
                operation.status = "running"
                operation.started_at = datetime.now()
                await db.commit()
                
                success_count = 0
                failed_count = 0
                errors = []
                
                for i, target_id in enumerate(operation.target_ids):
                    try:
                        await self._execute_single_operation(
                            db, operation, target_id
                        )
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        errors.append({
                            "target_id": target_id,
                            "error": str(e)
                        })
                    
                    # 更新进度
                    operation.processed_items = i + 1
                    operation.success_items = success_count
                    operation.failed_items = failed_count
                    operation.progress = int((i + 1) / operation.total_items * 100)
                    
                    if errors:
                        operation.error_details = {"errors": errors}
                    
                    await db.commit()
                
                operation.status = "completed"
                operation.completed_at = datetime.now()
                await db.commit()
                
                Logger.info(f"批量操作完成: {operation.name}, 成功: {success_count}, 失败: {failed_count}")
                
            except Exception as e:
                operation.status = "failed"
                operation.error_details = {"error": str(e)}
                await db.commit()
                Logger.error(f"执行批量操作失败: {str(e)}")
    
    async def _execute_single_operation(
        self,
        db: AsyncSession,
        operation: BulkOperation,
        target_id: int
    ):
        """执行单个操作"""
        try:
            if operation.target_type == "knowledge_base":
                kb = await db.get(KnowledgeBase, target_id)
                if not kb:
                    raise ValueError(f"知识库 {target_id} 不存在")
                
                if operation.operation_type == BulkOperationType.DELETE.value:
                    await db.delete(kb)
                elif operation.operation_type == BulkOperationType.ARCHIVE.value:
                    kb.status = "archived"
                elif operation.operation_type == BulkOperationType.PUBLISH.value:
                    kb.status = "published"
            
            elif operation.target_type == "document":
                doc = await db.get(Document, target_id)
                if not doc:
                    raise ValueError(f"文档 {target_id} 不存在")
                
                if operation.operation_type == BulkOperationType.DELETE.value:
                    await db.delete(doc)
                elif operation.operation_type == BulkOperationType.ARCHIVE.value:
                    doc.status = "archived"
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            raise
    
    # ==================== 标签管理 ====================
    
    async def create_tag(
        self,
        tag_data: ContentTagCreate,
        created_by: int
    ) -> ContentTagResponse:
        """创建内容标签"""
        try:
            tag = ContentTag(
                **tag_data.model_dump(),
                created_by=created_by
            )
            
            self.db.add(tag)
            await self.db.commit()
            await self.db.refresh(tag)
            
            return ContentTagResponse(
                id=tag.id,
                name=tag.name,
                description=tag.description,
                color=tag.color,
                category=tag.category,
                usage_count=tag.usage_count,
                is_system=tag.is_system,
                is_active=tag.is_active,
                created_at=tag.created_at,
                updated_at=tag.updated_at,
                created_by=tag.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建内容标签失败: {str(e)}")
            raise
    
    async def get_tags(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ContentTagResponse]:
        """获取标签列表"""
        try:
            query = select(ContentTag)
            
            if category:
                query = query.where(ContentTag.category == category)
            if is_active is not None:
                query = query.where(ContentTag.is_active == is_active)
            
            query = query.offset(skip).limit(limit).order_by(desc(ContentTag.usage_count))
            
            result = await self.db.execute(query)
            tags = result.scalars().all()
            
            return [
                ContentTagResponse(
                    id=tag.id,
                    name=tag.name,
                    description=tag.description,
                    color=tag.color,
                    category=tag.category,
                    usage_count=tag.usage_count,
                    is_system=tag.is_system,
                    is_active=tag.is_active,
                    created_at=tag.created_at,
                    updated_at=tag.updated_at,
                    created_by=tag.created_by
                ) for tag in tags
            ]
            
        except Exception as e:
            Logger.error(f"获取标签列表失败: {str(e)}")
            raise
    
    # ==================== 分类管理 ====================
    
    async def create_category(
        self,
        category_data: ContentCategoryCreate,
        created_by: int
    ) -> ContentCategoryResponse:
        """创建内容分类"""
        try:
            # 计算分类层级
            level = 0
            if category_data.parent_id:
                parent = await self.db.get(ContentCategory, category_data.parent_id)
                if parent:
                    level = parent.level + 1
            
            category = ContentCategory(
                **category_data.model_dump(),
                level=level,
                created_by=created_by
            )
            
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)
            
            return ContentCategoryResponse(
                id=category.id,
                name=category.name,
                slug=category.slug,
                description=category.description,
                parent_id=category.parent_id,
                level=category.level,
                sort_order=category.sort_order,
                icon=category.icon,
                color=category.color,
                is_active=category.is_active,
                content_count=category.content_count,
                created_at=category.created_at,
                updated_at=category.updated_at,
                created_by=category.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建内容分类失败: {str(e)}")
            raise
    
    async def get_categories_tree(self) -> List[Dict[str, Any]]:
        """获取分类树结构"""
        try:
            result = await self.db.execute(
                select(ContentCategory)
                .where(ContentCategory.is_active == True)
                .order_by(ContentCategory.level, ContentCategory.sort_order)
            )
            categories = result.scalars().all()
            
            # 构建树结构
            category_dict = {}
            root_categories = []
            
            for category in categories:
                category_data = {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "level": category.level,
                    "icon": category.icon,
                    "color": category.color,
                    "content_count": category.content_count,
                    "children": []
                }
                category_dict[category.id] = category_data
                
                if category.parent_id is None:
                    root_categories.append(category_data)
                else:
                    parent = category_dict.get(category.parent_id)
                    if parent:
                        parent["children"].append(category_data)
            
            return root_categories
            
        except Exception as e:
            Logger.error(f"获取分类树结构失败: {str(e)}")
            raise

    # ==================== 高级搜索 ====================

    async def advanced_search(self, search_request: SearchRequest) -> SearchResponse:
        """高级搜索功能"""
        try:
            start_time = datetime.now()

            # 构建搜索查询
            query = select(SearchIndex).where(SearchIndex.is_active == True)

            # 文本搜索
            if search_request.query:
                search_terms = search_request.query.split()
                for term in search_terms:
                    query = query.where(
                        or_(
                            SearchIndex.title.ilike(f"%{term}%"),
                            SearchIndex.content.ilike(f"%{term}%"),
                            SearchIndex.keywords.ilike(f"%{term}%")
                        )
                    )

            # 内容类型过滤
            if search_request.content_types:
                query = query.where(SearchIndex.content_type.in_(search_request.content_types))

            # 日期过滤
            if search_request.date_from:
                query = query.where(SearchIndex.created_at >= search_request.date_from)
            if search_request.date_to:
                query = query.where(SearchIndex.created_at <= search_request.date_to)

            # 计算总数
            count_result = await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
            total_count = count_result.scalar() or 0

            # 排序
            if search_request.sort_by == "relevance":
                query = query.order_by(desc(SearchIndex.boost_score))
            elif search_request.sort_by == "date":
                if search_request.sort_order == "desc":
                    query = query.order_by(desc(SearchIndex.created_at))
                else:
                    query = query.order_by(asc(SearchIndex.created_at))
            elif search_request.sort_by == "title":
                if search_request.sort_order == "desc":
                    query = query.order_by(desc(SearchIndex.title))
                else:
                    query = query.order_by(asc(SearchIndex.title))

            # 分页
            offset = (search_request.page - 1) * search_request.page_size
            query = query.offset(offset).limit(search_request.page_size)

            # 执行查询
            result = await self.db.execute(query)
            search_indexes = result.scalars().all()

            # 构建搜索结果
            results = []
            for index in search_indexes:
                # 生成摘要
                snippet = self._generate_snippet(index.content, search_request.query)

                # 计算相关性分数
                score = self._calculate_relevance_score(index, search_request.query)

                results.append(SearchResult(
                    content_type=index.content_type,
                    content_id=index.content_id,
                    title=index.title or "",
                    snippet=snippet,
                    score=score,
                    metadata=index.meta_data,
                    url=f"/{index.content_type}/{index.content_id}"
                ))

            # 计算总页数
            total_pages = (total_count + search_request.page_size - 1) // search_request.page_size

            # 计算搜索耗时
            search_time = (datetime.now() - start_time).total_seconds()

            return SearchResponse(
                query=search_request.query,
                total_count=total_count,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=total_pages,
                results=results,
                search_time=search_time
            )

        except Exception as e:
            Logger.error(f"高级搜索失败: {str(e)}")
            raise

    def _generate_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """生成搜索摘要"""
        if not content or not query:
            return content[:max_length] if content else ""

        # 查找查询词在内容中的位置
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            return content[:max_length]

        # 以查询词为中心生成摘要
        start = max(0, pos - max_length // 2)
        end = min(len(content), start + max_length)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _calculate_relevance_score(self, index: SearchIndex, query: str) -> float:
        """计算相关性分数"""
        score = index.boost_score

        if query and index.title:
            # 标题匹配加分
            if query.lower() in index.title.lower():
                score += 2.0

        if query and index.keywords:
            # 关键词匹配加分
            if query.lower() in index.keywords.lower():
                score += 1.5

        return round(score, 2)

    # ==================== 数据导出 ====================

    async def create_export_task(
        self,
        export_request: DataExportRequest,
        created_by: int
    ) -> DataExportResponse:
        """创建数据导出任务"""
        try:
            task = DataExportTask(
                name=export_request.name,
                export_type=export_request.export_type,
                data_type=export_request.data_type,
                filters=export_request.filters,
                format=export_request.format,
                created_by=created_by,
                expires_at=datetime.now() + timedelta(days=7)  # 7天后过期
            )

            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)

            # 异步执行导出任务
            asyncio.create_task(self._execute_export_task(task.id))

            return DataExportResponse(
                id=task.id,
                name=task.name,
                export_type=task.export_type,
                data_type=task.data_type,
                filters=task.filters,
                format=task.format,
                status=task.status,
                progress=task.progress,
                total_records=task.total_records,
                exported_records=task.exported_records,
                file_path=task.file_path,
                file_size=task.file_size,
                download_url=task.download_url,
                expires_at=task.expires_at,
                error_message=task.error_message,
                started_at=task.started_at,
                completed_at=task.completed_at,
                created_at=task.created_at,
                created_by=task.created_by
            )

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建数据导出任务失败: {str(e)}")
            raise

    async def _execute_export_task(self, task_id: int):
        """执行数据导出任务"""
        from app.models.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                task = await db.get(DataExportTask, task_id)
                if not task:
                    return

                task.status = "running"
                task.started_at = datetime.now()
                await db.commit()

                # 生成文件路径
                filename = f"{task.name}_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{task.format}"
                file_path = os.path.join("exports", filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # 根据数据类型导出数据
                if task.data_type == "knowledge_bases":
                    await self._export_knowledge_bases(db, task, file_path)
                elif task.data_type == "documents":
                    await self._export_documents(db, task, file_path)
                elif task.data_type == "users":
                    await self._export_users(db, task, file_path)

                # 更新任务状态
                task.status = "completed"
                task.completed_at = datetime.now()
                task.file_path = file_path
                task.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                task.download_url = f"/api/v1/admin/content/exports/{task.id}/download"
                task.progress = 100

                await db.commit()

                Logger.info(f"数据导出任务完成: {task.name}")

            except Exception as e:
                task.status = "failed"
                task.error_message = str(e)
                await db.commit()
                Logger.error(f"执行数据导出任务失败: {str(e)}")

    async def _export_knowledge_bases(self, db: AsyncSession, task: DataExportTask, file_path: str):
        """导出知识库数据"""
        try:
            query = select(KnowledgeBase)

            # 应用过滤条件
            if task.filters:
                if "status" in task.filters:
                    query = query.where(KnowledgeBase.status.in_(task.filters["status"]))
                if "created_from" in task.filters:
                    query = query.where(KnowledgeBase.created_at >= task.filters["created_from"])
                if "created_to" in task.filters:
                    query = query.where(KnowledgeBase.created_at <= task.filters["created_to"])

            # 计算总记录数
            count_result = await db.execute(select(func.count()).select_from(query.subquery()))
            task.total_records = count_result.scalar() or 0
            await db.commit()

            # 分批导出数据
            batch_size = 1000
            offset = 0

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = None

                while True:
                    batch_query = query.offset(offset).limit(batch_size)
                    result = await db.execute(batch_query)
                    knowledge_bases = result.scalars().all()

                    if not knowledge_bases:
                        break

                    for kb in knowledge_bases:
                        row_data = {
                            "id": kb.id,
                            "name": kb.name,
                            "description": kb.description,
                            "status": kb.status,
                            "created_at": kb.created_at.isoformat() if kb.created_at else "",
                            "updated_at": kb.updated_at.isoformat() if kb.updated_at else "",
                            "created_by": kb.created_by
                        }

                        if writer is None:
                            writer = csv.DictWriter(csvfile, fieldnames=row_data.keys())
                            writer.writeheader()

                        writer.writerow(row_data)
                        task.exported_records += 1

                    # 更新进度
                    task.progress = int(task.exported_records / task.total_records * 100)
                    await db.commit()

                    offset += batch_size

        except Exception as e:
            Logger.error(f"导出知识库数据失败: {str(e)}")
            raise

    async def _export_documents(self, db: AsyncSession, task: DataExportTask, file_path: str):
        """导出文档数据"""
        try:
            query = select(Document)

            # 应用过滤条件
            if task.filters:
                if "status" in task.filters:
                    query = query.where(Document.status.in_(task.filters["status"]))
                if "created_from" in task.filters:
                    query = query.where(Document.created_at >= task.filters["created_from"])
                if "created_to" in task.filters:
                    query = query.where(Document.created_at <= task.filters["created_to"])

            # 计算总记录数
            count_result = await db.execute(select(func.count()).select_from(query.subquery()))
            task.total_records = count_result.scalar() or 0
            await db.commit()

            # 分批导出数据
            batch_size = 1000
            offset = 0

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = None

                while True:
                    batch_query = query.offset(offset).limit(batch_size)
                    result = await db.execute(batch_query)
                    documents = result.scalars().all()

                    if not documents:
                        break

                    for doc in documents:
                        row_data = {
                            "id": doc.id,
                            "filename": doc.filename,
                            "file_type": doc.file_type,
                            "file_size": doc.file_size,
                            "status": doc.status,
                            "knowledge_base_id": doc.knowledge_base_id,
                            "created_at": doc.created_at.isoformat() if doc.created_at else "",
                            "updated_at": doc.updated_at.isoformat() if doc.updated_at else ""
                        }

                        if writer is None:
                            writer = csv.DictWriter(csvfile, fieldnames=row_data.keys())
                            writer.writeheader()

                        writer.writerow(row_data)
                        task.exported_records += 1

                    # 更新进度
                    task.progress = int(task.exported_records / task.total_records * 100)
                    await db.commit()

                    offset += batch_size

        except Exception as e:
            Logger.error(f"导出文档数据失败: {str(e)}")
            raise

    async def _export_users(self, db: AsyncSession, task: DataExportTask, file_path: str):
        """导出用户数据"""
        try:
            query = select(User)

            # 应用过滤条件
            if task.filters:
                if "is_active" in task.filters:
                    query = query.where(User.is_active == task.filters["is_active"])
                if "created_from" in task.filters:
                    query = query.where(User.created_at >= task.filters["created_from"])
                if "created_to" in task.filters:
                    query = query.where(User.created_at <= task.filters["created_to"])

            # 计算总记录数
            count_result = await db.execute(select(func.count()).select_from(query.subquery()))
            task.total_records = count_result.scalar() or 0
            await db.commit()

            # 分批导出数据
            batch_size = 1000
            offset = 0

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = None

                while True:
                    batch_query = query.offset(offset).limit(batch_size)
                    result = await db.execute(batch_query)
                    users = result.scalars().all()

                    if not users:
                        break

                    for user in users:
                        row_data = {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "full_name": user.full_name,
                            "is_active": user.is_active,
                            "is_superuser": user.is_superuser,
                            "created_at": user.created_at.isoformat() if user.created_at else "",
                            "last_login": user.last_login.isoformat() if user.last_login else ""
                        }

                        if writer is None:
                            writer = csv.DictWriter(csvfile, fieldnames=row_data.keys())
                            writer.writeheader()

                        writer.writerow(row_data)
                        task.exported_records += 1

                    # 更新进度
                    task.progress = int(task.exported_records / task.total_records * 100)
                    await db.commit()

                    offset += batch_size

        except Exception as e:
            Logger.error(f"导出用户数据失败: {str(e)}")
            raise

    # ==================== 内容仪表板 ====================

    async def get_content_dashboard(self) -> ContentDashboardResponse:
        """获取内容管理仪表板数据"""
        try:
            # 总内容数（知识库 + 文档）
            kb_count_result = await self.db.execute(select(func.count(KnowledgeBase.id)))
            doc_count_result = await self.db.execute(select(func.count(Document.id)))
            total_content = (kb_count_result.scalar() or 0) + (doc_count_result.scalar() or 0)

            # 已发布内容数
            published_kb_result = await self.db.execute(
                select(func.count(KnowledgeBase.id)).where(KnowledgeBase.status == "published")
            )
            published_doc_result = await self.db.execute(
                select(func.count(Document.id)).where(Document.status == "processed")
            )
            published_content = (published_kb_result.scalar() or 0) + (published_doc_result.scalar() or 0)

            # 待审核内容数
            pending_kb_result = await self.db.execute(
                select(func.count(KnowledgeBase.id)).where(KnowledgeBase.status == "pending")
            )
            pending_doc_result = await self.db.execute(
                select(func.count(Document.id)).where(Document.status == "pending")
            )
            pending_moderation = (pending_kb_result.scalar() or 0) + (pending_doc_result.scalar() or 0)

            # 总分类数
            categories_result = await self.db.execute(
                select(func.count(ContentCategory.id)).where(ContentCategory.is_active == True)
            )
            total_categories = categories_result.scalar() or 0

            # 总标签数
            tags_result = await self.db.execute(
                select(func.count(ContentTag.id)).where(ContentTag.is_active == True)
            )
            total_tags = tags_result.scalar() or 0

            # 活跃批量操作数
            active_operations_result = await self.db.execute(
                select(func.count(BulkOperation.id)).where(BulkOperation.status.in_(["pending", "running"]))
            )
            active_bulk_operations = active_operations_result.scalar() or 0

            # 最近审核日志
            recent_logs_result = await self.db.execute(
                select(ContentModerationLog)
                .order_by(desc(ContentModerationLog.created_at))
                .limit(10)
            )
            recent_moderation_logs = [
                ContentModerationLogResponse(
                    id=log.id,
                    content_type=log.content_type,
                    content_id=log.content_id,
                    rule_id=log.rule_id,
                    moderator_id=log.moderator_id,
                    action=log.action,
                    reason=log.reason,
                    details=log.details,
                    confidence_score=log.confidence_score,
                    is_automated=log.is_automated,
                    previous_status=log.previous_status,
                    new_status=log.new_status,
                    created_at=log.created_at
                ) for log in recent_logs_result.scalars().all()
            ]

            # 按状态统计内容
            kb_status_result = await self.db.execute(
                select(KnowledgeBase.status, func.count(KnowledgeBase.id))
                .group_by(KnowledgeBase.status)
            )
            doc_status_result = await self.db.execute(
                select(Document.status, func.count(Document.id))
                .group_by(Document.status)
            )

            content_by_status = {}
            for status, count in kb_status_result.fetchall():
                content_by_status[f"kb_{status}"] = count
            for status, count in doc_status_result.fetchall():
                content_by_status[f"doc_{status}"] = count

            # 按类型统计内容
            content_by_type = {
                "knowledge_bases": kb_count_result.scalar() or 0,
                "documents": doc_count_result.scalar() or 0
            }

            # 热门分类
            top_categories_result = await self.db.execute(
                select(ContentCategory.name, ContentCategory.content_count)
                .where(ContentCategory.is_active == True)
                .order_by(desc(ContentCategory.content_count))
                .limit(5)
            )
            top_categories = [
                {"name": name, "count": count}
                for name, count in top_categories_result.fetchall()
            ]

            # 热门标签
            top_tags_result = await self.db.execute(
                select(ContentTag.name, ContentTag.usage_count)
                .where(ContentTag.is_active == True)
                .order_by(desc(ContentTag.usage_count))
                .limit(5)
            )
            top_tags = [
                {"name": name, "count": count}
                for name, count in top_tags_result.fetchall()
            ]

            return ContentDashboardResponse(
                total_content=total_content,
                published_content=published_content,
                pending_moderation=pending_moderation,
                total_categories=total_categories,
                total_tags=total_tags,
                active_bulk_operations=active_bulk_operations,
                recent_moderation_logs=recent_moderation_logs,
                content_by_status=content_by_status,
                content_by_type=content_by_type,
                top_categories=top_categories,
                top_tags=top_tags
            )

        except Exception as e:
            Logger.error(f"获取内容管理仪表板数据失败: {str(e)}")
            raise

    # ==================== 批量标签操作 ====================

    async def batch_tag_operation(
        self,
        operation: BatchTagOperation,
        operator_id: int
    ) -> Dict[str, Any]:
        """批量标签操作"""
        try:
            results = {
                "total": len(operation.content_ids),
                "success": 0,
                "failed": 0,
                "errors": []
            }

            for content_id in operation.content_ids:
                try:
                    # 这里需要根据具体的内容类型实现标签操作
                    # 由于没有具体的内容-标签关联表，这里只是示例

                    if operation.operation == "add":
                        # 添加标签逻辑
                        pass
                    elif operation.operation == "remove":
                        # 移除标签逻辑
                        pass
                    elif operation.operation == "replace":
                        # 替换标签逻辑
                        pass

                    results["success"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": content_id,
                        "error": str(e)
                    })

            await self.db.commit()
            return results

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"批量标签操作失败: {str(e)}")
            raise

    # ==================== 搜索索引管理 ====================

    async def update_search_index(
        self,
        content_type: str,
        content_id: int,
        title: str,
        content: str,
        keywords: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """更新搜索索引"""
        try:
            # 查找现有索引
            existing_result = await self.db.execute(
                select(SearchIndex)
                .where(SearchIndex.content_type == content_type)
                .where(SearchIndex.content_id == content_id)
            )
            existing_index = existing_result.scalar_one_or_none()

            if existing_index:
                # 更新现有索引
                existing_index.title = title
                existing_index.content = content
                existing_index.keywords = keywords
                existing_index.metadata = metadata
                existing_index.last_indexed = datetime.now()
                existing_index.updated_at = datetime.now()
            else:
                # 创建新索引
                new_index = SearchIndex(
                    content_type=content_type,
                    content_id=content_id,
                    title=title,
                    content=content,
                    keywords=keywords,
                    metadata=metadata
                )
                self.db.add(new_index)

            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"更新搜索索引失败: {str(e)}")
            raise

    async def delete_search_index(self, content_type: str, content_id: int):
        """删除搜索索引"""
        try:
            await self.db.execute(
                delete(SearchIndex)
                .where(SearchIndex.content_type == content_type)
                .where(SearchIndex.content_id == content_id)
            )
            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"删除搜索索引失败: {str(e)}")
            raise
