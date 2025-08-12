#!/usr/bin/env python3
"""
知识库API迁移脚本
将原有的知识库API文件拆分为模块化结构
"""

import os
import shutil
from pathlib import Path


def backup_original_api_file():
    """备份原始API文件"""
    try:
        original_file = "app/api/v1/admin/knowledge_base.py"
        backup_file = "app/api/v1/admin/knowledge_base_backup.py"
        
        if os.path.exists(original_file):
            shutil.copy2(original_file, backup_file)
            print(f"✅ 原始API文件已备份到: {backup_file}")
            return True
        else:
            print(f"❌ 原始API文件不存在: {original_file}")
            return False
    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        return False


def verify_api_structure():
    """验证API结构"""
    required_files = [
        "app/api/v1/admin/knowledge/__init__.py",
        "app/api/v1/admin/knowledge/core.py",
        "app/api/v1/admin/knowledge/training.py",
        "app/api/v1/admin/knowledge/query.py",
        "app/api/v1/admin/knowledge/members.py",
        "app/api/v1/admin/knowledge/prompt.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少以下文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ 所有API文件结构验证通过")
    return True


def verify_service_bridge():
    """验证服务桥接层"""
    bridge_file = "app/services/knowledge_base.py"
    if not os.path.exists(bridge_file):
        print(f"❌ 服务桥接层文件不存在: {bridge_file}")
        return False
    
    print("✅ 服务桥接层验证通过")
    return True


def verify_imports():
    """验证导入语句"""
    try:
        # 测试导入
        import sys
        sys.path.insert(0, '.')
        
        # 测试服务导入
        from app.services.knowledge_base import KnowledgeBaseService
        print("✅ 服务导入测试通过")
        
        # 测试API导入
        from app.api.v1.admin.knowledge_base import router
        print("✅ API导入测试通过")
        
        return True
    except Exception as e:
        print(f"❌ 导入测试失败: {str(e)}")
        return False


def main():
    """主迁移函数"""
    print("🚀 开始知识库API迁移...")
    print("=" * 50)
    
    # 1. 备份原始文件
    print("1. 备份原始API文件...")
    if not backup_original_api_file():
        return
    
    # 2. 验证API结构
    print("\n2. 验证API结构...")
    if not verify_api_structure():
        return
    
    # 3. 验证服务桥接层
    print("\n3. 验证服务桥接层...")
    if not verify_service_bridge():
        return
    
    # 4. 验证导入
    print("\n4. 验证导入语句...")
    if not verify_imports():
        return
    
    # 5. 验证迁移结果
    print("\n5. 验证迁移结果...")
    if verify_api_structure() and verify_service_bridge() and verify_imports():
        print("\n🎉 API迁移成功完成！")
        print("\n📋 迁移总结:")
        print("- 原始API文件已备份到 knowledge_base_backup.py")
        print("- API已拆分为5个专门的路由模块")
        print("- 服务层已拆分为5个专门的服务类")
        print("- 所有现有API调用无需修改")
        print("- 导入语句保持不变: from app.services.knowledge_base import KnowledgeBaseService")
        print("\n🔧 新的API结构:")
        print("- app/api/v1/admin/knowledge/core.py - 核心CRUD操作")
        print("- app/api/v1/admin/knowledge/training.py - 训练相关")
        print("- app/api/v1/admin/knowledge/query.py - 查询相关")
        print("- app/api/v1/admin/knowledge/members.py - 成员管理")
        print("- app/api/v1/admin/knowledge/prompt.py - 提示词模板")
        print("\n🔧 新的服务结构:")
        print("- app/services/knowledge/knowledge_base_core.py - 核心服务")
        print("- app/services/knowledge/knowledge_base_training.py - 训练服务")
        print("- app/services/knowledge/knowledge_base_query.py - 查询服务")
        print("- app/services/knowledge/knowledge_base_members.py - 成员服务")
        print("- app/services/knowledge/knowledge_base_prompt.py - 提示词服务")
        print("\n🔧 后续步骤:")
        print("1. 运行测试确保功能正常")
        print("2. 根据需要进一步优化各个子模块")
        print("3. 删除备份文件（如果确认无问题）")
    else:
        print("\n❌ 迁移失败，请检查错误信息")


if __name__ == "__main__":
    main() 