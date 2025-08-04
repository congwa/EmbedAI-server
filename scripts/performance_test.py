#!/usr/bin/env python3
"""
性能测试脚本
测试系统关键功能的性能表现
"""

import asyncio
import time
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class PerformanceTest:
    """性能测试类"""
    
    def __init__(self):
        self.results = {}
    
    async def time_function(self, func, *args, **kwargs):
        """测量函数执行时间"""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            end_time = time.time()
            return end_time - start_time, True, result
        except Exception as e:
            end_time = time.time()
            return end_time - start_time, False, str(e)
    
    async def run_performance_test(self, test_name: str, func, iterations: int = 10, *args, **kwargs):
        """运行性能测试"""
        print(f"🚀 运行性能测试: {test_name} ({iterations}次迭代)")
        
        times = []
        success_count = 0
        errors = []
        
        for i in range(iterations):
            duration, success, result = await self.time_function(func, *args, **kwargs)
            times.append(duration)
            
            if success:
                success_count += 1
            else:
                errors.append(result)
            
            if (i + 1) % max(1, iterations // 10) == 0:
                print(f"  进度: {i + 1}/{iterations}")
        
        # 计算统计信息
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        success_rate = (success_count / iterations) * 100
        
        self.results[test_name] = {
            "iterations": iterations,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "median_time": median_time,
            "success_rate": success_rate,
            "errors": errors[:5]  # 只保留前5个错误
        }
        
        print(f"✅ {test_name} 完成:")
        print(f"   平均时间: {avg_time*1000:.2f}ms")
        print(f"   最小时间: {min_time*1000:.2f}ms")
        print(f"   最大时间: {max_time*1000:.2f}ms")
        print(f"   中位数: {median_time*1000:.2f}ms")
        print(f"   成功率: {success_rate:.1f}%")
        if errors:
            print(f"   错误示例: {errors[0]}")
        print()
    
    def test_password_hashing(self):
        """测试密码哈希性能"""
        from app.core.security import get_password_hash
        return get_password_hash("TestPassword123!")
    
    def test_password_verification(self):
        """测试密码验证性能"""
        from app.core.security import get_password_hash, verify_password
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        return verify_password(password, hashed)
    
    async def test_database_session_creation(self):
        """测试数据库会话创建性能"""
        from app.models.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return db is not None
    
    async def test_service_initialization(self):
        """测试服务初始化性能"""
        from app.models.database import AsyncSessionLocal
        from app.services.user import UserService
        from app.services.analytics import AnalyticsService
        
        async with AsyncSessionLocal() as db:
            user_service = UserService(db)
            analytics_service = AnalyticsService(db)
            return user_service is not None and analytics_service is not None
    
    def test_schema_validation(self):
        """测试数据验证性能"""
        from app.schemas.user import UserCreate
        from app.schemas.knowledge_base import KnowledgeBaseCreate
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        kb_data = {
            "name": "Test KB",
            "domain": "Test Domain"
        }
        
        user_create = UserCreate(**user_data)
        kb_create = KnowledgeBaseCreate(**kb_data)
        
        return user_create is not None and kb_create is not None
    
    def test_response_model_creation(self):
        """测试响应模型创建性能"""
        from app.core.response import APIResponse
        
        success_response = APIResponse.success(data={"test": "data"})
        error_response = APIResponse.error(message="测试错误")
        
        return success_response is not None and error_response is not None
    
    def test_logger_performance(self):
        """测试日志记录性能"""
        from app.core.logger import Logger
        
        Logger.info("性能测试信息日志")
        Logger.error("性能测试错误日志")
        Logger.warning("性能测试警告日志")
        
        return True
    
    def test_config_access(self):
        """测试配置访问性能"""
        from app.core.config import settings
        
        # 访问多个配置项
        database_url = settings.DATABASE_URL
        secret_key = settings.SECRET_KEY
        
        return database_url is not None and secret_key is not None
    
    def test_model_import(self):
        """测试模型导入性能"""
        from app.models.user import User
        from app.models.knowledge_base import KnowledgeBase
        from app.models.analytics import UserActivityLog
        from app.models.health import SystemMetric
        from app.models.security import IPWhitelist
        from app.models.config import EnvironmentVariable
        from app.models.content import ContentModerationRule
        from app.models.integration import APIKey
        
        return True
    
    def print_summary(self):
        """打印性能测试总结"""
        print("="*80)
        print("📊 性能测试总结报告")
        print("="*80)
        
        total_tests = len(self.results)
        total_avg_time = sum(r["avg_time"] for r in self.results.values())
        overall_success_rate = sum(r["success_rate"] for r in self.results.values()) / total_tests
        
        print(f"总测试数: {total_tests}")
        print(f"总平均时间: {total_avg_time*1000:.2f}ms")
        print(f"整体成功率: {overall_success_rate:.1f}%")
        print()
        
        # 按性能排序
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]["avg_time"]
        )
        
        print("📈 性能排名 (按平均时间):")
        for i, (test_name, result) in enumerate(sorted_results, 1):
            status = "🟢" if result["success_rate"] >= 95 else "🟡" if result["success_rate"] >= 80 else "🔴"
            print(f"{i:2d}. {status} {test_name}")
            print(f"     平均: {result['avg_time']*1000:.2f}ms | 成功率: {result['success_rate']:.1f}%")
        
        print()
        
        # 性能警告
        slow_tests = [name for name, result in self.results.items() if result["avg_time"] > 0.1]
        if slow_tests:
            print("⚠️  性能警告 (>100ms):")
            for test_name in slow_tests:
                result = self.results[test_name]
                print(f"   - {test_name}: {result['avg_time']*1000:.2f}ms")
        
        # 错误警告
        error_tests = [name for name, result in self.results.items() if result["success_rate"] < 100]
        if error_tests:
            print("\n❌ 错误警告:")
            for test_name in error_tests:
                result = self.results[test_name]
                print(f"   - {test_name}: {result['success_rate']:.1f}% 成功率")
                if result["errors"]:
                    print(f"     错误示例: {result['errors'][0]}")
        
        print("="*80)
        
        return overall_success_rate >= 95 and not slow_tests


async def main():
    """主函数"""
    print("🚀 开始EmbedAI性能测试...")
    print()
    
    perf_test = PerformanceTest()
    
    # 运行各种性能测试
    await perf_test.run_performance_test(
        "密码哈希", perf_test.test_password_hashing, 100
    )
    
    await perf_test.run_performance_test(
        "密码验证", perf_test.test_password_verification, 100
    )
    
    await perf_test.run_performance_test(
        "数据库会话创建", perf_test.test_database_session_creation, 50
    )
    
    await perf_test.run_performance_test(
        "服务初始化", perf_test.test_service_initialization, 20
    )
    
    await perf_test.run_performance_test(
        "数据验证", perf_test.test_schema_validation, 1000
    )
    
    await perf_test.run_performance_test(
        "响应模型创建", perf_test.test_response_model_creation, 1000
    )
    
    await perf_test.run_performance_test(
        "日志记录", perf_test.test_logger_performance, 500
    )
    
    await perf_test.run_performance_test(
        "配置访问", perf_test.test_config_access, 1000
    )
    
    await perf_test.run_performance_test(
        "模型导入", perf_test.test_model_import, 100
    )
    
    # 打印总结
    success = perf_test.print_summary()
    
    if success:
        print("\n✅ 性能测试完成 - 系统性能良好!")
        return 0
    else:
        print("\n⚠️ 性能测试完成 - 发现性能问题!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 性能测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 性能测试运行出错: {e}")
        sys.exit(1)
