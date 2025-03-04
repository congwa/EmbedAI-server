import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from main import app
from app.models.database import engine, Base
from .utils.test_state import TestState
from .utils.decorators import step_decorator
from fastapi import WebSocket
from app.models.enums import ChatMode, TrainingStatus
from .test_knowledge_base_flow import (
    step_create_admin,
    step_admin_login,
    step_create_normal_user,
    step_user_login,
    step_create_knowledge_base,
    setup_database
)
from .test_document_flow import step_create_document
import pytest_asyncio
import asyncio

@pytest.fixture(scope="session")
def state() -> Generator[TestState, None, None]:
    """测试状态管理器"""
    yield TestState("chat_flow")

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """测试客户端"""
    yield TestClient(app)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_data(state: TestState, client: TestClient) -> AsyncGenerator[None, None]:
    """设置测试数据"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    state.reset()
    yield

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
            kb.training_status = TrainingStatus.TRAINING
            kb.training_started_at = datetime.now()
            kb.training_error = None
            await db.commit()
            Logger.info("Training status updated")
            
            # 准备文档内容和元数据
            doc_contents = [doc.content for doc in documents]
            doc_metadata = [{"id": doc.id, "title": doc.title} for doc in documents]
            
            Logger.info(f"Starting training with {len(documents)} documents")
            Logger.info(f"Document contents: {doc_contents}")
            Logger.info(f"Document metadata: {doc_metadata}")
            
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
                Logger.error(f"Error type: {type(e)}")
                import traceback
                Logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            # 训练完成后更新状态
            kb.training_status = TrainingStatus.TRAINED
            kb.training_finished_at = datetime.now()
            kb.training_error = None
            await db.commit()
            
        except Exception as e:
            Logger.error(f"Training failed: {str(e)}")
            kb.training_status = TrainingStatus.FAILED
            kb.training_error = str(e)
            await db.commit()
            raise AssertionError(f"知识库训练失败: {str(e)}")
    
    # 等待训练完成
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        print('response.json()["data"]检查状态结果: ', response.json()["data"])
        # 检查训练状态
        training_status = response.json()["data"]["training_status"]
        if training_status == TrainingStatus.TRAINED:
            break
        elif training_status == TrainingStatus.FAILED:
            raise AssertionError(f"知识库训练失败: {response.json()['data'].get('training_error', '未知错误')}")
            
        retry_count += 1
        await asyncio.sleep(2)  # 缩短等待时间，避免测试时间过长
    
    assert retry_count < max_retries, "知识库训练超时"
    return response.json()

@step_decorator("create_chat")
async def step_create_chat(state: TestState, client: TestClient):
    """创建聊天会话"""
    # 写死三方用户 ID
    state.save_step_data("third_party_user_id", "1234567890")
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    response = client.post(
        "/api/v1/admin/chats",
        json={
            "knowledge_base_id": kb_id,
            "third_party_user_id": third_party_user_id,
            "chat_mode": ChatMode.AI
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("chat_id", response.json()["data"]["id"])
    return response.json()

@step_decorator("connect_websocket")
async def step_connect_websocket(state: TestState, client: TestClient):
    """连接WebSocket并进行多轮对话测试"""
    chat_id = state.get_step_data("chat_id")
    client_id = "test_client"
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    with client.websocket_connect(
        f"/api/v1/ws/chat/{chat_id}?client_id={client_id}&third_party_user_id={third_party_user_id}"
    ) as websocket:
        # 发送心跳
        await websocket.send_json({"type": "ping"})
        response = await websocket.receive_json()
        assert response["type"] == "pong"
        
        # 第一轮对话
        await websocket.send_json({
            "content": "你好，这是第一条测试消息"
        })
        
        # 接收用户消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "你好，这是第一条测试消息"
        
        # 接收AI回复
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["message_type"] == "assistant"
        
        # 第二轮对话
        await websocket.send_json({
            "content": "请问你是谁？"
        })
        
        # 接收用户消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "请问你是谁？"
        
        # 接收AI回复
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["message_type"] == "assistant"
        
        # 第三轮对话
        await websocket.send_json({
            "content": "你能帮我做什么？"
        })
        
        # 接收用户消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "你能帮我做什么？"
        
        # 接收AI回复
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["message_type"] == "assistant"

@step_decorator("connect_admin_websocket")
async def step_connect_admin_websocket(state: TestState, client: TestClient):
    """管理员连接WebSocket并进行多轮对话测试"""
    chat_id = state.get_step_data("chat_id")
    client_id = "admin_client"
    admin_id = state.get_step_data("admin_id")
    
    with client.websocket_connect(
        f"/api/v1/ws/chat/admin/{chat_id}?client_id={client_id}&admin_id={admin_id}"
    ) as websocket:
        # 发送心跳
        await websocket.send_json({"type": "ping"})
        response = await websocket.receive_json()
        assert response["type"] == "pong"
        
        # 第一轮管理员回复
        await websocket.send_json({
            "content": "你好，我是客服，有什么可以帮你？"
        })
        
        # 接收消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "你好，我是客服，有什么可以帮你？"
        assert response["data"]["message_type"] == "admin"
        
        # 第二轮管理员回复
        await websocket.send_json({
            "content": "我们的系统可以帮助你解答问题"
        })
        
        # 接收消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "我们的系统可以帮助你解答问题"
        assert response["data"]["message_type"] == "admin"

@pytest.mark.asyncio
async def test_chat_flow(state: TestState, client: TestClient):
    """测试聊天功能流程"""
    # 创建并登录管理员
    await step_create_admin(state, client)
    await step_admin_login(state, client)
    
    # 创建并登录普通用户
    await step_create_normal_user(state, client)
    await step_user_login(state, client)
    
    # 创建知识库
    await step_create_knowledge_base(state, client)
    
    # 创建文档
    await step_create_document(state, client)
    
    # 训练知识库
    await step_train_knowledge_base(state, client)
    
    # 创建聊天会话
    await step_create_chat(state, client)
    
    # 测试用户WebSocket连接和多轮对话
    await step_connect_websocket(state, client)
    
    # 测试管理员WebSocket连接和多轮对话
    await step_connect_admin_websocket(state, client)
    
    # 再次测试用户对话，验证上下文保持
    await step_connect_websocket(state, client)