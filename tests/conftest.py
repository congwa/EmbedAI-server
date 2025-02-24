import os
import sys
import pytest
import asyncio
import pytest_asyncio
import warnings
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

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
    parser.addoption(
        "--show-print",
        action="store_true",
        default=True,
        help="显示print输出"
    )

@pytest.fixture(scope="session")
def reset_state(request):
    """获取是否重置状态的参数值"""
    return request.config.getoption("--reset-state")

# 配置pytest环境
def pytest_configure(config):
    """配置pytest运行环境"""
    # 允许print输出
    config.option.capture = "no"
    
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 设置特定模块的日志级别
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
    logging.getLogger('EmbedAi-Server').setLevel(logging.INFO)
    
    # 忽略特定警告
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=pytest.PytestDeprecationWarning)
    warnings.filterwarnings("ignore", category=pytest.PytestCollectionWarning)
    warnings.filterwarnings("ignore", message=".*declarative_base.*")
    warnings.filterwarnings("ignore", message=".*class-based.*config.*")
    warnings.filterwarnings("ignore", message=".*event_loop fixture.*")
    warnings.filterwarnings("ignore", message=".*The asyncio_mode.*")
    warnings.filterwarnings("ignore", message=".*cannot collect test class.*")
    warnings.filterwarnings("ignore", message=".*Support for class-based.*")
    warnings.filterwarnings("ignore", message=".*MovedIn20Warning.*")
    
    # 设置asyncio默认fixture作用域
    config.option.asyncio_mode = "auto"
    config.option.asyncio_default_fixture_loop_scope = "session"

# 设置测试用的事件循环
@pytest.fixture(scope="session")
def event_loop():
    """创建一个session范围的事件循环"""
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