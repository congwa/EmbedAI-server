import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from app.models.database import AsyncSessionLocal, engine, Base
from .utils.test_state import TestState
from .utils.decorators import step_decorator
from .test_knowledge_base_flow import (
    step_create_admin,
    step_admin_login,
    step_create_normal_user,
    step_user_login,
    step_create_knowledge_base,
    setup_database
)
import pytest_asyncio

@pytest.fixture(scope="session")
def state() -> Generator[TestState, None, None]:
    """测试状态管理器"""
    yield TestState("document_flow")

@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """测试客户端"""
    yield TestClient(app)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_data(state: TestState, client: TestClient) -> AsyncGenerator[None, None]:
    """设置测试数据"""
    # 重用knowledge_base_flow中的数据库设置
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    state.reset()
    
    # 创建必要的测试数据
    await step_create_admin(state, client)
    await step_admin_login(state, client)
    await step_create_normal_user(state, client)
    await step_user_login(state, client)
    await step_create_knowledge_base(state, client)
    yield

@step_decorator("create_document")
async def step_create_document(state: TestState, client: TestClient):
    """创建文档"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    
    response = client.post(
        f"/api/v1/admin/knowledge-bases/{kb_id}/documents",
        json={
            "title": "测试文档",
            "content": "这是一个测试文档的内容",
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
        f"/api/v1/admin/knowledge-bases/{kb_id}/documents",
        params={"skip": 0, "limit": 10},
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

@pytest.mark.asyncio
async def test_document_flow(state: TestState, client: TestClient):
    """测试文档管理流程"""
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