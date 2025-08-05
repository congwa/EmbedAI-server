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
from app.core.middleware import LoggingMiddleware, RequestValidationMiddleware, TraceMiddleware
from app.middleware import RAGLoggingMiddleware
from app.middleware.context_middleware import ContextMiddleware
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
    Logger.info("应用程序启动中...")
    await create_tables()
    await start_monitoring_connections()
    yield
    # 关闭时执行
    Logger.info("应用程序关闭中...")

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
    # 获取当前请求的trace_id
    trace_id = request.headers.get("X-Trace-ID", "无追踪ID")
    
    Logger.error(
        f"发生未处理的错误: {exc}",
        request_path=request.url.path,
        request_method=request.method,
        trace_id=trace_id,
        error=str(exc)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "message": str(exc),
            "trace_id": trace_id
        },
    )

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加链路追踪中间件 - 必须在最外层，最先执行
app.add_middleware(TraceMiddleware)

# 添加分析中间件 - 在链路追踪之后，用于收集分析数据
from app.middleware.analytics_middleware import AnalyticsMiddleware
app.add_middleware(AnalyticsMiddleware)

# 添加RAG日志中间件 - 在链路追踪之后，其他中间件之前
app.add_middleware(RAGLoggingMiddleware)

# 添加上下文中间件
app.add_middleware(ContextMiddleware)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# 添加请求验证中间件
app.add_middleware(RequestValidationMiddleware)

# 注册主路由
from app.api.v1 import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# 注册WebSocket路由
from app.api.v1.ws import router as ws_router
app.include_router(ws_router, prefix='/ws')

# start_monitoring_connections 函数已在 app.core.ws 中定义，这里不需要重复定义

# 3. 修改 uvicorn.run 的调用方式
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)