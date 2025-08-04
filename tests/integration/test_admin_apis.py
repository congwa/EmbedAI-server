"""
管理API集成测试
"""

import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.integration
@pytest.mark.asyncio
class TestAdminAPIs:
    """管理API集成测试类"""
    
    async def test_analytics_dashboard(self, async_client: AsyncClient, admin_headers: dict):
        """测试分析仪表板API"""
        response = await async_client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        dashboard_data = data["data"]
        assert "total_users" in dashboard_data
        assert "active_users" in dashboard_data
        assert "total_knowledge_bases" in dashboard_data
        assert "user_growth" in dashboard_data
    
    async def test_health_dashboard(self, async_client: AsyncClient, admin_headers: dict):
        """测试健康监控仪表板API"""
        response = await async_client.get(
            "/api/v1/admin/health/dashboard",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        health_data = data["data"]
        assert "system_status" in health_data
        assert "database_status" in health_data
        assert "redis_status" in health_data
        assert "disk_usage" in health_data
        assert "memory_usage" in health_data
    
    async def test_user_management_apis(self, async_client: AsyncClient, admin_headers: dict):
        """测试用户管理API"""
        # 获取用户列表
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 创建新用户
        user_data = {
            "username": "apitest",
            "email": "apitest@example.com",
            "password": "ApiTest123!",
            "full_name": "API Test User"
        }
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        created_user = response.json()["data"]
        user_id = created_user["id"]
        
        # 获取用户详情
        response = await async_client.get(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        user_detail = response.json()["data"]
        assert user_detail["username"] == "apitest"
        
        # 更新用户
        update_data = {"full_name": "Updated API Test User"}
        response = await async_client.put(
            f"/api/v1/admin/users/{user_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        updated_user = response.json()["data"]
        assert updated_user["full_name"] == "Updated API Test User"
        
        # 删除用户
        response = await async_client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_config_management_apis(self, async_client: AsyncClient, admin_headers: dict):
        """测试配置管理API"""
        # 获取配置仪表板
        response = await async_client.get(
            "/api/v1/admin/config/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 获取环境变量
        response = await async_client.get(
            "/api/v1/admin/config/environment-variables",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 创建配置项
        config_data = {
            "key": "TEST_CONFIG",
            "value": "test_value",
            "description": "Test configuration",
            "category": "test"
        }
        response = await async_client.post(
            "/api/v1/admin/config/environment-variables",
            json=config_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 更新配置项
        update_data = {"value": "updated_test_value"}
        response = await async_client.put(
            "/api/v1/admin/config/environment-variables/TEST_CONFIG",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_security_apis(self, async_client: AsyncClient, admin_headers: dict):
        """测试安全管理API"""
        # 获取安全仪表板
        response = await async_client.get(
            "/api/v1/admin/security/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 获取IP白名单
        response = await async_client.get(
            "/api/v1/admin/security/ip-whitelist",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 添加IP到白名单
        ip_data = {
            "ip_address": "192.168.1.100",
            "description": "Test IP",
            "is_active": True
        }
        response = await async_client.post(
            "/api/v1/admin/security/ip-whitelist",
            json=ip_data,
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_content_management_apis(self, async_client: AsyncClient, admin_headers: dict):
        """测试内容管理API"""
        # 获取内容仪表板
        response = await async_client.get(
            "/api/v1/admin/content/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 获取内容审核规则
        response = await async_client.get(
            "/api/v1/admin/content/moderation/rules",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 获取内容标签
        response = await async_client.get(
            "/api/v1/admin/content/tags",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_integration_management_apis(self, async_client: AsyncClient, admin_headers: dict):
        """测试集成管理API"""
        # 获取集成仪表板
        response = await async_client.get(
            "/api/v1/admin/integration/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 创建API密钥
        api_key_data = {
            "name": "Test API Key",
            "description": "Test API key for integration testing",
            "scopes": ["read", "write"],
            "rate_limit": 1000
        }
        response = await async_client.post(
            "/api/v1/admin/integration/api-keys",
            json=api_key_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        api_key = response.json()["data"]
        assert "api_key" in api_key
        
        # 获取API密钥列表
        response = await async_client.get(
            "/api/v1/admin/integration/api-keys",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 创建Webhook
        webhook_data = {
            "name": "Test Webhook",
            "description": "Test webhook for integration testing",
            "url": "https://httpbin.org/post",
            "events": ["user.created", "knowledge_base.created"],
            "timeout": 30,
            "retry_count": 3
        }
        response = await async_client.post(
            "/api/v1/admin/integration/webhooks",
            json=webhook_data,
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """测试未授权访问"""
        # 不提供认证头部
        response = await async_client.get("/api/v1/admin/analytics/dashboard")
        assert response.status_code == 401
        
        # 提供无效的认证头部
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=invalid_headers
        )
        assert response.status_code == 401
    
    async def test_non_admin_access(self, async_client: AsyncClient, auth_headers: dict):
        """测试非管理员访问"""
        # 使用普通用户token访问管理API
        response = await async_client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 403  # 应该被拒绝访问
    
    async def test_api_error_handling(self, async_client: AsyncClient, admin_headers: dict):
        """测试API错误处理"""
        # 测试不存在的用户ID
        response = await async_client.get(
            "/api/v1/admin/users/99999",
            headers=admin_headers
        )
        assert response.status_code == 404
        
        # 测试无效的请求数据
        invalid_user_data = {
            "username": "",  # 空用户名
            "email": "invalid-email",  # 无效邮箱
            "password": "123"  # 密码太短
        }
        response = await async_client.post(
            "/api/v1/admin/users",
            json=invalid_user_data,
            headers=admin_headers
        )
        assert response.status_code == 422  # 验证错误
    
    async def test_pagination(self, async_client: AsyncClient, admin_headers: dict):
        """测试分页功能"""
        # 测试用户列表分页
        response = await async_client.get(
            "/api/v1/admin/users?page=1&page_size=10",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        
        # 测试无效分页参数
        response = await async_client.get(
            "/api/v1/admin/users?page=-1&page_size=0",
            headers=admin_headers
        )
        assert response.status_code == 422
