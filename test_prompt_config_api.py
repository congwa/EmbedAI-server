#!/usr/bin/env python3
"""
测试提示词管理配置API接口

这个脚本用于测试新添加的提示词管理配置接口是否正常工作
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/admin/config"

# 测试用的管理员凭据（需要根据实际情况调整）
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

class ConfigAPITester:
    """配置API测试器"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self) -> bool:
        """登录获取认证token"""
        try:
            login_url = f"{BASE_URL}/api/v1/auth/login"
            async with self.session.post(login_url, json=ADMIN_CREDENTIALS) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("data", {}).get("access_token")
                    print(f"✅ 登录成功，获取到token: {self.auth_token[:20]}...")
                    return True
                else:
                    print(f"❌ 登录失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    async def test_get_prompt_config(self):
        """测试获取提示词配置"""
        print("\n🧪 测试获取提示词配置...")
        try:
            url = f"{API_BASE}/prompt"
            async with self.session.get(url, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 获取提示词配置成功")
                    print(f"   配置内容: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    return data['data']
                else:
                    print(f"❌ 获取提示词配置失败: {response.status}")
                    text = await response.text()
                    print(f"   错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 获取提示词配置异常: {str(e)}")
            return None
    
    async def test_update_prompt_config(self):
        """测试更新提示词配置"""
        print("\n🧪 测试更新提示词配置...")
        try:
            url = f"{API_BASE}/prompt"
            update_data = {
                "max_length": 60000,
                "max_variables": 60,
                "enable_analytics": True
            }
            
            async with self.session.put(url, json=update_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 更新提示词配置成功")
                    print(f"   更新后配置: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    return data['data']
                else:
                    print(f"❌ 更新提示词配置失败: {response.status}")
                    text = await response.text()
                    print(f"   错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 更新提示词配置异常: {str(e)}")
            return None
    
    async def test_validate_prompt_config(self):
        """测试验证提示词配置"""
        print("\n🧪 测试验证提示词配置...")
        try:
            url = f"{API_BASE}/prompt/validate"
            test_config = {
                "max_length": 50000,
                "max_variables": 50,
                "version_limit": 100,
                "cache_ttl": 3600,
                "enable_analytics": True
            }
            
            async with self.session.post(url, json=test_config, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 验证提示词配置成功")
                    print(f"   验证结果: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    return data['data']
                else:
                    print(f"❌ 验证提示词配置失败: {response.status}")
                    text = await response.text()
                    print(f"   错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 验证提示词配置异常: {str(e)}")
            return None
    
    async def test_get_prompt_options(self):
        """测试获取提示词配置选项"""
        print("\n🧪 测试获取提示词配置选项...")
        try:
            url = f"{API_BASE}/prompt/options"
            async with self.session.get(url, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 获取提示词配置选项成功")
                    print(f"   配置选项: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    return data['data']
                else:
                    print(f"❌ 获取提示词配置选项失败: {response.status}")
                    text = await response.text()
                    print(f"   错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 获取提示词配置选项异常: {str(e)}")
            return None
    
    async def test_get_rag_config(self):
        """测试获取RAG配置"""
        print("\n🧪 测试获取RAG配置...")
        try:
            url = f"{API_BASE}/rag"
            async with self.session.get(url, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 获取RAG配置成功")
                    print(f"   配置内容: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    return data['data']
                else:
                    print(f"❌ 获取RAG配置失败: {response.status}")
                    text = await response.text()
                    print(f"   错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 获取RAG配置异常: {str(e)}")
            return None
    
    async def test_update_rag_config(self):
        """测试更新RAG配置"""
        print("\n🧪 测试更新RAG配置...")
        try:
            url = f"{API_BASE}/rag"
            update_data = {
                "chunk_size": 1200,
                "chunk_overlap": 250,
                "use_rerank": True
            }
            
            async with self.session.put(url, json=update_data, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 更新RAG配置成功")
                    print(f"   更新后配置: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    return data['data']
                else:
                    print(f"❌ 更新RAG配置失败: {response.status}")
                    text = await response.text()
                    print(f"   错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 更新RAG配置异常: {str(e)}")
            return None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始测试配置管理API接口...")
        
        # 登录
        if not await self.login():
            print("❌ 无法登录，测试终止")
            return
        
        # 测试提示词配置相关接口
        await self.test_get_prompt_config()
        await self.test_get_prompt_options()
        await self.test_validate_prompt_config()
        await self.test_update_prompt_config()
        
        # 测试RAG配置相关接口
        await self.test_get_rag_config()
        await self.test_update_rag_config()
        
        print("\n✨ 所有测试完成！")

async def main():
    """主函数"""
    async with ConfigAPITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    print("配置管理API测试工具")
    print("=" * 50)
    asyncio.run(main())