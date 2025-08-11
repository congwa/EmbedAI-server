"""
新响应系统的单元测试

测试新的异常驱动响应系统的各个组件。
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.core.exceptions_new import (
    BaseAPIException,
    UnauthorizedError,
    ForbiddenError,
    ResourceNotFoundError,
    ValidationError,
    BusinessError,
    SystemError
)
from app.core.response_utils import (
    success_response,
    pagination_response,
    created_response,
    no_content_response,
    accepted_response
)


class TestExceptionClasses:
    """测试异常类的创建和属性"""
    
    def test_base_api_exception(self):
        """测试基础异常类"""
        exc = BaseAPIException("测试错误", {"key": "value"})
        
        assert exc.status_code == 500
        assert exc.detail["message"] == "测试错误"
        assert exc.detail["data"] == {"key": "value"}
        assert exc.detail["error_code"] == "unknown_error"
        assert "timestamp" in exc.detail
    
    def test_unauthorized_error(self):
        """测试认证失败异常"""
        exc = UnauthorizedError("认证失败")
        
        assert exc.status_code == 401
        assert exc.detail["error_code"] == "unauthorized"
        assert exc.detail["message"] == "认证失败"
        assert exc.headers["WWW-Authenticate"] == "Bearer"
    
    def test_forbidden_error(self):
        """测试权限不足异常"""
        exc = ForbiddenError("权限不足")
        
        assert exc.status_code == 403
        assert exc.detail["error_code"] == "forbidden"
        assert exc.detail["message"] == "权限不足"
    
    def test_resource_not_found_error(self):
        """测试资源未找到异常"""
        exc = ResourceNotFoundError("用户", 123)
        
        assert exc.status_code == 404
        assert exc.detail["error_code"] == "resource_not_found"
        assert "用户不存在（ID: 123）" in exc.detail["message"]
        assert exc.detail["data"]["resource_name"] == "用户"
        assert exc.detail["data"]["resource_id"] == 123
    
    def test_validation_error(self):
        """测试数据验证异常"""
        exc = ValidationError("邮箱格式无效", "email", "invalid-email")
        
        assert exc.status_code == 422
        assert exc.detail["error_code"] == "validation_error"
        assert exc.detail["message"] == "邮箱格式无效"
        assert exc.detail["data"]["field"] == "email"
        assert exc.detail["data"]["value"] == "invalid-email"
    
    def test_business_error(self):
        """测试业务逻辑异常"""
        exc = BusinessError("库存不足")
        
        assert exc.status_code == 400
        assert exc.detail["error_code"] == "business_error"
        assert exc.detail["message"] == "库存不足"
    
    def test_system_error(self):
        """测试系统异常"""
        original_exc = ValueError("原始错误")
        exc = SystemError("系统错误", "SYS001", original_exc)
        
        assert exc.status_code == 500
        assert exc.detail["error_code"] == "system_error"
        assert exc.detail["message"] == "系统错误"
        assert exc.detail["data"]["internal_error_code"] == "SYS001"
        assert exc.detail["data"]["original_error"] == "原始错误"


class TestResponseUtils:
    """测试响应工具函数"""
    
    def test_success_response(self):
        """测试成功响应"""
        data = {"id": 1, "name": "test"}
        response = success_response(data=data, message="操作成功")
        
        assert response["success"] is True
        assert response["code"] == 200
        assert response["message"] == "操作成功"
        assert response["data"] == data
    
    def test_success_response_default(self):
        """测试默认成功响应"""
        response = success_response()
        
        assert response["success"] is True
        assert response["code"] == 200
        assert response["message"] == "操作成功"
        assert response["data"] is None
    
    def test_pagination_response(self):
        """测试分页响应"""
        items = [{"id": 1}, {"id": 2}]
        response = pagination_response(
            items=items,
            total=100,
            page=2,
            page_size=10
        )
        
        assert response["success"] is True
        assert response["code"] == 200
        assert response["message"] == "获取列表成功"
        assert response["data"]["items"] == items
        assert response["data"]["pagination"]["total"] == 100
        assert response["data"]["pagination"]["page"] == 2
        assert response["data"]["pagination"]["page_size"] == 10
        assert response["data"]["pagination"]["total_pages"] == 10
        assert response["data"]["pagination"]["has_next"] is True
        assert response["data"]["pagination"]["has_prev"] is True
    
    def test_pagination_response_edge_cases(self):
        """测试分页响应的边界情况"""
        # 第一页
        response = pagination_response([], 5, 1, 10)
        assert response["data"]["pagination"]["has_prev"] is False
        assert response["data"]["pagination"]["has_next"] is False
        
        # 最后一页
        response = pagination_response([], 25, 3, 10)
        assert response["data"]["pagination"]["has_prev"] is True
        assert response["data"]["pagination"]["has_next"] is False
    
    def test_created_response(self):
        """测试创建成功响应"""
        data = {"id": 1, "name": "new item"}
        response = created_response(data=data, message="创建成功")
        
        assert response["success"] is True
        assert response["code"] == 201
        assert response["message"] == "创建成功"
        assert response["data"] == data
    
    def test_no_content_response(self):
        """测试无内容响应"""
        response = no_content_response("删除成功")
        
        assert response["success"] is True
        assert response["code"] == 204
        assert response["message"] == "删除成功"
        assert response["data"] is None
    
    def test_accepted_response(self):
        """测试请求已接受响应"""
        response = accepted_response(
            message="任务已提交",
            task_id="task-123"
        )
        
        assert response["success"] is True
        assert response["code"] == 202
        assert response["message"] == "任务已提交"
        assert response["data"]["task_id"] == "task-123"


class TestAutoResponseDecorator:
    """测试自动响应装饰器"""
    
    def test_auto_response_decorator(self):
        """测试自动响应装饰器"""
        from app.core.response_utils import auto_response
        
        @auto_response(success_message="用户获取成功")
        async def get_user():
            return {"id": 1, "name": "test"}
        
        # 模拟异步函数调用
        import asyncio
        result = asyncio.run(get_user())
        
        assert result["success"] is True
        assert result["message"] == "用户获取成功"
        assert result["data"] == {"id": 1, "name": "test"}
    
    def test_auto_response_with_existing_response(self):
        """测试装饰器处理已有响应格式的情况"""
        from app.core.response_utils import auto_response
        
        @auto_response()
        async def get_user():
            return success_response(data={"id": 1}, message="自定义消息")
        
        import asyncio
        result = asyncio.run(get_user())
        
        # 应该直接返回已有的响应格式
        assert result["message"] == "自定义消息"


class TestDataProcessing:
    """测试数据处理功能"""
    
    def test_process_pydantic_model(self):
        """测试Pydantic模型的处理"""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            id: int
            name: str
        
        model = TestModel(id=1, name="test")
        response = success_response(data=model)
        
        # 应该自动转换为字典
        assert response["data"] == {"id": 1, "name": "test"}
    
    def test_process_list_data(self):
        """测试列表数据的处理"""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            id: int
            name: str
        
        models = [TestModel(id=1, name="test1"), TestModel(id=2, name="test2")]
        response = success_response(data=models)
        
        expected = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        assert response["data"] == expected


class TestCompatibility:
    """测试向后兼容性"""
    
    def test_response_wrapper_compatibility(self):
        """测试ResponseWrapper的兼容性"""
        from app.core.response_utils import ResponseWrapper
        
        with pytest.warns(DeprecationWarning):
            response = ResponseWrapper.success(data={"test": "data"})
        
        # 应该返回JSONResponse对象
        from fastapi.responses import JSONResponse
        assert isinstance(response, JSONResponse)
    
    def test_deprecated_api_response_warnings(self):
        """测试废弃的APIResponse方法会发出警告"""
        from app.core.response import APIResponse
        
        with pytest.warns(DeprecationWarning):
            APIResponse.success(data={"test": "data"})
        
        with pytest.warns(DeprecationWarning):
            APIResponse.error("test error")
        
        with pytest.warns(DeprecationWarning):
            APIResponse.pagination([], 0, 1, 10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])