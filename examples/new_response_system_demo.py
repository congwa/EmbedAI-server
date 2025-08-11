#!/usr/bin/env python3
"""
新响应系统演示脚本

展示如何使用新的异常驱动响应系统。
"""

import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 导入新的异常系统和响应工具
from app.core.exceptions_new import (
    ResourceNotFoundError,
    BusinessError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError
)
from app.core.response_utils import (
    success_response,
    pagination_response,
    created_response,
    no_content_response
)


# 示例数据模型
class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True


class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


# 模拟数据库
users_db = [
    User(id=1, name="Alice", email="alice@example.com"),
    User(id=2, name="Bob", email="bob@example.com"),
    User(id=3, name="Charlie", email="charlie@example.com", is_active=False),
]


# 模拟服务层
class UserService:
    """用户服务层 - 展示异常的正确使用"""
    
    @staticmethod
    async def get_user(user_id: int) -> Optional[User]:
        """获取用户"""
        for user in users_db:
            if user.id == user_id:
                return user
        return None
    
    @staticmethod
    async def get_users(skip: int = 0, limit: int = 10) -> tuple[List[User], int]:
        """获取用户列表"""
        total = len(users_db)
        items = users_db[skip:skip + limit]
        return items, total
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        """创建用户"""
        # 检查邮箱是否已存在
        for user in users_db:
            if user.email == user_data.email:
                raise BusinessError(f"邮箱 {user_data.email} 已被注册")
        
        # 简单的邮箱格式验证
        if "@" not in user_data.email:
            raise ValidationError("邮箱格式无效", field="email", value=user_data.email)
        
        # 创建新用户
        new_id = max(user.id for user in users_db) + 1 if users_db else 1
        new_user = User(
            id=new_id,
            name=user_data.name,
            email=user_data.email
        )
        users_db.append(new_user)
        return new_user
    
    @staticmethod
    async def update_user(user_id: int, user_data: UserUpdate) -> User:
        """更新用户"""
        user = await UserService.get_user(user_id)
        if not user:
            raise ResourceNotFoundError("用户", user_id)
        
        # 更新用户信息
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            # 检查新邮箱是否已被其他用户使用
            for existing_user in users_db:
                if existing_user.id != user_id and existing_user.email == user_data.email:
                    raise BusinessError(f"邮箱 {user_data.email} 已被其他用户使用")
            user.email = user_data.email
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        return user
    
    @staticmethod
    async def delete_user(user_id: int) -> None:
        """删除用户"""
        user = await UserService.get_user(user_id)
        if not user:
            raise ResourceNotFoundError("用户", user_id)
        
        # 检查用户是否可以删除
        if user.id == 1:  # 假设ID为1的用户是系统管理员
            raise BusinessError("系统管理员用户无法删除")
        
        # 从数据库中移除
        users_db.remove(user)


# 模拟API路由函数
async def demo_get_user(user_id: int):
    """获取单个用户 - 展示资源不存在异常"""
    print(f"\n=== 获取用户 {user_id} ===")
    
    try:
        user = await UserService.get_user(user_id)
        if not user:
            raise ResourceNotFoundError("用户", user_id)
        
        response = success_response(data=user.dict(), message="获取用户成功")
        print("✅ 成功响应:")
        print(f"   {response}")
        return response
        
    except ResourceNotFoundError as e:
        print("❌ 异常被抛出:")
        print(f"   类型: {type(e).__name__}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.detail['message']}")
        print(f"   数据: {e.detail['data']}")
        raise  # 在实际应用中，这会被全局异常处理器捕获


async def demo_list_users(page: int = 1, page_size: int = 2):
    """获取用户列表 - 展示分页响应"""
    print(f"\n=== 获取用户列表 (页码: {page}, 每页: {page_size}) ===")
    
    skip = (page - 1) * page_size
    users, total = await UserService.get_users(skip, page_size)
    
    response = pagination_response(
        items=[user.dict() for user in users],
        total=total,
        page=page,
        page_size=page_size,
        message="获取用户列表成功"
    )
    
    print("✅ 分页响应:")
    print(f"   总数: {response['data']['pagination']['total']}")
    print(f"   当前页: {response['data']['pagination']['page']}")
    print(f"   用户数: {len(response['data']['items'])}")
    print(f"   有下一页: {response['data']['pagination']['has_next']}")
    
    return response


