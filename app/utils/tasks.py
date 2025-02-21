import crontab
from huey import RedisHuey
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase, TrainingStatus
from app.models.document import Document
from app.utils.session import SessionManager
from app.models.database import AsyncSessionLocal
from sqlalchemy import select
from app.core.logger import Logger
from app.core.redis_manager import redis_manager

# 修改为从huey导入crontab
from huey import crontab
from huey import RedisHuey

# 初始化Huey实例
from app.core.config import settings

huey = RedisHuey(
    'knowledge-base-training',
    connection_pool=redis_manager._redis.connection_pool if redis_manager._redis else None
)

@huey.task()
def train_knowledge_base(kb_id: int):
    """异步训练知识库任务

    Args:
        kb_id (int): 知识库ID
    """
    async def _train():
        Logger.info(f"Starting async training task for knowledge base {kb_id}")
        async with AsyncSessionLocal() as db:
            try:
                # 获取知识库
                kb = (await db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )).scalar_one_or_none()
                
                if not kb:
                    Logger.error(f"Training task failed: Knowledge base {kb_id} not found")
                    return

                # 获取知识库的所有未删除文档
                documents = (await db.execute(
                    select(Document).filter(
                        Document.knowledge_base_id == kb_id,
                        Document.is_deleted == False
                    )
                )).scalars().all()

                if not documents:
                    Logger.error(f"Training task failed: No documents available for knowledge base {kb_id}")
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = "没有可用于训练的文档"
                    await db.commit()
                    return

                Logger.info(f"Processing {len(documents)} documents for knowledge base {kb_id}")

                try:
                    # 获取会话并开始训练
                    session_manager = SessionManager(db)
                    grag = session_manager.get_session(str(kb_id), kb.llm_config)
                    
                    # 更新训练状态
                    kb.training_status = TrainingStatus.TRAINING
                    kb.training_started_at = datetime.now()
                    kb.training_error = None
                    await db.commit()
                    
                    # 准备文档内容和元数据
                    doc_contents = [doc.content for doc in documents]
                    doc_metadata = [{"id": doc.id, "title": doc.title} for doc in documents]
                    
                    Logger.info(f"Starting training process for knowledge base {kb_id}")
                    
                    # 设置训练超时时间（默认30分钟）
                    timeout = datetime.now() + timedelta(minutes=30)
                    
                    # 使用同步方式处理所有文档
                    entity_count, relation_count, chunk_count = await grag.async_insert(
                        content=doc_contents,
                        metadata=doc_metadata,
                        show_progress=True
                    )
                    
                    # 检查是否超时
                    if datetime.now() > timeout:
                        raise TimeoutError("训练任务超时")
                    
                    # 训练完成后更新状态
                    kb.training_status = TrainingStatus.TRAINED
                    kb.training_finished_at = datetime.now()
                    kb.training_error = None
                    
                    Logger.info(f"Training completed for knowledge base {kb_id}: {entity_count} entities, {relation_count} relations, {chunk_count} chunks")

                except TimeoutError as e:
                    Logger.error(f"Training task timeout for knowledge base {kb_id}")
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = "训练任务超时"
                    
                except Exception as e:
                    # 训练失败时更新状态
                    Logger.error(f"Training task failed for knowledge base {kb_id}: {str(e)}")
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = f"训练失败: {str(e)}"

                finally:
                    await db.commit()

            except Exception as e:
                Logger.error(f"Unexpected error during training task for knowledge base {kb_id}: {str(e)}")
                await db.rollback()
                raise e

    import asyncio
    asyncio.run(_train())

@huey.periodic_task(crontab(minute='*/1'))
def check_queued_knowledge_bases():
    """定期检查排队中的知识库，并启动训练"""
    async def _check():
        Logger.debug("Checking queued knowledge bases")
        async with AsyncSessionLocal() as db:
            try:
                # 检查是否有正在训练的知识库
                training_kb = (await db.execute(
                    select(KnowledgeBase).filter(
                        KnowledgeBase.training_status == TrainingStatus.TRAINING
                    )
                )).scalar_one_or_none()

                if not training_kb:
                    # 获取下一个待训练的知识库ID
                    next_kb_id = await redis_manager.get_next_training_task()
                    if next_kb_id:
                        # 获取知识库信息
                        queued_kb = (await db.execute(
                            select(KnowledgeBase).filter(
                                KnowledgeBase.id == next_kb_id
                            )
                        )).scalar_one_or_none()

                        if queued_kb:
                            Logger.info(f"Starting training for queued knowledge base {queued_kb.id}")
                            # 更新状态为训练中
                            queued_kb.training_status = TrainingStatus.TRAINING
                            queued_kb.training_started_at = datetime.now()
                            queued_kb.training_error = None
                            queued_kb.queued_at = None
                            await db.commit()
                            
                            # 启动训练任务
                            train_knowledge_base(queued_kb.id)

            except Exception as e:
                Logger.error(f"Error checking queued knowledge bases: {str(e)}")
                await db.rollback()
                raise e

    import asyncio
    asyncio.run(_check())