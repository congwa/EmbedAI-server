"""
端到端测试 - 完整工作流程测试
"""

import pytest
import asyncio
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCompleteWorkflows:
    """完整工作流程端到端测试"""
    
    async def test_complete_user_lifecycle(self, async_client: AsyncClient, admin_headers: dict):
        """测试完整的用户生命周期"""
        
        # 1. 创建用户
        user_data = {
            "username": "lifecycle_user",
            "email": "lifecycle@example.com",
            "password": "LifecycleTest123!",
            "full_name": "Lifecycle Test User"
        }
        
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        created_user = response.json()["data"]
        user_id = created_user["id"]
        
        # 2. 验证用户出现在用户列表中
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=admin_headers
        )
        assert response.status_code == 200
        users_list = response.json()["data"]["items"]
        user_found = any(user["id"] == user_id for user in users_list)
        assert user_found, "新创建的用户应该出现在用户列表中"
        
        # 3. 更新用户信息
        update_data = {
            "full_name": "Updated Lifecycle User",
            "is_active": False
        }
        response = await async_client.put(
            f"/api/v1/admin/users/{user_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        updated_user = response.json()["data"]
        assert updated_user["full_name"] == "Updated Lifecycle User"
        assert updated_user["is_active"] is False
        
        # 4. 验证用户状态在分析仪表板中反映
        response = await async_client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        analytics = response.json()["data"]
        assert analytics["total_users"] > 0
        
        # 5. 删除用户
        response = await async_client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 6. 验证用户已被删除
        response = await async_client.get(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 404
    
    async def test_knowledge_base_workflow(self, async_client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """测试知识库完整工作流程"""
        
        # 1. 创建知识库
        kb_data = {
            "name": "E2E Test Knowledge Base",
            "description": "End-to-end test knowledge base"
        }
        
        response = await async_client.post(
            "/api/v1/knowledge-bases",
            json=kb_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        kb = response.json()["data"]
        kb_id = kb["id"]
        
        # 2. 验证知识库在管理仪表板中显示
        response = await async_client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        analytics = response.json()["data"]
        assert analytics["total_knowledge_bases"] > 0
        
        # 3. 更新知识库
        update_data = {
            "name": "Updated E2E Test KB",
            "description": "Updated description"
        }
        response = await async_client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 4. 删除知识库
        response = await async_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    async def test_security_workflow(self, async_client: AsyncClient, admin_headers: dict):
        """测试安全管理工作流程"""
        
        # 1. 检查初始安全状态
        response = await async_client.get(
            "/api/v1/admin/security/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        initial_security = response.json()["data"]
        
        # 2. 添加IP到白名单
        ip_data = {
            "ip_address": "192.168.1.100",
            "description": "E2E Test IP",
            "is_active": True
        }
        response = await async_client.post(
            "/api/v1/admin/security/ip-whitelist",
            json=ip_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        whitelist_entry = response.json()["data"]
        entry_id = whitelist_entry["id"]
        
        # 3. 验证IP出现在白名单中
        response = await async_client.get(
            "/api/v1/admin/security/ip-whitelist",
            headers=admin_headers
        )
        assert response.status_code == 200
        whitelist = response.json()["data"]
        ip_found = any(entry["id"] == entry_id for entry in whitelist)
        assert ip_found, "IP应该出现在白名单中"
        
        # 4. 更新IP白名单条目
        update_data = {
            "description": "Updated E2E Test IP",
            "is_active": False
        }
        response = await async_client.put(
            f"/api/v1/admin/security/ip-whitelist/{entry_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 5. 删除IP白名单条目
        response = await async_client.delete(
            f"/api/v1/admin/security/ip-whitelist/{entry_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_integration_workflow(self, async_client: AsyncClient, admin_headers: dict):
        """测试集成管理工作流程"""
        
        # 1. 创建API密钥
        api_key_data = {
            "name": "E2E Test API Key",
            "description": "End-to-end test API key",
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
        key_id = api_key["id"]
        
        # 2. 验证API密钥在列表中
        response = await async_client.get(
            "/api/v1/admin/integration/api-keys",
            headers=admin_headers
        )
        assert response.status_code == 200
        api_keys = response.json()["data"]
        key_found = any(key["id"] == key_id for key in api_keys)
        assert key_found, "API密钥应该出现在列表中"
        
        # 3. 创建Webhook
        webhook_data = {
            "name": "E2E Test Webhook",
            "description": "End-to-end test webhook",
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
        webhook = response.json()["data"]
        webhook_id = webhook["id"]
        
        # 4. 测试Webhook
        test_data = {
            "event_type": "user.created",
            "test_payload": {
                "test": True,
                "message": "E2E test webhook"
            }
        }
        response = await async_client.post(
            f"/api/v1/admin/integration/webhooks/{webhook_id}/test",
            json=test_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 5. 验证集成仪表板更新
        response = await async_client.get(
            "/api/v1/admin/integration/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        integration_dashboard = response.json()["data"]
        assert integration_dashboard["total_api_keys"] > 0
        assert integration_dashboard["total_webhooks"] > 0
        
        # 6. 清理资源
        await async_client.delete(
            f"/api/v1/admin/integration/api-keys/{key_id}",
            headers=admin_headers
        )
        # Webhook删除API需要实现
    
    async def test_content_management_workflow(self, async_client: AsyncClient, admin_headers: dict):
        """测试内容管理工作流程"""
        
        # 1. 检查内容仪表板
        response = await async_client.get(
            "/api/v1/admin/content/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        content_dashboard = response.json()["data"]
        
        # 2. 获取内容审核规则
        response = await async_client.get(
            "/api/v1/admin/content/moderation/rules",
            headers=admin_headers
        )
        assert response.status_code == 200
        moderation_rules = response.json()["data"]
        assert len(moderation_rules) > 0, "应该有预定义的审核规则"
        
        # 3. 创建内容标签
        tag_data = {
            "name": "E2E测试",
            "description": "端到端测试标签",
            "color": "#ff6b6b",
            "category": "测试"
        }
        response = await async_client.post(
            "/api/v1/admin/content/tags",
            json=tag_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        tag = response.json()["data"]
        tag_id = tag["id"]
        
        # 4. 验证标签在列表中
        response = await async_client.get(
            "/api/v1/admin/content/tags",
            headers=admin_headers
        )
        assert response.status_code == 200
        tags = response.json()["data"]
        tag_found = any(t["id"] == tag_id for t in tags)
        assert tag_found, "标签应该出现在列表中"
        
        # 5. 执行内容搜索
        search_data = {
            "query": "测试",
            "content_types": ["knowledge_base"],
            "sort_by": "relevance",
            "page": 1,
            "page_size": 20
        }
        response = await async_client.post(
            "/api/v1/admin/content/search",
            json=search_data,
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_system_monitoring_workflow(self, async_client: AsyncClient, admin_headers: dict):
        """测试系统监控工作流程"""
        
        # 1. 检查系统健康状态
        response = await async_client.get(
            "/api/v1/admin/health/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        health_dashboard = response.json()["data"]
        assert health_dashboard["system_status"] in ["healthy", "warning", "critical"]
        
        # 2. 获取系统指标
        response = await async_client.get(
            "/api/v1/admin/health/metrics",
            headers=admin_headers
        )
        assert response.status_code == 200
        metrics = response.json()["data"]
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics
        
        # 3. 检查告警规则
        response = await async_client.get(
            "/api/v1/admin/health/alert-rules",
            headers=admin_headers
        )
        assert response.status_code == 200
        alert_rules = response.json()["data"]
        assert len(alert_rules) > 0, "应该有预定义的告警规则"
        
        # 4. 获取系统日志
        response = await async_client.get(
            "/api/v1/admin/health/logs?level=INFO&limit=10",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_configuration_workflow(self, async_client: AsyncClient, admin_headers: dict):
        """测试配置管理工作流程"""
        
        # 1. 检查配置仪表板
        response = await async_client.get(
            "/api/v1/admin/config/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        config_dashboard = response.json()["data"]
        
        # 2. 创建配置项
        config_data = {
            "key": "E2E_TEST_CONFIG",
            "value": "test_value",
            "description": "E2E test configuration",
            "category": "test",
            "is_sensitive": False
        }
        response = await async_client.post(
            "/api/v1/admin/config/environment-variables",
            json=config_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 3. 验证配置项存在
        response = await async_client.get(
            "/api/v1/admin/config/environment-variables",
            headers=admin_headers
        )
        assert response.status_code == 200
        env_vars = response.json()["data"]
        config_found = any(var["key"] == "E2E_TEST_CONFIG" for var in env_vars)
        assert config_found, "配置项应该存在"
        
        # 4. 更新配置项
        update_data = {
            "value": "updated_test_value",
            "description": "Updated E2E test configuration"
        }
        response = await async_client.put(
            "/api/v1/admin/config/environment-variables/E2E_TEST_CONFIG",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 5. 删除配置项
        response = await async_client.delete(
            "/api/v1/admin/config/environment-variables/E2E_TEST_CONFIG",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    async def test_cross_module_integration(self, async_client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """测试跨模块集成"""
        
        # 1. 创建用户并验证在分析中反映
        user_data = {
            "username": "integration_user",
            "email": "integration@example.com",
            "password": "Integration123!"
        }
        response = await async_client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        user = response.json()["data"]
        
        # 2. 验证用户创建事件在安全日志中记录
        await asyncio.sleep(1)  # 等待日志记录
        response = await async_client.get(
            "/api/v1/admin/security/audit-logs?event_type=user_created&limit=10",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # 3. 验证系统健康状态正常
        response = await async_client.get(
            "/api/v1/admin/health/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        health = response.json()["data"]
        assert health["system_status"] != "critical"
        
        # 4. 清理测试数据
        await async_client.delete(
            f"/api/v1/admin/users/{user['id']}",
            headers=admin_headers
        )
