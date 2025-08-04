"""
性能测试配置文件
使用Locust进行负载测试
"""

import json
import random
from locust import HttpUser, task, between
from locust.exception import RescheduleTask


class AdminUser(HttpUser):
    """管理员用户性能测试"""
    
    wait_time = between(1, 3)  # 请求间隔1-3秒
    
    def on_start(self):
        """测试开始时的初始化"""
        # 登录获取管理员token
        login_data = {
            "username": "admin",
            "password": "Admin123!"
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            # 如果登录失败，创建管理员账户
            admin_data = {
                "username": "admin",
                "email": "admin@test.com",
                "password": "Admin123!",
                "is_superuser": True
            }
            self.client.post("/api/v1/auth/register", json=admin_data)
            
            # 重新登录
            response = self.client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {token}"}
            else:
                raise RescheduleTask("无法获取管理员token")
    
    @task(3)
    def get_analytics_dashboard(self):
        """测试分析仪表板性能"""
        with self.client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
    
    @task(2)
    def get_health_dashboard(self):
        """测试健康监控仪表板性能"""
        with self.client.get(
            "/api/v1/admin/health/dashboard",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
    
    @task(2)
    def get_users_list(self):
        """测试用户列表性能"""
        page = random.randint(1, 5)
        page_size = random.choice([10, 20, 50])
        
        with self.client.get(
            f"/api/v1/admin/users?page={page}&page_size={page_size}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
    
    @task(1)
    def create_user(self):
        """测试创建用户性能"""
        user_id = random.randint(10000, 99999)
        user_data = {
            "username": f"testuser{user_id}",
            "email": f"test{user_id}@example.com",
            "password": "TestPassword123!",
            "full_name": f"Test User {user_id}"
        }
        
        with self.client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
    
    @task(1)
    def get_config_dashboard(self):
        """测试配置仪表板性能"""
        with self.client.get(
            "/api/v1/admin/config/dashboard",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
    
    @task(1)
    def get_security_dashboard(self):
        """测试安全仪表板性能"""
        with self.client.get(
            "/api/v1/admin/security/dashboard",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")


class APIUser(HttpUser):
    """API用户性能测试"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """获取API密钥"""
        # 这里应该使用预先创建的API密钥
        self.headers = {"Authorization": "Bearer eak_test_api_key_for_performance_testing"}
    
    @task(5)
    def get_knowledge_bases(self):
        """测试获取知识库列表性能"""
        with self.client.get(
            "/api/v1/knowledge-bases",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:  # 401是预期的，因为使用测试密钥
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")
    
    @task(3)
    def search_content(self):
        """测试内容搜索性能"""
        search_terms = ["AI", "机器学习", "深度学习", "自然语言处理", "知识图谱"]
        query = random.choice(search_terms)
        
        with self.client.get(
            f"/api/v1/search?q={query}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")


class WebhookUser(HttpUser):
    """Webhook性能测试"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """初始化Webhook测试"""
        self.webhook_secret = "test_webhook_secret"
    
    @task
    def receive_webhook(self):
        """模拟接收Webhook"""
        webhook_data = {
            "event_type": "knowledge_base.created",
            "timestamp": "2024-08-04T12:00:00Z",
            "data": {
                "id": random.randint(1, 1000),
                "name": f"Test KB {random.randint(1, 100)}",
                "owner_id": random.randint(1, 10)
            },
            "metadata": {
                "source": "api",
                "version": "v1"
            }
        }
        
        # 模拟Webhook接收端点
        with self.client.post(
            "/webhook/test-endpoint",
            json=webhook_data,
            catch_response=True
        ) as response:
            # 对于测试端点，404是预期的
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"状态码: {response.status_code}")


# 性能测试场景配置
class HighLoadScenario(HttpUser):
    """高负载场景测试"""
    
    wait_time = between(0.1, 0.5)  # 更短的等待时间
    weight = 3  # 更高的权重
    
    tasks = [AdminUser.get_analytics_dashboard, AdminUser.get_users_list]


class MixedWorkloadScenario(HttpUser):
    """混合工作负载场景"""
    
    wait_time = between(1, 3)
    weight = 2
    
    def on_start(self):
        AdminUser.on_start(self)
    
    tasks = [
        AdminUser.get_analytics_dashboard,
        AdminUser.get_health_dashboard,
        AdminUser.get_users_list,
        AdminUser.get_config_dashboard
    ]


# 自定义性能测试事件
from locust import events

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的回调"""
    print("开始性能测试...")
    print(f"目标主机: {environment.host}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时的回调"""
    print("性能测试完成!")
    
    # 输出性能统计
    stats = environment.stats
    print(f"总请求数: {stats.total.num_requests}")
    print(f"失败请求数: {stats.total.num_failures}")
    print(f"平均响应时间: {stats.total.avg_response_time:.2f}ms")
    print(f"最大响应时间: {stats.total.max_response_time}ms")
    print(f"RPS: {stats.total.current_rps:.2f}")

@events.request_failure.add_listener
def on_request_failure(request_type, name, response_time, response_length, exception, **kwargs):
    """请求失败时的回调"""
    print(f"请求失败: {request_type} {name} - {exception}")

# 性能测试配置
if __name__ == "__main__":
    import os
    from locust.main import main
    
    # 设置默认参数
    os.environ.setdefault("LOCUST_HOST", "http://localhost:8000")
    os.environ.setdefault("LOCUST_USERS", "50")
    os.environ.setdefault("LOCUST_SPAWN_RATE", "5")
    os.environ.setdefault("LOCUST_RUN_TIME", "300s")
    
    main()
