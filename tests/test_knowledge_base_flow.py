import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from app.models.database import AsyncSessionLocal, engine, Base
from app.models.knowledge_base import PermissionType
from .utils.test_state import TestState
from .utils.decorators import test_step
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

@test_step("create_admin")
async def test_create_admin(state: TestState, client: TestClient):
    """创建管理员账户"""
    print("执行测试步骤：创建管理员账户")
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

@test_step("admin_login")
async def test_admin_login(state: TestState, client: TestClient):
    """管理员登录"""
    print("执行测试步骤：管理员登录")
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": "admin@example.com",
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    state.save_step_data("admin_token", response.json()["data"]["access_token"])

@test_step("create_normal_user")
async def test_create_normal_user(state: TestState, client: TestClient):
    """创建普通用户"""
    print("执行测试步骤：创建普通用户")
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

@test_step("user_login")
async def test_user_login(state: TestState, client: TestClient):
    """普通用户登录"""
    print("执行测试步骤：普通用户登录")
    response = client.post(
        "/api/v1/admin/login",
        json={
            "email": "user@example.com",
            "password": "user123"
        }
    )
    assert response.status_code == 200
    state.save_step_data("user_token", response.json()["data"]["access_token"])

@test_step("create_knowledge_base")
async def test_create_knowledge_base(state: TestState, client: TestClient):
    """创建知识库"""
    print("执行测试步骤：创建知识库")
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

@test_step("add_user_to_kb")
async def test_add_user_to_kb(state: TestState, client: TestClient):
    """添加用户到知识库"""
    print("执行测试步骤：添加用户到知识库")
    admin_token = state.get_step_data("admin_token")
    kb_id = state.get_step_data("kb_id")
    admin_id = state.get_step_data("admin_id")
    response = client.post(
        f"/api/v1/admin/knowledge-bases/{kb_id}/users",
        json={
            "user_id": admin_id,
            "permission": "viewer"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

@test_step("create_document")
async def test_create_document(state: TestState, client: TestClient):
    """创建文档"""
    print("执行测试步骤：创建文档")
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

@test_step("train_knowledge_base")
async def test_train_knowledge_base(state: TestState, client: TestClient):
    """训练知识库"""
    print("执行测试步骤：训练知识库")
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    response = client.post(
        f"/api/v1/admin/knowledge-bases/{kb_id}/train",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200

@test_step("query_knowledge_base")
async def test_query_knowledge_base(state: TestState, client: TestClient):
    """查询知识库"""
    print("执行测试步骤：查询知识库")
    user_token = state.get_step_data("user_token")
    kb_id = state.get_step_data("kb_id")
    
    # 等待知识库训练完成
    max_retries = 10
    for _ in range(max_retries):
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        if response.json()["data"]["training_status"] == "TRAINED":
            break
        await asyncio.sleep(1)
    
    response = client.post(
        f"/api/v1/admin/knowledge-bases/{kb_id}/query",
        json={
            "query": "测试问题",
            "top_k": 3
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_full_flow(state: TestState, client: TestClient):
    """完整的测试流程"""
    # 按顺序执行所有测试步骤
    await test_create_admin(state, client)
    await test_admin_login(state, client)
    await test_create_normal_user(state, client)
    await test_user_login(state, client)
    await test_create_knowledge_base(state, client)
    await test_add_user_to_kb(state, client)
    await test_create_document(state, client)
    # await test_train_knowledge_base(state, client)
    # await test_query_knowledge_base(state, client) 