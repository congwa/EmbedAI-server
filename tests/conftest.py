"""
测试配置文件
提供测试所需的fixtures和配置
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from app.models.database import Base, get_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.services.auth import create_access_token
from app.core.config import settings

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

TestAsyncSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理数据库
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # 删除测试数据库文件
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with TestAsyncSessionLocal() as session:
        yield session

@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """覆盖数据库依赖"""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client(override_get_db) -> TestClient:
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    from app.services.user import UserService
    from app.schemas.user import UserCreate
    
    user_service = UserService(db_session)
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        is_active=True
    )
    user = await user_service.create_user(user_data)
    return user

@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员"""
    from app.services.user import UserService
    from app.schemas.user import UserCreate
    
    user_service = UserService(db_session)
    admin_data = UserCreate(
        username="testadmin",
        email="admin@example.com",
        password="AdminPassword123!",
        is_active=True,
        is_superuser=True
    )
    admin = await user_service.create_user(admin_data)
    return admin

@pytest.fixture
def user_token(test_user: User) -> str:
    """创建用户访问令牌"""
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def admin_token(test_admin: User) -> str:
    """创建管理员访问令牌"""
    return create_access_token(data={"sub": str(test_admin.id)})

@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """创建认证头部"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """创建管理员认证头部"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
async def test_knowledge_base(db_session: AsyncSession, test_user: User) -> KnowledgeBase:
    """创建测试知识库"""
    from app.services.knowledge_base import KnowledgeBaseService
    from app.schemas.knowledge_base import KnowledgeBaseCreate
    
    kb_service = KnowledgeBaseService(db_session)
    kb_data = KnowledgeBaseCreate(
        name="Test Knowledge Base",
        description="A test knowledge base"
    )
    kb = await kb_service.create_knowledge_base(kb_data, test_user.id)
    return kb

@pytest.fixture
def sample_data():
    """提供测试数据"""
    return {
        "users": [
            {
                "username": "user1",
                "email": "user1@example.com",
                "password": "Password123!"
            },
            {
                "username": "user2", 
                "email": "user2@example.com",
                "password": "Password123!"
            }
        ],
        "knowledge_bases": [
            {
                "name": "KB1",
                "description": "Knowledge Base 1"
            },
            {
                "name": "KB2",
                "description": "Knowledge Base 2"
            }
        ]
    }

# 测试标记
pytest_plugins = ["pytest_asyncio"]

# 测试配置
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )

# 测试环境变量
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
