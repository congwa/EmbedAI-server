from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.models.database import create_tables
from app.core.exceptions import (
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
from app.models import *  # 导入所有模型
from app.core.ws import connection_manager, start_monitoring_connections
from fastapi.responses import JSONResponse
import logging

# 1. 使用新的 lifespan 方式替代 on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    Logger.info("Application starting up...")
    await create_tables()
    await start_monitoring_connections()
    yield
    # 关闭时执行
    Logger.info("Application shutting down...")

# 2. 在创建 FastAPI 实例时指定 lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    debug=True
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmbedAi-Server")

# 注册异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error occurred: {exc}")
    logger.error(f"Request path: {request.url.path}, method: {request.method}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
    )

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)

# 注册主路由
from app.api.v1 import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# 注册WebSocket路由
from app.api.v1.ws.chat import router as chat_router
app.include_router(chat_router, prefix='/ws')

async def start_monitoring_connections():
    await connection_manager.monitor_connections()

# 3. 修改 uvicorn.run 的调用方式
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)