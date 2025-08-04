#!/usr/bin/env python3
"""
初始化RBAC系统脚本

该脚本创建默认的权限、角色和用户组
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import AsyncSessionLocal
from app.models.rbac import Permission, Role, UserGroup
from app.core.logger import Logger

async def create_default_permissions():
    """创建默认权限"""
    
    default_permissions = [
        # 用户管理权限
        {"name": "查看用户", "code": "user:read", "resource": "user", "action": "read", "description": "查看用户信息"},
        {"name": "创建用户", "code": "user:create", "resource": "user", "action": "create", "description": "创建新用户"},
        {"name": "更新用户", "code": "user:update", "resource": "user", "action": "update", "description": "更新用户信息"},
        {"name": "删除用户", "code": "user:delete", "resource": "user", "action": "delete", "description": "删除用户"},
        {"name": "管理用户角色", "code": "user:manage_roles", "resource": "user", "action": "manage_roles", "description": "管理用户角色分配"},
        
        # 角色管理权限
        {"name": "查看角色", "code": "role:read", "resource": "role", "action": "read", "description": "查看角色信息"},
        {"name": "创建角色", "code": "role:create", "resource": "role", "action": "create", "description": "创建新角色"},
        {"name": "更新角色", "code": "role:update", "resource": "role", "action": "update", "description": "更新角色信息"},
        {"name": "删除角色", "code": "role:delete", "resource": "role", "action": "delete", "description": "删除角色"},
        
        # 权限管理权限
        {"name": "查看权限", "code": "permission:read", "resource": "permission", "action": "read", "description": "查看权限信息"},
        {"name": "创建权限", "code": "permission:create", "resource": "permission", "action": "create", "description": "创建新权限"},
        {"name": "更新权限", "code": "permission:update", "resource": "permission", "action": "update", "description": "更新权限信息"},
        {"name": "删除权限", "code": "permission:delete", "resource": "permission", "action": "delete", "description": "删除权限"},
        
        # 用户组管理权限
        {"name": "查看用户组", "code": "group:read", "resource": "group", "action": "read", "description": "查看用户组信息"},
        {"name": "创建用户组", "code": "group:create", "resource": "group", "action": "create", "description": "创建新用户组"},
        {"name": "更新用户组", "code": "group:update", "resource": "group", "action": "update", "description": "更新用户组信息"},
        {"name": "删除用户组", "code": "group:delete", "resource": "group", "action": "delete", "description": "删除用户组"},
        
        # 知识库管理权限
        {"name": "查看知识库", "code": "kb:read", "resource": "knowledge_base", "action": "read", "description": "查看知识库信息"},
        {"name": "创建知识库", "code": "kb:create", "resource": "knowledge_base", "action": "create", "description": "创建新知识库"},
        {"name": "更新知识库", "code": "kb:update", "resource": "knowledge_base", "action": "update", "description": "更新知识库信息"},
        {"name": "删除知识库", "code": "kb:delete", "resource": "knowledge_base", "action": "delete", "description": "删除知识库"},
        {"name": "训练知识库", "code": "kb:train", "resource": "knowledge_base", "action": "train", "description": "训练知识库"},
        
        # 文档管理权限
        {"name": "查看文档", "code": "document:read", "resource": "document", "action": "read", "description": "查看文档信息"},
        {"name": "上传文档", "code": "document:create", "resource": "document", "action": "create", "description": "上传新文档"},
        {"name": "更新文档", "code": "document:update", "resource": "document", "action": "update", "description": "更新文档信息"},
        {"name": "删除文档", "code": "document:delete", "resource": "document", "action": "delete", "description": "删除文档"},
        
        # 分析统计权限
        {"name": "查看分析报告", "code": "analytics:read", "resource": "analytics", "action": "read", "description": "查看分析统计报告"},
        {"name": "导出分析数据", "code": "analytics:export", "resource": "analytics", "action": "export", "description": "导出分析数据"},
        
        # 健康监控权限
        {"name": "查看健康状态", "code": "health:read", "resource": "health", "action": "read", "description": "查看系统健康状态"},
        {"name": "管理健康检查", "code": "health:manage", "resource": "health", "action": "manage", "description": "管理健康检查配置"},
        {"name": "处理系统警告", "code": "health:alert", "resource": "health", "action": "alert", "description": "处理系统警告"},
        
        # 系统配置权限
        {"name": "查看系统配置", "code": "config:read", "resource": "config", "action": "read", "description": "查看系统配置"},
        {"name": "更新系统配置", "code": "config:update", "resource": "config", "action": "update", "description": "更新系统配置"},
        
        # 聊天管理权限
        {"name": "查看聊天记录", "code": "chat:read", "resource": "chat", "action": "read", "description": "查看聊天记录"},
        {"name": "管理聊天会话", "code": "chat:manage", "resource": "chat", "action": "manage", "description": "管理聊天会话"},
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for perm_data in default_permissions:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(Permission).where(Permission.code == perm_data["code"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    permission = Permission(
                        name=perm_data["name"],
                        code=perm_data["code"],
                        resource=perm_data["resource"],
                        action=perm_data["action"],
                        description=perm_data["description"],
                        is_system=True,
                        is_active=True
                    )
                    db.add(permission)
                    Logger.info(f"创建权限: {perm_data['name']}")
                else:
                    Logger.info(f"权限已存在: {perm_data['name']}")
            
            await db.commit()
            Logger.info("默认权限创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认权限失败: {str(e)}")
            raise

async def create_default_roles():
    """创建默认角色"""
    
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            
            # 获取所有权限
            permissions_result = await db.execute(select(Permission))
            all_permissions = permissions_result.scalars().all()
            permissions_dict = {p.code: p for p in all_permissions}
            
            # 定义角色和对应权限
            roles_config = [
                {
                    "name": "超级管理员",
                    "code": "super_admin",
                    "description": "拥有所有权限的超级管理员",
                    "permissions": list(permissions_dict.keys()),  # 所有权限
                    "priority": 100
                },
                {
                    "name": "系统管理员",
                    "code": "system_admin",
                    "description": "系统管理员，负责用户和系统管理",
                    "permissions": [
                        "user:read", "user:create", "user:update", "user:delete", "user:manage_roles",
                        "role:read", "role:create", "role:update", "role:delete",
                        "group:read", "group:create", "group:update", "group:delete",
                        "analytics:read", "analytics:export",
                        "health:read", "health:manage", "health:alert",
                        "config:read", "config:update"
                    ],
                    "priority": 90
                },
                {
                    "name": "知识库管理员",
                    "code": "kb_admin",
                    "description": "知识库管理员，负责知识库和文档管理",
                    "permissions": [
                        "kb:read", "kb:create", "kb:update", "kb:delete", "kb:train",
                        "document:read", "document:create", "document:update", "document:delete",
                        "chat:read", "chat:manage",
                        "analytics:read"
                    ],
                    "priority": 80
                },
                {
                    "name": "分析师",
                    "code": "analyst",
                    "description": "数据分析师，负责查看分析报告",
                    "permissions": [
                        "analytics:read", "analytics:export",
                        "health:read",
                        "user:read", "kb:read", "document:read", "chat:read"
                    ],
                    "priority": 70
                },
                {
                    "name": "普通用户",
                    "code": "user",
                    "description": "普通用户，基本使用权限",
                    "permissions": [
                        "kb:read", "document:read", "chat:read"
                    ],
                    "priority": 10
                }
            ]
            
            for role_config in roles_config:
                # 检查角色是否已存在
                result = await db.execute(
                    select(Role).where(Role.code == role_config["code"])
                )
                existing_role = result.scalar_one_or_none()
                
                if not existing_role:
                    # 创建角色
                    role = Role(
                        name=role_config["name"],
                        code=role_config["code"],
                        description=role_config["description"],
                        priority=role_config["priority"],
                        is_system=True,
                        is_active=True
                    )
                    db.add(role)
                    await db.flush()
                    
                    # 分配权限 - 使用SQL插入避免异步问题
                    await db.flush()  # 确保role有ID

                    for perm_code in role_config["permissions"]:
                        if perm_code in permissions_dict:
                            permission = permissions_dict[perm_code]
                            # 直接插入关联表
                            from sqlalchemy import text
                            await db.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                                {"role_id": role.id, "permission_id": permission.id}
                            )
                    Logger.info(f"创建角色: {role_config['name']} (权限数: {len(role_config['permissions'])})")
                else:
                    Logger.info(f"角色已存在: {role_config['name']}")
            
            await db.commit()
            Logger.info("默认角色创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认角色失败: {str(e)}")
            raise

async def create_default_groups():
    """创建默认用户组"""
    
    default_groups = [
        {
            "name": "管理员组",
            "code": "admin_group",
            "description": "系统管理员用户组"
        },
        {
            "name": "知识库管理组",
            "code": "kb_manager_group",
            "description": "知识库管理员用户组"
        },
        {
            "name": "普通用户组",
            "code": "user_group",
            "description": "普通用户组"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for group_data in default_groups:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(UserGroup).where(UserGroup.code == group_data["code"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    group = UserGroup(
                        name=group_data["name"],
                        code=group_data["code"],
                        description=group_data["description"],
                        is_active=True
                    )
                    db.add(group)
                    Logger.info(f"创建用户组: {group_data['name']}")
                else:
                    Logger.info(f"用户组已存在: {group_data['name']}")
            
            await db.commit()
            Logger.info("默认用户组创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认用户组失败: {str(e)}")
            raise

async def main():
    """主函数"""
    try:
        Logger.info("开始初始化RBAC系统...")
        
        # 创建默认权限
        await create_default_permissions()
        
        # 创建默认角色
        await create_default_roles()
        
        # 创建默认用户组
        await create_default_groups()
        
        Logger.info("RBAC系统初始化完成!")
        
    except Exception as e:
        Logger.error(f"RBAC初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
