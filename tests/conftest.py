import os
import sys
import pytest
import asyncio
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.models.database import AsyncSessionLocal, engine, Base

def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--reset-state",
        action="store_true",
        default=False,
        help="重置测试状态，忽略已保存的状态文件"
    )

@pytest.fixture(scope="session")
def reset_state(request):
    """获取是否重置状态的参数值"""
    return request.config.getoption("--reset-state")

# 设置测试用的事件循环
@pytest_asyncio.fixture(scope="session")
def event_loop():
    """创建一个会话级别的事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def client() -> Generator:
    """创建测试用的 FastAPI 客户端"""
    with TestClient(app) as c:
        yield c

@pytest_asyncio.fixture(scope="session")
async def db() -> AsyncGenerator:
    """创建测试用的数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def setup_database(state, reset_state):
    """设置测试数据库"""
    # 如果指定了重置状态或者是新的测试运行，重置数据库和状态
    if reset_state or not state.step_completed("setup_database"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        state.reset()
    
    yield
    
    # 测试完成后不清理数据库，以支持断点续测 