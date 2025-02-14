import crontab
from huey import RedisHuey
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase, TrainingStatus
from app.models.document import Document
from app.utils.session import SessionManager
from app.models.database import AsyncSessionLocal
from sqlalchemy import select

# 修改为从huey导入crontab
from huey import crontab
from huey import RedisHuey

# 初始化Huey实例
from app.core.config import settings

huey = RedisHuey('knowledge-base-training',
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD)

@huey.task()
def train_knowledge_base(kb_id: int):
    """异步训练知识库任务

    Args:
        kb_id (int): 知识库ID
    """
    async def _train():
        async with AsyncSessionLocal() as db:
            try:
                # 获取知识库
                kb = (await db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )).scalar_one_or_none()
                
                if not kb:
                    return

                # 获取知识库的所有未删除文档
                documents = (await db.execute(
                    select(Document).filter(
                        Document.knowledge_base_id == kb_id,
                        Document.is_deleted == False
                    )
                )).scalars().all()

                if not documents:
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = "No documents available for training"
                    await db.commit()
                    return

                try:
                    # 获取会话并开始训练
                    session_manager = SessionManager()
                    # 使用同步方式获取会话
                    session = session_manager.get_session_sync(
                        str(kb_id),
                        kb.llm_config
                    )
                    
                    # 更新训练状态
                    kb.training_status = TrainingStatus.TRAINING
                    kb.training_started_at = datetime.now()
                    kb.training_error = None
                    await db.commit()
                    
                    # 准备文档内容和元数据
                    doc_contents = [doc.content for doc in documents]
                    doc_metadata = [doc.metadata for doc in documents] if hasattr(Document, 'metadata') else None
                    
                    # 使用同步方式处理所有文档
                    # TODO: 训练的结果处理逻辑
                    entity_count, relation_count, chunk_count = session.train_sync(
                        documents=doc_contents,
                        metadata=doc_metadata
                    )
                    
                    # 训练完成后更新状态
                    kb.training_status = TrainingStatus.TRAINED
                    kb.training_finished_at = datetime.now()
                    kb.training_error = None

                except Exception as e:
                    # 训练失败时更新状态
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = str(e)

                finally:
                    await db.commit()

            except Exception as e:
                await db.rollback()
                raise e

    import asyncio
    asyncio.run(_train())

@huey.periodic_task(crontab(minute='*/1'))
def check_queued_knowledge_bases():
    """定期检查排队中的知识库，并启动训练"""
    async def _check():
        async with AsyncSessionLocal() as db:
            try:
                # 检查是否有正在训练的知识库
                training_kb = (await db.execute(
                    select(KnowledgeBase).filter(
                        KnowledgeBase.training_status == TrainingStatus.TRAINING
                    )
                )).scalar_one_or_none()

                if not training_kb:
                    # 获取最早排队的知识库
                    queued_kb = (await db.execute(
                        select(KnowledgeBase).filter(
                            KnowledgeBase.training_status == TrainingStatus.QUEUED
                        ).order_by(KnowledgeBase.queued_at)
                    )).scalar_one_or_none()

                    if queued_kb:
                        # 更新状态为训练中
                        queued_kb.training_status = TrainingStatus.TRAINING
                        queued_kb.training_started_at = datetime.now()
                        queued_kb.training_error = None
                        queued_kb.queued_at = None
                        await db.commit()
                        
                        # 启动训练任务
                        train_knowledge_base(queued_kb.id)

            except Exception as e:
                await db.rollback()
                raise e

    import asyncio
    asyncio.run(_check())