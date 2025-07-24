from datetime import datetime, timedelta
from app.models.knowledge_base import KnowledgeBase, TrainingStatus
from app.models.document import Document
from app.utils.session import SessionManager
from app.models.database import AsyncSessionLocal
from sqlalchemy import select
from app.core.logger import Logger
from app.core.redis_manager import redis_manager
from app.rag.training.training_manager import RAGTrainingManager, TrainingResult

# 从huey导入crontab
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
    Logger.info(f"train_knowledge_base: {kb_id}")
    
    async def _train():
        Logger.info(f"开始异步训练任务，知识库ID: {kb_id}")
        async with AsyncSessionLocal() as db:
            try:
                # 创建训练管理器
                training_manager = RAGTrainingManager(db)
                
                # 执行训练
                result = await training_manager.train(kb_id)
                
                # 创建审计管理器
                from app.services.audit import AuditManager
                from app.schemas.identity import UserContext, UserType
                
                audit_manager = AuditManager(db)
                
                # 创建系统用户上下文
                system_context = UserContext(
                    user_type=UserType.SYSTEM,
                    user_id=0,
                    identity_id=None,
                    client_id=None
                )
                
                # 计算训练时间
                kb = (await db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )).scalar_one_or_none()
                
                training_duration = None
                if kb and kb.training_started_at:
                    training_duration = (datetime.now() - kb.training_started_at).total_seconds()
                
                if not result.success:
                    Logger.error(f"训练知识库 {kb_id} 失败: {result.error_message}")
                    # 更新知识库状态
                    await training_manager.update_training_status(
                        kb_id, 
                        TrainingStatus.FAILED, 
                        result.error_message
                    )
                    
                    # 记录审计日志
                    await audit_manager.log_training(
                        user_context=system_context,
                        kb_id=kb_id,
                        status="failed",
                        document_count=result.document_count,
                        chunk_count=result.chunk_count,
                        embedding_count=result.embedding_count,
                        duration=training_duration,
                        error=result.error_message
                    )
                else:
                    Logger.info(f"知识库 {kb_id} 训练成功，处理了 {result.document_count} 个文档，"
                               f"生成了 {result.chunk_count} 个分块和 {result.embedding_count} 个向量")
                    
                    # 记录审计日志
                    await audit_manager.log_training(
                        user_context=system_context,
                        kb_id=kb_id,
                        status="completed",
                        document_count=result.document_count,
                        chunk_count=result.chunk_count,
                        embedding_count=result.embedding_count,
                        duration=training_duration
                    )
                    
            except Exception as e:
                Logger.error(f"训练知识库 {kb_id} 时发生意外错误: {str(e)}")
                # 更新知识库状态
                kb = (await db.execute(
                    select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
                )).scalar_one_or_none()
                
                if kb:
                    kb.training_status = TrainingStatus.FAILED
                    kb.training_error = f"训练失败: {str(e)}"
                    await db.commit()

    import asyncio
    Logger.info(f"启动知识库 {kb_id} 的训练任务")
    asyncio.run(_train())

@huey.periodic_task(crontab(minute='*/1'))
def check_queued_knowledge_bases():
    """定期检查排队中的知识库，并启动训练"""
    async def _check():
        Logger.info("检查排队中的知识库")
        async with AsyncSessionLocal() as db:
            try:
                # 创建训练管理器
                training_manager = RAGTrainingManager(db)
                
                # 检查队列
                next_kb_id = await training_manager.check_queue()
                
                if next_kb_id:
                    Logger.info(f"找到下一个要训练的知识库: {next_kb_id}")
                    
                    # 更新状态为训练中
                    await training_manager.update_training_status(
                        next_kb_id,
                        TrainingStatus.TRAINING
                    )
                    
                    # 启动训练任务
                    train_knowledge_base(next_kb_id)
                else:
                    Logger.info("没有排队中的知识库")

            except Exception as e:
                Logger.error(f"检查训练队列时发生错误: {str(e)}")
                await db.rollback()

    import asyncio
    asyncio.run(_check())