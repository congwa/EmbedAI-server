"""
RAG日志中间件

自动为RAG相关的API请求初始化链路追踪和日志记录
"""
import time
import re
from typing import Optional, Dict, Any, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import Logger


class RAGLoggingMiddleware(BaseHTTPMiddleware):
    """RAG日志中间件
    
    功能：
    1. 自动识别RAG相关的API请求
    2. 初始化RAG链路追踪
    3. 记录API请求和响应日志
    4. 提取和记录RAG相关参数
    """
    
    # RAG相关的API路径模式
    RAG_API_PATTERNS = [
        r'/api/v1/admin/knowledge-bases/\d+/train',
        r'/api/v1/admin/knowledge-bases/\d+/query',
        r'/api/v1/admin/knowledge-bases/\d+',
        r'/api/v1/admin/knowledge-bases',
        r'/api/v1/client/knowledge-base/\d+/query',
        r'/api/v1/chat/.*/knowledge-base/\d+',
    ]
    
    def __init__(self, app):
        """初始化中间件
        
        Args:
            app: FastAPI应用实例
        """
        super().__init__(app)
        self.compiled_patterns = [re.compile(pattern) for pattern in self.RAG_API_PATTERNS]
        
    async def dispatch(self, request: Request, call_next):
        """处理请求
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应对象
        """
        # 检查是否是RAG相关的API
        if not self._is_rag_api(request.url.path):
            return await call_next(request)
            
        # 记录请求开始时间
        start_time = time.time()
        
        # 提取RAG相关参数
        kb_id = self._extract_kb_id(request)
        user_id = self._extract_user_id(request)
        operation_type = self._determine_operation_type(request)
        
        # 初始化RAG链路追踪
        trace_id = Logger.init_rag_trace(
            kb_id=kb_id or 0,  # 如果无法提取kb_id，使用0作为默认值
            user_id=user_id,
            operation_type=operation_type
        )
        
        # 记录API请求日志
        Logger.rag_api_request(
            endpoint=request.url.path,
            method=request.method,
            kb_id=kb_id,
            user_id=user_id,
            params=dict(request.query_params),
            headers=dict(request.headers),
            client_ip=self._get_client_ip(request)
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录API响应日志
            Logger.rag_api_response(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                process_time=process_time,
                kb_id=kb_id,
                result_summary=self._extract_response_summary(response)
            )
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation=f"api_{operation_type}",
                duration=process_time,
                kb_id=kb_id
            )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录API错误日志
            Logger.rag_api_error(
                endpoint=request.url.path,
                method=request.method,
                error=str(e),
                kb_id=kb_id,
                user_id=user_id,
                process_time=process_time
            )
            
            # 重新抛出异常
            raise
            
    def _is_rag_api(self, path: str) -> bool:
        """检查是否是RAG相关的API
        
        Args:
            path: API路径
            
        Returns:
            bool: 是否是RAG API
        """
        for pattern in self.compiled_patterns:
            if pattern.match(path):
                return True
        return False
        
    def _extract_kb_id(self, request: Request) -> Optional[int]:
        """从请求中提取知识库ID
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Optional[int]: 知识库ID，如果无法提取则返回None
        """
        # 从URL路径中提取
        path = request.url.path
        
        # 匹配 /knowledge-bases/{kb_id} 或 /knowledge-base/{kb_id} 模式
        kb_patterns = [
            r'/knowledge-bases/(\d+)',
            r'/knowledge-base/(\d+)',
        ]
        
        for pattern in kb_patterns:
            match = re.search(pattern, path)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
                    
        # 从查询参数中提取
        if 'kb_id' in request.query_params:
            try:
                return int(request.query_params['kb_id'])
            except ValueError:
                pass
                
        # 从请求体中提取（如果是POST/PUT请求）
        # 注意：这里无法直接读取请求体，因为它可能已经被消费
        # 实际实现中可能需要在路由处理器中设置
        
        return None
        
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """从请求中提取用户ID
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Optional[int]: 用户ID，如果无法提取则返回None
        """
        # 从请求状态中获取（通常由认证中间件设置）
        if hasattr(request.state, 'user') and hasattr(request.state.user, 'id'):
            return request.state.user.id
            
        # 从请求头中提取（如果有自定义头）
        user_id_header = request.headers.get('X-User-ID')
        if user_id_header:
            try:
                return int(user_id_header)
            except ValueError:
                pass
                
        return None
        
    def _determine_operation_type(self, request: Request) -> str:
        """确定操作类型
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 操作类型
        """
        path = request.url.path.lower()
        method = request.method.upper()
        
        # 训练相关操作
        if '/train' in path:
            return 'training'
            
        # 查询相关操作
        if '/query' in path or method == 'GET':
            return 'query'
            
        # 管理相关操作
        if method in ['POST', 'PUT', 'DELETE']:
            return 'management'
            
        return 'unknown'
        
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
            
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
            
        # 使用客户端地址
        if hasattr(request, 'client') and request.client:
            return request.client.host
            
        return 'unknown'
        
    def _extract_response_summary(self, response: Response) -> Dict[str, Any]:
        """提取响应摘要信息
        
        Args:
            response: HTTP响应对象
            
        Returns:
            Dict[str, Any]: 响应摘要
        """
        summary = {
            'status_code': response.status_code,
            'content_type': response.headers.get('content-type', 'unknown')
        }
        
        # 如果是JSON响应，尝试提取一些基本信息
        if isinstance(response, JSONResponse):
            try:
                # 注意：这里无法直接访问响应体内容
                # 实际实现中可能需要在路由处理器中设置额外的响应头
                content_length = response.headers.get('content-length')
                if content_length:
                    summary['content_length'] = int(content_length)
            except (ValueError, TypeError):
                pass
                
        return summary


class RAGLoggingConfig:
    """RAG日志中间件配置"""
    
    def __init__(
        self,
        enabled: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024,  # 最大记录的请求/响应体大小（字节）
        excluded_paths: Optional[List[str]] = None
    ):
        """初始化配置
        
        Args:
            enabled: 是否启用中间件
            log_request_body: 是否记录请求体
            log_response_body: 是否记录响应体
            max_body_size: 最大记录的请求/响应体大小
            excluded_paths: 排除的路径列表
        """
        self.enabled = enabled
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.excluded_paths = excluded_paths or []


# 默认配置
default_config = RAGLoggingConfig()