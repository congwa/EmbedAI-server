import pytest
from typing import Generator
from fastapi.testclient import TestClient
from .utils.test_state import TestState
from .utils.decorators import step_decorator
from main import app

@pytest.fixture(scope="session")
def state() -> Generator[TestState, None, None]:
    """测试状态管理器"""
    yield TestState("client_flow")

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """测试客户端"""
    yield TestClient(app)

@step_decorator("create_third_party_user")
async def step_create_third_party_user(state: TestState, client: TestClient):
    """创建第三方用户"""
    user_token = state.get_step_data("user_token")
    
    response = client.post(
        "/api/v1/admin/third-party-users",
        json={
            "username": "test_user",
            "external_id": "ext_123",
            "metadata": {
                "source": "test",
                "platform": "web"
            }
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("third_party_user_id", response.json()["data"]["id"])
    return response.json()

@step_decorator("get_third_party_user")
async def step_get_third_party_user(state: TestState, client: TestClient):
    """获取第三方用户信息"""
    user_token = state.get_step_data("user_token")
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    response = client.get(
        f"/api/v1/admin/third-party-users/{third_party_user_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "test_user"
    return response.json()

@step_decorator("list_third_party_users")
async def step_list_third_party_users(state: TestState, client: TestClient):
    """获取第三方用户列表"""
    user_token = state.get_step_data("user_token")
    
    response = client.get(
        "/api/v1/admin/third-party-users",
        params={"page": 1, "size": 10},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) > 0
    return response.json()

@step_decorator("update_third_party_user")
async def step_update_third_party_user(state: TestState, client: TestClient):
    """更新第三方用户信息"""
    user_token = state.get_step_data("user_token")
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    response = client.put(
        f"/api/v1/admin/third-party-users/{third_party_user_id}",
        json={
            "username": "updated_user",
            "metadata": {
                "source": "test",
                "platform": "mobile"
            }
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "updated_user"
    return response.json()

@step_decorator("client_api_access")
async def step_client_api_access(state: TestState, client: TestClient):
    """测试客户端API访问"""
    user_token = state.get_step_data("user_token")
    third_party_user_id = state.get_step_data("third_party_user_id")
    
    # 测试获取知识库列表
    response = client.get(
        "/api/v1/client/knowledge-bases",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-Third-Party-User-ID": str(third_party_user_id)
        }
    )
    assert response.status_code == 200
    
    # 测试创建聊天会话
    kb_id = state.get_step_data("kb_id")
    response = client.post(
        "/api/v1/client/chats",
        json={"knowledge_base_id": kb_id},
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-Third-Party-User-ID": str(third_party_user_id)
        }
    )
    assert response.status_code == 200
    return response.json()

@step_decorator("create_admin")
async def step_create_admin(state: TestState, client: TestClient):
    """创建管理员账户"""
    response = client.post(
        "/api/v1/admin/register",
        json={
            "email": "admin@example.com",
            "password": "admin123",
            "register_code": "123456"
        }
    )
    assert response.status_code == 200
    response_data = response.json()
    state.save_step_data("admin_id", response_data["data"]["id"])
    state.save_step_data("admin_email", response_data["data"]["email"])
    return response_data

@step_decorator("admin_login")
async def step_admin_login(state: TestState, client: TestClient):
    """管理员登录"""
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": "admin@example.com",
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    state.save_step_data("admin_token", response.json()["data"]["access_token"])

@step_decorator("create_normal_user")
async def step_create_normal_user(state: TestState, client: TestClient):
    """创建普通用户"""
    admin_token = state.get_step_data("admin_token")
    response = client.post(
        "/api/v1/admin/users",
        json={
            "email": "user@example.com",
            "password": "user123",
            "is_admin": False
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("user_id", response.json()["data"]["id"])

@step_decorator("user_login")
async def step_user_login(state: TestState, client: TestClient):
    """普通用户登录"""
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": "user@example.com",
            "password": "user123"
        }
    )
    assert response.status_code == 200
    state.save_step_data("user_token", response.json()["data"]["access_token"])

@pytest.mark.asyncio
async def test_client_flow(state: TestState, client: TestClient):
    """测试第三方用户功能流程"""
    # 创建并登录管理员
    await step_create_admin(state, client)
    await step_admin_login(state, client)
    
    # 创建并登录普通用户
    await step_create_normal_user(state, client)
    await step_user_login(state, client)
    
    # 创建第三方用户
    await step_create_third_party_user(state, client)
    
    # 获取第三方用户信息
    await step_get_third_party_user(state, client)
    
    # 获取第三方用户列表
    await step_list_third_party_users(state, client)
    
    # 更新第三方用户信息
    await step_update_third_party_user(state, client)
    
    # 测试客户端API访问
    await step_client_api_access(state, client)