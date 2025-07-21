from tests.utils.decorators import step_decorator
from tests.utils.test_state import TestState
from fastapi.testclient import TestClient


@step_decorator("create_knowledge_base")
async def step_create_knowledge_base(state: TestState, client: TestClient):
    """创建知识库"""
    user_token = state.get_step_data("user_token")
    response = client.post(
        "/api/v1/admin/knowledge-bases",
        json={
            "name": "测试知识库",
            "domain": "测试领域",
            "example_queries": ["问题1", "问题2"],
            "entity_types": ["实体1", "实体2"],
            "llm_config": {
                "llm": {
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "api_key": "test-api-key"
                },
                "embeddings": {
                    "model": "BAAI/bge-m3",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "api_key": "test-api-key",
                    "embedding_dim": 1024
                }
            }
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("kb_id", response.json()["data"]["id"])
    return response.json()


@step_decorator("get_kb_members")
async def step_get_kb_members(state: TestState, client: TestClient):
    """获取知识库成员列表"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    members = response.json()["data"]["members"]
    # 验证初始只有创建者一个成员
    assert len(members) == 1
    assert members[0]["is_owner"] == True
    assert members[0]["permission"] == "owner"
    return response.json()


@step_decorator("add_member_to_kb")
async def step_add_member_to_kb(state: TestState, client: TestClient):
    """添加成员到知识库"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    another_user_id = state.get_step_data("another_user_id")
    
    # 添加成员
    response = client.post(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members",
        json={
            "user_id": another_user_id,
            "permission": "editor"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    
    # 验证成员列表
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    members = response.json()["data"]["members"]
    assert len(members) == 2
    editor = next(m for m in members if m["id"] == another_user_id)
    assert editor["permission"] == "editor"
    assert not editor["is_owner"]
    return response.json()


@step_decorator("train_knowledge_base")
async def step_train_knowledge_base(state: TestState, client: TestClient):
    """训练知识库"""
   
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    
    # 开始训练
    response = client.post(
        f"/api/v1/admin/knowledge-bases/{kb_id}/train",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    
    # 直接执行训练任务的内部逻辑
    from app.utils.tasks import train_knowledge_base
    from app.models.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.knowledge_base import KnowledgeBase
    from app.models.document import Document
    from app.utils.session import SessionManager
    from datetime import datetime, timedelta
    from app.core.logger import Logger
    from app.core.config import settings
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取知识库
            result = await db.execute(
                select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
            )
            kb = result.scalars().first()
            
            if not kb:
                raise AssertionError(f"知识库 {kb_id} 不存在")

            # 获取知识库的所有未删除文档
            result = await db.execute(
                select(Document).filter(
                    Document.knowledge_base_id == kb_id,
                    Document.is_deleted == False
                )
            )
            documents = result.scalars().all()

            if not documents:
                raise AssertionError("没有可用于训练的文档")

            # 获取会话并开始训练
            session_manager = SessionManager(db)
            Logger.info("Creating session manager")
            
            grag = await session_manager.get_session(str(kb_id), settings.DEFAULT_LLM_CONFIG)
            Logger.info("Session created successfully")
            
            # 更新训练状态
            kb.training_status = "training"
            kb.training_started_at = datetime.now()
            kb.training_error = None
            await db.commit()
            Logger.info("Training status updated")
            
            # 准备文档内容和元数据
            doc_contents = [doc.content for doc in documents]
            doc_metadata = [{"id": doc.id, "title": doc.title} for doc in documents]
            
            Logger.info(f"Starting training with {len(documents)} documents")
            
            try:
                # 使用同步方式处理所有文档
                entity_count, relation_count, chunk_count = await grag.async_insert(
                    content=doc_contents,
                    metadata=doc_metadata,
                    show_progress=True
                )
                Logger.info(f"Training completed with {entity_count} entities, {relation_count} relations, {chunk_count} chunks")
            except Exception as e:
                Logger.error(f"Training failed with error: {str(e)}")
                raise
            
            # 训练完成后更新状态
            kb.training_status = "trained"
            kb.training_finished_at = datetime.now()
            kb.training_error = None
            await db.commit()
            
        except Exception as e:
            Logger.error(f"Training failed: {str(e)}")
            kb.training_status = "failed"
            kb.training_error = str(e)
            await db.commit()
            raise AssertionError(f"知识库训练失败: {str(e)}")
    
    return response.json() 