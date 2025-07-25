from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import uuid
from app.core.logger import Logger
from app.core.response import APIResponse
import traceback

class TraceMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件
    
    为每个HTTP请求分配唯一的trace_id，并在请求上下文中传递
    """
    async def dispatch(self, request: Request, call_next):
        # 获取或生成trace_id
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = f"trace-{uuid.uuid4().hex[:8]}"
            
        # 初始化追踪上下文
        Logger.init_trace(
            trace_id=trace_id,
            request_path=str(request.url.path),
            request_method=request.method
        )
        
        # 记录请求开始
        start_time = time.time()
        
        # 添加trace_id到响应头
        response = await call_next(request)
        if isinstance(response, Response):
            response.headers["X-Trace-ID"] = trace_id
            
        # 记录请求结束
        process_time = time.time() - start_time
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件
    
    记录HTTP请求和响应的详细信息
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 提取请求参数
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求信息
        Logger.api_request(
            method=request.method,
            path=path,
            params=query_params,
            client_ip=client_host,
            user_agent=user_agent
        )
        
        try:
            response = await call_next(request)
            
            # 记录响应信息
            process_time = time.time() - start_time
            Logger.api_response(
                method=request.method,
                path=path,
                status_code=response.status_code,
                process_time=process_time
            )
            
            return response
        except Exception as e:
            error_info = traceback.format_exc()
            # 记录错误信息
            process_time = time.time() - start_time
            Logger.error(
                f"处理请求时发生错误: {request.method} {path}",
                error=str(e),
                traceback=error_info,
                process_time=process_time,
                client_ip=client_host
            )
            raise

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件
    
    验证请求头和参数的有效性
    """
    async def dispatch(self, request: Request, call_next):
        # 验证请求头
        if request.method != "OPTIONS":  # 跳过 OPTIONS 请求的验证
            required_headers = ["user-agent"]
            for header in required_headers:
                if header not in request.headers:
                    Logger.warning(
                        f"请求缺少必要的头部: {header}",
                        path=str(request.url.path),
                        method=request.method,
                        client_ip=request.client.host if request.client else "unknown"
                    )
                    return APIResponse.error(
                        message=f"缺少必要的请求头: {header}",
                        code=400
                    )
        
        return await call_next(request)