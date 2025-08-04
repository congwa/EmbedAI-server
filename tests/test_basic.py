"""
基础测试 - 验证系统基本功能
"""

import pytest
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash, verify_password
from app.core.config import settings


@pytest.mark.unit
def test_password_hashing():
    """测试密码哈希功能"""
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    
    # 验证哈希后的密码不等于原密码
    assert hashed != password
    
    # 验证密码验证功能
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.unit
def test_config_loading():
    """测试配置加载"""
    # 验证基本配置项存在
    assert hasattr(settings, 'DATABASE_URL')
    assert hasattr(settings, 'SECRET_KEY')
    
    # 验证配置值不为空
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) > 0


@pytest.mark.unit
def test_imports():
    """测试关键模块导入"""
    try:
        from app.models.user import User
        from app.models.knowledge_base import KnowledgeBase
        from app.services.user import UserService
        from app.services.analytics import AnalyticsService
        from app.services.health_monitor import HealthService
        from app.services.security import SecurityService
        from app.services.config import ConfigService
        from app.services.content import ContentService
        from app.services.integration import IntegrationService
        
        # 如果能成功导入，测试通过
        assert True
        
    except ImportError as e:
        pytest.fail(f"导入失败: {e}")


@pytest.mark.unit
def test_database_models():
    """测试数据库模型定义"""
    from app.models.user import User
    from app.models.knowledge_base import KnowledgeBase
    
    # 验证模型有必要的属性
    assert hasattr(User, '__tablename__')
    assert hasattr(User, 'id')
    assert hasattr(User, 'username')
    assert hasattr(User, 'email')
    
    assert hasattr(KnowledgeBase, '__tablename__')
    assert hasattr(KnowledgeBase, 'id')
    assert hasattr(KnowledgeBase, 'name')


@pytest.mark.unit
def test_schemas():
    """测试数据验证模式"""
    from app.schemas.user import UserCreate, UserResponse
    from app.schemas.knowledge_base import KnowledgeBaseCreate
    
    # 测试用户创建模式
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
    
    user_create = UserCreate(**user_data)
    assert user_create.username == "testuser"
    assert user_create.email == "test@example.com"
    assert user_create.password == "TestPassword123!"
    
    # 测试知识库创建模式
    kb_data = {
        "name": "Test KB",
        "description": "Test knowledge base"
    }
    
    kb_create = KnowledgeBaseCreate(**kb_data)
    assert kb_create.name == "Test KB"
    assert kb_create.description == "Test knowledge base"


@pytest.mark.unit
def test_response_models():
    """测试响应模型"""
    from app.core.response import APIResponse
    
    # 测试成功响应
    success_response = APIResponse.success(data={"test": "data"}, message="操作成功")
    response_dict = success_response.model_dump()
    
    assert response_dict["success"] is True
    assert response_dict["data"]["test"] == "data"
    assert response_dict["message"] == "操作成功"
    
    # 测试错误响应
    error_response = APIResponse.error(message="操作失败", code=400)
    error_dict = error_response.model_dump()
    
    assert error_dict["success"] is False
    assert error_dict["message"] == "操作失败"
    assert error_dict["code"] == 400


@pytest.mark.unit
def test_logger():
    """测试日志功能"""
    from app.core.logger import Logger
    
    # 验证Logger有必要的方法
    assert hasattr(Logger, 'info')
    assert hasattr(Logger, 'error')
    assert hasattr(Logger, 'warning')
    assert hasattr(Logger, 'debug')
    
    # 测试日志记录（不会实际输出到文件）
    try:
        Logger.info("测试信息日志")
        Logger.error("测试错误日志")
        Logger.warning("测试警告日志")
        Logger.debug("测试调试日志")
        assert True
    except Exception as e:
        pytest.fail(f"日志记录失败: {e}")


@pytest.mark.unit
def test_enums():
    """测试枚举定义"""
    from app.models.enums import UserRole, DocumentType, TrainingStatus
    
    # 验证用户角色枚举
    assert hasattr(UserRole, 'USER')
    assert hasattr(UserRole, 'ADMIN')
    assert hasattr(UserRole, 'SUPER_ADMIN')
    
    # 验证文档类型枚举
    assert hasattr(DocumentType, 'PDF')
    assert hasattr(DocumentType, 'DOCX')
    assert hasattr(DocumentType, 'TXT')
    
    # 验证训练状态枚举
    assert hasattr(TrainingStatus, 'PENDING')
    assert hasattr(TrainingStatus, 'TRAINING')
    assert hasattr(TrainingStatus, 'COMPLETED')
    assert hasattr(TrainingStatus, 'FAILED')


@pytest.mark.unit
def test_exceptions():
    """测试自定义异常"""
    from app.core.exceptions import (
        EmbedAIException,
        ValidationError,
        AuthenticationError,
        AuthorizationError,
        NotFoundError
    )
    
    # 测试基础异常
    try:
        raise EmbedAIException("测试异常")
    except EmbedAIException as e:
        assert str(e) == "测试异常"
    
    # 测试验证错误
    try:
        raise ValidationError("验证失败")
    except ValidationError as e:
        assert str(e) == "验证失败"
    
    # 测试认证错误
    try:
        raise AuthenticationError("认证失败")
    except AuthenticationError as e:
        assert str(e) == "认证失败"


@pytest.mark.unit
def test_utilities():
    """测试工具函数"""
    from app.utils.rate_limit import RateLimiter
    
    # 验证速率限制器存在
    assert RateLimiter is not None
    
    # 可以添加更多工具函数测试


if __name__ == "__main__":
    # 运行基础测试
    pytest.main([__file__, "-v"])
