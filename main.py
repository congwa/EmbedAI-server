from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.models.database import create_tables
from app.core.exceptions import (
    HTTPException,
    ValidationError,
    SQLAlchemyError,
    http_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.core.middleware import LoggingMiddleware, RequestValidationMiddleware
from app.core.logger import Logger
from contextlib import asynccontextmanager
import uvicorn

from fast_graphrag import GraphRAG, QueryParam
from app.models import *  # 导入所有模型

# 1. 使用新的 lifespan 方式替代 on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    Logger.info("Application starting up...")
    await create_tables()
    yield
    # 关闭时执行
    Logger.info("Application shutting down...")

# 2. 在创建 FastAPI 实例时指定 lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 注册异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)

# 注册主路由
from app.api.v1 import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# 3. 修改 uvicorn.run 的调用方式
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)