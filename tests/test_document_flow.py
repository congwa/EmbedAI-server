import pytest
from typing import Generator
from fastapi.testclient import TestClient
from .utils.test_state import TestState
from .utils.decorators import step_decorator
from main import app

@pytest.fixture(scope="session")
def state() -> Generator[TestState, None, None]:
    """测试状态管理器"""
    yield TestState("document_flow")

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """测试客户端"""
    yield TestClient(app)

@step_decorator("create_document")
async def step_create_document(state: TestState, client: TestClient):
    """创建文档"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    
    response = client.post(
        "/api/v1/admin/documents",
        json={
            "title": "测试文档",
            "content": "这是一个测试文档的内容",
            "knowledge_base_id": kb_id,
            "doc_type": "text"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("doc_id", response.json()["data"]["id"])
    return response.json()

@step_decorator("update_document")
async def step_update_document(state: TestState, client: TestClient):
    """更新文档"""
    user_token = state.get_step_data("user_token")
    doc_id = state.get_step_data("doc_id")
    
    response = client.put(
        f"/api/v1/admin/documents/{doc_id}",
        json={
            "title": "更新后的文档",
            "content": "这是更新后的文档内容"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    return response.json()

@step_decorator("get_document")
async def step_get_document(state: TestState, client: TestClient):
    """获取文档"""
    user_token = state.get_step_data("user_token")
    doc_id = state.get_step_data("doc_id")
    
    response = client.get(
        f"/api/v1/admin/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "更新后的文档"
    return response.json()

@step_decorator("list_documents")
async def step_list_documents(state: TestState, client: TestClient):
    """获取文档列表"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    
    response = client.get(
        "/api/v1/admin/documents",
        params={"knowledge_base_id": kb_id, "page": 1, "size": 10},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) > 0
    return response.json()

@step_decorator("soft_delete_document")
async def step_soft_delete_document(state: TestState, client: TestClient):
    """软删除文档"""
    user_token = state.get_step_data("user_token")
    doc_id = state.get_step_data("doc_id")
    
    response = client.delete(
        f"/api/v1/admin/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_token}"}
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
async def test_document_flow(state: TestState, client: TestClient):
    """测试文档管理流程"""
    # 创建并登录管理员
    await step_create_admin(state, client)
    await step_admin_login(state, client)
    
    # 创建并登录普通用户
    await step_create_normal_user(state, client)
    await step_user_login(state, client)
    
    # 创建文档
    await step_create_document(state, client)
    
    # 更新文档
    await step_update_document(state, client)
    
    # 获取文档
    await step_get_document(state, client)
    
    # 获取文档列表
    await step_list_documents(state, client)
    
    # 软删除文档
    await step_soft_delete_document(state, client)