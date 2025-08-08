#!/usr/bin/env python3
"""
提示词配置使用示例

展示如何在应用中使用提示词管理配置
"""

from typing import Dict, Any
from app.services.config_manager import ConfigManager
from app.services.prompt import PromptService
from app.models.database import get_db
from app.core.logger import Logger

class PromptConfigUsageExample:
    """提示词配置使用示例类"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.config_manager = ConfigManager(db_session)
        self.prompt_service = PromptService(db_session)
    
    async def example_1_get_current_config(self):
        """示例1: 获取当前提示词配置"""
        print("=== 示例1: 获取当前提示词配置 ===")
        
        try:
            config = await self.config_manager.get_prompt_config()
            print(f"当前配置: {config}")
            
            # 使用配置中的限制
            max_length = config.get("max_length", 50000)
            max_variables = config.get("max_variables", 50)
            
            print(f"模板最大长度限制: {max_length}")
            print(f"变量数量限制: {max_variables}")
            
        except Exception as e:
            Logger.error(f"获取配置失败: {str(e)}")
    
    async def example_2_validate_template_against_config(self):
        """示例2: 根据配置验证模板"""
        print("\n=== 示例2: 根据配置验证模板 ===")
        
        try:
            # 获取当前配置
            config = await self.config_manager.get_prompt_config()
            max_length = config.get("max_length", 50000)
            max_variables = config.get("max_variables", 50)
            
            # 模拟一个模板
            template_content = "你好，{{name}}！今天是{{date}}，天气{{weather}}。"
            template_variables = [
                {"name": "name", "type": "string", "required": True},
                {"name": "date", "type": "string", "required": True},
                {"name": "weather", "type": "string", "required": False, "default": "晴朗"}
            ]
            
            # 验证模板长度
            if len(template_content) > max_length:
                print(f"❌ 模板长度 {len(template_content)} 超过限制 {max_length}")
                return False
            
            # 验证变量数量
            if len(template_variables) > max_variables:
                print(f"❌ 变量数量 {len(template_variables)} 超过限制 {max_variables}")
                return False
            
            print("✅ 模板验证通过")
            print(f"   模板长度: {len(template_content)}/{max_length}")
            print(f"   变量数量: {len(template_variables)}/{max_variables}")
            
            return True
            
        except Exception as e:
            Logger.error(f"模板验证失败: {str(e)}")
            return False
    
    async def example_3_update_config_for_optimization(self):
        """示例3: 为性能优化更新配置"""
        print("\n=== 示例3: 为性能优化更新配置 ===")
        
        try:
            # 获取当前配置
            current_config = await self.config_manager.get_prompt_config()
            print(f"当前缓存TTL: {current_config.get('cache_ttl', 3600)}秒")
            
            # 为高频使用场景优化缓存时间
            optimization_updates = {
                "cache_ttl": 7200,  # 增加到2小时
                "batch_size": 200,  # 增加批处理大小
                "enable_analytics": True  # 确保启用分析
            }
            
            # 更新配置
            updated_config = await self.config_manager.update_prompt_config(
                config_updates=optimization_updates,
                user_id=1  # 假设管理员用户ID为1
            )
            
            print("✅ 配置优化完成")
            print(f"   新缓存TTL: {updated_config.get('cache_ttl')}秒")
            print(f"   新批处理大小: {updated_config.get('batch_size')}")
            
        except Exception as e:
            Logger.error(f"配置优化失败: {str(e)}")
    
    async def example_4_config_driven_template_creation(self):
        """示例4: 基于配置的模板创建"""
        print("\n=== 示例4: 基于配置的模板创建 ===")
        
        try:
            # 获取配置
            config = await self.config_manager.get_prompt_config()
            
            # 根据配置动态调整模板创建策略
            if config.get("enable_analytics", True):
                print("✅ 分析功能已启用，将记录模板使用情况")
            
            if config.get("enable_auto_optimization", False):
                print("✅ 自动优化已启用，将提供优化建议")
            else:
                print("ℹ️ 自动优化未启用，可在配置中开启")
            
            # 根据版本限制设置版本管理策略
            version_limit = config.get("version_limit", 100)
            print(f"📝 版本管理: 最多保留 {version_limit} 个历史版本")
            
            # 根据保留天数设置清理策略
            retention_days = config.get("retention_days", 90)
            print(f"🗂️ 数据保留: 使用统计数据保留 {retention_days} 天")
            
        except Exception as e:
            Logger.error(f"配置驱动的模板创建失败: {str(e)}")
    
    async def example_5_config_validation_before_update(self):
        """示例5: 更新前的配置验证"""
        print("\n=== 示例5: 更新前的配置验证 ===")
        
        try:
            # 准备要更新的配置
            new_config = {
                "max_length": 80000,
                "max_variables": 75,
                "cache_ttl": 1800,
                "enable_analytics": True
            }
            
            # 验证配置
            validation_result = await self.config_manager.validate_config(
                config_type="prompt",
                config_data=new_config
            )
            
            if validation_result["valid"]:
                print("✅ 配置验证通过")
                print(f"   验证的配置: {validation_result['validated_config']}")
                
                # 如果验证通过，可以安全地更新
                # updated_config = await self.config_manager.update_prompt_config(
                #     config_updates=new_config,
                #     user_id=1
                # )
                print("💡 配置可以安全更新")
                
            else:
                print("❌ 配置验证失败")
                for error in validation_result.get("errors", []):
                    print(f"   错误: {error}")
                
        except Exception as e:
            Logger.error(f"配置验证失败: {str(e)}")
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("🚀 提示词配置使用示例")
        print("=" * 50)
        
        await self.example_1_get_current_config()
        await self.example_2_validate_template_against_config()
        await self.example_3_update_config_for_optimization()
        await self.example_4_config_driven_template_creation()
        await self.example_5_config_validation_before_update()
        
        print("\n✨ 所有示例运行完成！")

# 在知识库服务中集成提示词配置的示例
class KnowledgeBaseWithPromptConfig:
    """集成提示词配置的知识库服务示例"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.config_manager = ConfigManager(db_session)
    
    async def create_optimized_prompt_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建优化的提示词模板"""
        try:
            # 获取当前配置
            config = await self.config_manager.get_prompt_config()
            
            # 根据配置调整模板创建策略
            max_length = config.get("max_length", 50000)
            max_variables = config.get("max_variables", 50)
            
            # 验证模板内容
            content = template_data.get("content", "")
            variables = template_data.get("variables", [])
            
            if len(content) > max_length:
                raise ValueError(f"模板内容长度 {len(content)} 超过配置限制 {max_length}")
            
            if len(variables) > max_variables:
                raise ValueError(f"变量数量 {len(variables)} 超过配置限制 {max_variables}")
            
            # 如果启用了分析，添加使用跟踪
            if config.get("enable_analytics", True):
                template_data["enable_usage_tracking"] = True
            
            # 如果启用了自动优化，添加优化标记
            if config.get("enable_auto_optimization", False):
                template_data["enable_auto_optimization"] = True
            
            Logger.info(f"根据配置创建模板: 长度限制={max_length}, 变量限制={max_variables}")
            return template_data
            
        except Exception as e:
            Logger.error(f"创建优化模板失败: {str(e)}")
            raise
    
    async def get_template_cache_strategy(self) -> Dict[str, Any]:
        """获取模板缓存策略"""
        try:
            config = await self.config_manager.get_prompt_config()
            
            return {
                "cache_ttl": config.get("cache_ttl", 3600),
                "batch_size": config.get("batch_size", 100),
                "enable_cache": True
            }
            
        except Exception as e:
            Logger.error(f"获取缓存策略失败: {str(e)}")
            return {"cache_ttl": 3600, "batch_size": 100, "enable_cache": True}

# 使用示例
async def main():
    """主函数示例"""
    # 注意：在实际使用中，需要正确初始化数据库会话
    # async with get_db() as db:
    #     example = PromptConfigUsageExample(db)
    #     await example.run_all_examples()
    
    print("请在实际的异步环境中运行此示例")
    print("确保已正确配置数据库连接")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())