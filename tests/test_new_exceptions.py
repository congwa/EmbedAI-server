"""测试新的异常类体系"""

import pytest
from fastapi import status
from app.core.exceptions import (
    APIException,
    BusinessException,
    ResourceNotFoundException,
    PermissionDeniedException,
    ValidationException,
    SystemException,
    ConfigurationException
)


class TestAPIException:
    """测试APIException基类"""
    
    def test_api_exception_creation(self):
        """测试APIException创建"""
        exc = APIException(
            code=400,
            message="测试错误",
            data={"key": "value"}
        )
        
        assert exc.code == 400
        assert exc.message == "测试错误"
        assert exc.data == {"key": "value"}
        assert exc.headers is None
    
    def test_api_exception_with_headers(self):
        """测试带响应头的APIException"""
        headers = {"X-Custom-Header": "test"}
        exc = APIException(
            code=401,
            message="认证失败",
            headers=headers
        )
        
        assert exc.headers == headers


class TestBusinessException:
    """测试BusinessException"""
    
    def test_business_exception_creation(self):
        """测试BusinessException创建"""
        exc = BusinessException("业务规则验证失败")
        
        assert exc.code == status.HTTP_400_BAD_REQUEST
        assert exc.message == "业务规则验证失败"
        assert exc.data is None
    
    def test_business_exception_with_data(self):
        """测试带数据的BusinessException"""
        data = {"field": "name", "value": "invalid"}
        exc = BusinessException("名称格式不正确", data=data)
        
        assert exc.code == status.HTTP_400_BAD_REQUEST
        assert exc.message == "名称格式不正确"
        assert exc.data == data


class TestResourceNotFoundException:
    """测试ResourceNotFoundException"""
    
    def test_resource_not_found_default(self):
        """测试默认资源未找到异常"""
        exc = ResourceNotFoundException()
        
        assert exc.code == status.HTTP_404_NOT_FOUND
        assert exc.message == "资源不存在"
        assert exc.data == {"resource": "资源", "resource_id": None}
    
    def test_resource_not_found_with_resource_name(self):
        """测试指定资源名称的异常"""
        exc = ResourceNotFoundException("用户")
        
        assert exc.code == status.HTTP_404_NOT_FOUND
        assert exc.message == "用户不存在"
        assert exc.data == {"resource": "用户", "resource_id": None}
    
    def test_resource_not_found_with_id(self):
        """测试带资源ID的异常"""
        exc = ResourceNotFoundException("配置", 123)
        
        assert exc.code == status.HTTP_404_NOT_FOUND
        assert exc.message == "配置不存在（ID: 123）"
        assert exc.data == {"resource": "配置", "resource_id": 123}


class TestPermissionDeniedException:
    """测试PermissionDeniedException"""
    
    def test_permission_denied_default(self):
        """测试默认权限不足异常"""
        exc = PermissionDeniedException()
        
        assert exc.code == status.HTTP_403_FORBIDDEN
        assert exc.message == "权限不足"
        assert exc.data == {"required_permission": None}
    
    def test_permission_denied_with_message(self):
        """测试自定义消息的权限异常"""
        exc = PermissionDeniedException("无权限访问此资源")
        
        assert exc.code == status.HTTP_403_FORBIDDEN
        assert exc.message == "无权限访问此资源"
    
    def test_permission_denied_with_required_permission(self):
        """测试带所需权限的异常"""
        exc = PermissionDeniedException("需要管理员权限", "admin")
        
        assert exc.code == status.HTTP_403_FORBIDDEN
        assert exc.message == "需要管理员权限"
        assert exc.data == {"required_permission": "admin"}


class TestValidationException:
    """测试ValidationException"""
    
    def test_validation_exception_basic(self):
        """测试基本验证异常"""
        exc = ValidationException("数据格式不正确")
        
        assert exc.code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.message == "数据格式不正确"
        assert exc.data == {"field": None, "value": None}
    
    def test_validation_exception_with_field(self):
        """测试带字段信息的验证异常"""
        exc = ValidationException("邮箱格式不正确", field="email", value="invalid-email")
        
        assert exc.code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.message == "邮箱格式不正确"
        assert exc.data == {"field": "email", "value": "invalid-email"}


class TestSystemException:
    """测试SystemException"""
    
    def test_system_exception_default(self):
        """测试默认系统异常"""
        exc = SystemException()
        
        assert exc.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.message == "系统内部错误"
        assert exc.data == {"error_code": None}
    
    def test_system_exception_with_error_code(self):
        """测试带错误代码的系统异常"""
        exc = SystemException("数据库连接失败", "DB_CONNECTION_ERROR")
        
        assert exc.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.message == "数据库连接失败"
        assert exc.data == {"error_code": "DB_CONNECTION_ERROR"}


class TestConfigurationException:
    """测试ConfigurationException"""
    
    def test_configuration_exception_basic(self):
        """测试基本配置异常"""
        exc = ConfigurationException("配置项不存在")
        
        assert exc.code == status.HTTP_400_BAD_REQUEST
        assert exc.message == "配置项不存在"
        assert exc.data == {"config_key": None}
    
    def test_configuration_exception_with_key(self):
        """测试带配置键的异常"""
        exc = ConfigurationException("配置值无效", "database.host")
        
        assert exc.code == status.HTTP_400_BAD_REQUEST
        assert exc.message == "配置值无效"
        assert exc.data == {"config_key": "database.host"}