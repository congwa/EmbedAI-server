from tests.utils.decorators import step_decorator
from tests.utils.test_state import TestState
from fastapi.testclient import TestClient
import asyncio


@step_decorator("create_chat")
async def step_create_chat(state: TestState, client: TestClient):
    """创建聊天会话"""
    # 写死三方用户 ID 必须的
    state.save_step_data("third_party_user_id", 1234567890)
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    response = client.post(
        "/api/v1/client/chat/create",
        json={
            "third_party_user_id": third_party_user_id,
            "kb_id": kb_id,
            "title": None  # 如果需要，可以传递标题
        }
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


@step_decorator("list_chats")
async def step_list_chats(state: TestState, client: TestClient):
    """列出聊天会话"""
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    response = client.get(
        f"/api/v1/client/chat/list?third_party_user_id={third_party_user_id}"
    )
    assert response.status_code == 200
    return response.json() 