async def demo_create_user(name: str, email: str):
    """创建用户 - 展示业务逻辑异常和验证异常"""
    print(f"\n=== 创建用户 {name} ({email}) ===")
    
    try:
        user_data = UserCreate(name=name, email=email)
        new_user = await UserService.create_user(user_data)
        
        response = created_response(
            data=new_user.dict(),
            message="用户创建成功"
        )
        
        print("✅ 创建成功:")
        print(f"   用户ID: {new_user.id}")
        print(f"   用户名: {new_user.name}")
        print(f"   邮箱: {new_user.email}")
        
        return response
        
    except (BusinessError, ValidationError) as e:
        print("❌ 业务异常被抛出:")
        print(f"   类型: {type(e).__name__}")
        print(f"   状态码: {e.status_code}")
        print(f"   消息: {e.detail['message']}")
        if e.detail.get('data'):
            print(f"   额外数据: {e.detail['data']}")
        raise


async def demo_update_user(user_id: int, **updates):
    """更新用户 - 展示资源不存在和业务逻辑异常"""
    print(f"\n=== 更新用户 {user_id} ===")
    print(f"   更新数据: {updates}")
    
    try:
        user_data = UserUpdate(**updates)
        updated_user = await UserService.update_user(user_id, user_data)
        
        response = success_response(
            data=updated_user.dict(),
            message="用户更新成功"
        )
        
        print("✅ 更新成功:")
        print(f"   用户: {updated_user.name} ({updated_user.email})")
        
        return response
        
    except (ResourceNotFoundError, BusinessError) as e:
        print("❌ 异常被抛出:")
        print(f"   类型: {type(e).__name__}")
        print(f"   消息: {e.detail['message']}")
        raise


async def demo_delete_user(user_id: int):
    """删除用户 - 展示业务规则异常"""
    print(f"\n=== 删除用户 {user_id} ===")
    
    try:
        await UserService.delete_user(user_id)
        
        response = no_content_response("用户删除成功")
        
        print("✅ 删除成功")
        return response
        
    except (ResourceNotFoundError, BusinessError) as e:
        print("❌ 异常被抛出:")
        print(f"   类型: {type(e).__name__}")
        print(f"   消息: {e.detail['message']}")
        raise


async def main():
    """主演示函数"""
    print("🚀 新响应系统演示")
    print("=" * 50)
    
    # 1. 成功获取用户
    await demo_get_user(1)
    
    # 2. 获取不存在的用户
    try:
        await demo_get_user(999)
    except ResourceNotFoundError:
        pass  # 异常已在函数中展示
    
    # 3. 分页获取用户列表
    await demo_list_users(page=1, page_size=2)
    await demo_list_users(page=2, page_size=2)
    
    # 4. 成功创建用户
    await demo_create_user("David", "david@example.com")
    
    # 5. 创建重复邮箱用户（业务异常）
    try:
        await demo_create_user("Eve", "alice@example.com")  # 邮箱已存在
    except BusinessError:
        pass
    
    # 6. 创建无效邮箱用户（验证异常）
    try:
        await demo_create_user("Frank", "invalid-email")  # 无效邮箱格式
    except ValidationError:
        pass
    
    # 7. 成功更新用户
    await demo_update_user(2, name="Bob Smith", email="bob.smith@example.com")
    
    # 8. 更新不存在的用户
    try:
        await demo_update_user(999, name="Ghost")
    except ResourceNotFoundError:
        pass
    
    # 9. 尝试删除系统管理员（业务规则异常）
    try:
        await demo_delete_user(1)  # 系统管理员无法删除
    except BusinessError:
        pass
    
    # 10. 成功删除用户
    await demo_delete_user(3)
    
    print("\n" + "=" * 50)
    print("✅ 演示完成！")
    print("\n主要特点:")
    print("- 异常驱动的错误处理")
    print("- 统一的响应格式")
    print("- 清晰的异常类型")
    print("- 丰富的错误上下文信息")
    print("- 自动的全局异常处理")


if __name__ == "__main__":
    asyncio.run(main())