import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from app.models.database import AsyncSessionLocal, engine, Base
from app.models.knowledge_base import PermissionType
from .utils.test_state import TestState
from .utils.decorators import step_decorator
import pytest_asyncio
import asyncio

@pytest.fixture(scope="session")
def state():
    """测试状态管理器"""
    return TestState("knowledge_base_flow")

@pytest.fixture(scope="session")
def client():
    """测试客户端"""
    return TestClient(app)

@pytest_asyncio.fixture(autouse=True)
async def setup_database(state):
    """设置测试数据库"""
    # 每次测试开始时都重置数据库和状态
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    state.reset()
    
    yield
    
    # 测试完成后不清理数据库，以支持断点续测

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
                    "model": "test-model"
                },
                "embeddings": {
                    "model": "test-embeddings"
                }
            }
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("kb_id", response.json()["data"]["id"])

@step_decorator("create_another_user")
async def step_create_another_user(state: TestState, client: TestClient):
    """创建另一个普通用户"""
    admin_token = state.get_step_data("admin_token")
    response = client.post(
        "/api/v1/admin/users",
        json={
            "email": "another_user@example.com",
            "password": "user123",
            "is_admin": False
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    state.save_step_data("another_user_id", response.json()["data"]["id"])

@step_decorator("another_user_login")
async def step_another_user_login(state: TestState, client: TestClient):
    """另一个用户登录"""
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": "another_user@example.com",
            "password": "user123"
        }
    )
    assert response.status_code == 200
    state.save_step_data("another_user_token", response.json()["data"]["access_token"])

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

@step_decorator("update_member_permission")
async def step_update_member_permission(state: TestState, client: TestClient):
    """更新成员权限"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    another_user_id = state.get_step_data("another_user_id")
    
    # 更新权限
    response = client.put(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members/{another_user_id}",
        json={
            "permission": "admin"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    
    # 验证权限更新
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    members = response.json()["data"]["members"]
    admin = next(m for m in members if m["id"] == another_user_id)
    assert admin["permission"] == "admin"

@step_decorator("test_member_access")
async def step_test_member_access(state: TestState, client: TestClient):
    """测试成员访问权限"""
    another_user_token = state.get_step_data("another_user_token")
    kb_id = state.get_step_data("kb_id")
    
    # 测试查看知识库详情
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}",
        headers={"Authorization": f"Bearer {another_user_token}"}
    )
    assert response.status_code == 200
    
    # 测试查看成员列表
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members",
        headers={"Authorization": f"Bearer {another_user_token}"}
    )
    assert response.status_code == 200

@step_decorator("remove_member")
async def step_remove_member(state: TestState, client: TestClient):
    """移除成员"""
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    another_user_id = state.get_step_data("another_user_id")
    
    # 移除成员
    response = client.delete(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members/{another_user_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    
    # 验证成员已移除
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}/members",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    members = response.json()["data"]["members"]
    assert len(members) == 1
    assert all(m["id"] != another_user_id for m in members)
    
    # 验证被移除成员无法访问
    another_user_token = state.get_step_data("another_user_token")
    response = client.get(
        f"/api/v1/admin/knowledge-bases/{kb_id}",
        headers={"Authorization": f"Bearer {another_user_token}"}
    )
    assert response.status_code == 403

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

@pytest.mark.asyncio
async def test_full_flow(state: TestState, client: TestClient):
    """完整的测试流程"""
    await step_create_admin(state, client)
    await step_admin_login(state, client)
    await step_create_normal_user(state, client)
    await step_user_login(state, client)
    await step_create_another_user(state, client)
    await step_another_user_login(state, client)
    await step_create_knowledge_base(state, client)
    await step_get_kb_members(state, client)
    await step_add_member_to_kb(state, client)
    await step_update_member_permission(state, client)
    await step_test_member_access(state, client)
    await step_remove_member(state, client)
    await step_create_document(state, client) 