import json
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseFunction
from starlette.requests import Request
from starlette.responses import Response
from app.core.context import set_context, clear_context
from app.core.logger import Logger

class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseFunction
    ) -> Response:
        """
        设置和清除请求上下文
        """
        # 在请求处理前设置上下文
        user_id = None
        kb_id = None

        try:
            # 尝试从路径参数中获取
            if "user_id" in request.path_params:
                user_id = int(request.path_params["user_id"])
            if "kb_id" in request.path_params:
                kb_id = int(request.path_params["kb_id"])

            # 尝试从查询参数中获取
            if "user_id" in request.query_params:
                user_id = int(request.query_params["user_id"])
            if "kb_id" in request.query_params:
                kb_id = int(request.query_params["kb_id"])
            
            # 尝试从请求体中获取
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                    if isinstance(body, dict):
                        if "user_id" in body:
                            user_id = int(body["user_id"])
                        if "third_party_user_id" in body:
                            user_id = int(body["third_party_user_id"])
                        if "kb_id" in body:
                            kb_id = int(body["kb_id"])
                except json.JSONDecodeError:
                    # 如果请求体不是JSON，忽略
                    pass
                except Exception as e:
                    Logger.warning(f"从请求体解析上下文失败: {e}")

            set_context(user_id=user_id, kb_id=kb_id)
            Logger.info(f"设置请求上下文: user_id={user_id}, kb_id={kb_id} for path {request.url.path}")

            response = await call_next(request)
            return response

        finally:
            # 在请求处理后清除上下文
            Logger.info(f"清除请求上下文 for path {request.url.path}")
            clear_context()