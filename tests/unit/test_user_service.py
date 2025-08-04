"""
用户服务单元测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    """用户服务测试类"""
    
    async def test_create_user(self, db_session: AsyncSession):
        """测试创建用户"""
        user_service = UserService(db_session)
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="Password123!",
            full_name="New User"
        )
        
        user = await user_service.create_user(user_data)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.id is not None
    
    async def test_create_user_duplicate_username(self, db_session: AsyncSession):
        """测试创建重复用户名的用户"""
        user_service = UserService(db_session)
        user_data = UserCreate(
            username="duplicate",
            email="user1@example.com",
            password="Password123!"
        )
        
        # 创建第一个用户
        await user_service.create_user(user_data)
        
        # 尝试创建重复用户名的用户
        user_data2 = UserCreate(
            username="duplicate",
            email="user2@example.com",
            password="Password123!"
        )
        
        with pytest.raises(ValueError, match="用户名已存在"):
            await user_service.create_user(user_data2)
    
    async def test_create_user_duplicate_email(self, db_session: AsyncSession):
        """测试创建重复邮箱的用户"""
        user_service = UserService(db_session)
        user_data = UserCreate(
            username="user1",
            email="duplicate@example.com",
            password="Password123!"
        )
        
        # 创建第一个用户
        await user_service.create_user(user_data)
        
        # 尝试创建重复邮箱的用户
        user_data2 = UserCreate(
            username="user2",
            email="duplicate@example.com",
            password="Password123!"
        )
        
        with pytest.raises(ValueError, match="邮箱已存在"):
            await user_service.create_user(user_data2)
    
    async def test_get_user_by_id(self, db_session: AsyncSession, test_user: User):
        """测试根据ID获取用户"""
        user_service = UserService(db_session)
        
        user = await user_service.get_user(test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    async def test_get_user_by_username(self, db_session: AsyncSession, test_user: User):
        """测试根据用户名获取用户"""
        user_service = UserService(db_session)
        
        user = await user_service.get_user_by_username(test_user.username)
        
        assert user is not None
        assert user.username == test_user.username
        assert user.id == test_user.id
    
    async def test_get_user_by_email(self, db_session: AsyncSession, test_user: User):
        """测试根据邮箱获取用户"""
        user_service = UserService(db_session)
        
        user = await user_service.get_user_by_email(test_user.email)
        
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id
    
    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """测试更新用户"""
        user_service = UserService(db_session)
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )
        
        updated_user = await user_service.update_user(test_user.id, update_data)
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "updated@example.com"
        assert updated_user.username == test_user.username  # 未更新的字段保持不变
    
    async def test_delete_user(self, db_session: AsyncSession, test_user: User):
        """测试删除用户"""
        user_service = UserService(db_session)
        
        result = await user_service.delete_user(test_user.id)
        
        assert result is True
        
        # 验证用户已被删除
        deleted_user = await user_service.get_user(test_user.id)
        assert deleted_user is None
    
    async def test_authenticate_user(self, db_session: AsyncSession):
        """测试用户认证"""
        user_service = UserService(db_session)
        
        # 创建用户
        user_data = UserCreate(
            username="authuser",
            email="auth@example.com",
            password="AuthPassword123!"
        )
        user = await user_service.create_user(user_data)
        
        # 测试正确密码认证
        authenticated_user = await user_service.authenticate_user("authuser", "AuthPassword123!")
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # 测试错误密码认证
        failed_auth = await user_service.authenticate_user("authuser", "WrongPassword")
        assert failed_auth is None
        
        # 测试不存在的用户认证
        nonexistent_auth = await user_service.authenticate_user("nonexistent", "Password123!")
        assert nonexistent_auth is None
    
    async def test_get_users_list(self, db_session: AsyncSession, sample_data):
        """测试获取用户列表"""
        user_service = UserService(db_session)
        
        # 创建多个用户
        for user_data in sample_data["users"]:
            await user_service.create_user(UserCreate(**user_data))
        
        # 测试分页获取
        users = await user_service.get_users(skip=0, limit=10)
        assert len(users) >= 2
        
        # 测试限制数量
        users_limited = await user_service.get_users(skip=0, limit=1)
        assert len(users_limited) == 1
        
        # 测试跳过
        users_skipped = await user_service.get_users(skip=1, limit=10)
        assert len(users_skipped) >= 1
    
    async def test_user_password_hashing(self, db_session: AsyncSession):
        """测试密码哈希"""
        user_service = UserService(db_session)
        user_data = UserCreate(
            username="hashuser",
            email="hash@example.com",
            password="PlainPassword123!"
        )
        
        user = await user_service.create_user(user_data)
        
        # 密码应该被哈希，不应该是明文
        assert user.hashed_password != "PlainPassword123!"
        assert len(user.hashed_password) > 20  # 哈希后的密码应该比较长
        
        # 验证密码验证功能
        from app.core.security import verify_password
        assert verify_password("PlainPassword123!", user.hashed_password) is True
        assert verify_password("WrongPassword", user.hashed_password) is False
    
    async def test_user_status_management(self, db_session: AsyncSession):
        """测试用户状态管理"""
        user_service = UserService(db_session)
        user_data = UserCreate(
            username="statususer",
            email="status@example.com",
            password="Password123!"
        )
        
        user = await user_service.create_user(user_data)
        assert user.is_active is True
        
        # 禁用用户
        update_data = UserUpdate(is_active=False)
        updated_user = await user_service.update_user(user.id, update_data)
        assert updated_user.is_active is False
        
        # 重新启用用户
        update_data = UserUpdate(is_active=True)
        updated_user = await user_service.update_user(user.id, update_data)
        assert updated_user.is_active is True
