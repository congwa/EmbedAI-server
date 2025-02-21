import pytest
from typing import Generator
from fastapi.testclient import TestClient
from .utils.test_state import TestState
from .utils.decorators import step_decorator
from fastapi import WebSocket
from app.models.enums import ChatMode
from main import app

@pytest.fixture(scope="session")
def state() -> Generator[TestState, None, None]:
    """测试状态管理器"""
    yield TestState("chat_flow")

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """测试客户端"""
    yield TestClient(app)

@step_decorator("create_chat")
async def step_create_chat(state: TestState, client: TestClient):
    """创建聊天会话"""
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
    """连接WebSocket"""
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
        
        # 发送消息
        await websocket.send_json({
            "content": "你好，这是一条测试消息"
        })
        
        # 接收消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "你好，这是一条测试消息"
        
        # 接收AI回复
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["message_type"] == "assistant"

@step_decorator("connect_admin_websocket")
async def step_connect_admin_websocket(state: TestState, client: TestClient):
    """管理员连接WebSocket"""
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
        
        # 发送管理员消息
        await websocket.send_json({
            "content": "这是管理员的回复"
        })
        
        # 接收消息广播
        response = await websocket.receive_json()
        assert response["type"] == "message"
        assert response["data"]["content"] == "这是管理员的回复"
        assert response["data"]["message_type"] == "admin"

@pytest.mark.asyncio
async def test_chat_flow(state: TestState, client: TestClient):
    """测试聊天功能流程"""
    # 创建聊天会话
    await step_create_chat(state, client)
    
    # 测试用户WebSocket连接
    await step_connect_websocket(state, client)
    
    # 测试管理员WebSocket连接
    await step_connect_admin_websocket(state, client)