from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from app.core.logger import Logger
from app.core.response import APIResponse
import traceback

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        Logger.info(f"Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            
            # 记录响应信息
            process_time = time.time() - start_time
            Logger.info(
                f"Response: {request.method} {request.url} - "
                f"Status: {response.status_code} - "
                f"Process Time: {process_time:.2f}s"
            )
            
            return response
        except Exception as e:
            error_info = traceback.format_exc()
            # 记录错误信息
            Logger.error(
                f"Error processing request: {request.method} {request.url}\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{error_info}"
            )
            raise

class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 验证请求头
        if request.method != "OPTIONS":  # 跳过 OPTIONS 请求的验证
            required_headers = ["user-agent"]
            for header in required_headers:
                if header not in request.headers:
                    Logger.warning(f"Missing required header: {header}")
                    return APIResponse.error(
                        message=f"Missing required header: {header}",
                        code=400
                    )
        
        return await call_next(request)