from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'),
    echo=True,
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()

# 创建所有表的函数
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 测试数据库连接
async def test_connection() -> bool:
    """测试数据库连接是否正常"""
    try:
        async with AsyncSessionLocal() as session:
            # 执行一个简单的查询来测试连接
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        return False