import pytest
from typing import Generator, AsyncGenerator, Dict, Any, Optional
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from app.models.database import AsyncSessionLocal, engine, Base
from tests.utils.test_state import TestState
import pytest_asyncio


class BaseTest:
    """基础测试类，提供通用的测试功能"""
    
    @pytest.fixture(scope="session")
    def state(self) -> Generator[TestState, None, None]:
        """测试状态管理器"""
        yield TestState(self.get_test_name())
    
    @pytest.fixture(scope="session")
    def client(self) -> Generator[TestClient, None, None]:
        """测试客户端"""
        yield TestClient(app)
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_database(self, state: TestState) -> AsyncGenerator[None, None]:
        """设置测试数据库"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        state.reset()
        yield
    
    def get_test_name(self) -> str:
        """获取测试名称，子类需要实现此方法"""
        raise NotImplementedError("子类必须实现get_test_name方法")
    
    async def run_step(self, step_func, state: TestState, client: TestClient, **kwargs):
        """运行测试步骤"""
        return await step_func(state, client, **kwargs) 