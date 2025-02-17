from typing import Optional, List, Tuple
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserListItem
from sqlalchemy.sql import func
from app.core.exceptions import ValidationError

class UserService:
    """用户服务类

    处理用户相关的业务逻辑，包括用户的创建、查询和更新等操作
    """
    def __init__(self, db: AsyncSession):
        """初始化用户服务

        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db

    def _generate_api_keys(self) -> tuple[str, str]:
        """生成SDK密钥和密钥对

        Returns:
            tuple[str, str]: 包含sdk_key和secret_key的元组
        """
        sdk_key = f"sdk_{secrets.token_urlsafe(32)}"
        secret_key = f"sk_{secrets.token_urlsafe(48)}"
        return sdk_key, secret_key

    async def create(self, user_in: UserCreate, created_by_id: Optional[int] = None) -> User:
        """创建新用户

        根据提供的用户信息创建新的用户记录。如果是管理员创建普通用户，
        会自动生成SDK密钥和密钥对。

        Args:
            user_in (UserCreate): 用户创建模型，包含email、password和is_admin信息
            created_by_id (Optional[int]): 创建者的用户ID

        Returns:
            User: 创建成功的用户对象
            
        Raises:
            ValidationError: 当邮箱已存在时抛出验证错误
        """
        # 检查邮箱是否已存在
        stmt = select(User).where(User.email == user_in.email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValidationError(f"Email {user_in.email} is already registered")
            
        sdk_key = None
        secret_key = None
        if not user_in.is_admin and created_by_id:
            sdk_key, secret_key = self._generate_api_keys()

        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_admin=user_in.is_admin,
            created_by_id=created_by_id,
            sdk_key=sdk_key,
            secret_key=secret_key
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查询用户

        Args:
            email (str): 用户邮箱地址

        Returns:
            Optional[User]: 如果用户存在则返回用户对象，否则返回None
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """更新用户信息

        根据提供的信息更新指定用户的记录

        Args:
            user_id (int): 要更新的用户ID
            user_in (UserUpdate): 用户更新模型，包含需要更新的字段

        Returns:
            Optional[User]: 更新成功返回更新后的用户对象，如果用户不存在返回None
        """
        user = await self.db.get(User, user_id)
        if not user:
            return None
            
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        for field, value in update_data.items():
            setattr(user, field, value)
            
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_users(self, page: int, page_size: int, admin_id: int) -> Tuple[List[UserListItem], int]:
        """获取用户列表

        Args:
            page (int): 页码，从1开始
            page_size (int): 每页显示的数量
            admin_id (int): 管理员ID，用于筛选该管理员创建的用户

        Returns:
            Tuple[List[UserListItem], int]: 返回用户列表和总数
        """
        # 构建查询条件：非管理员用户 且 由指定管理员创建
        stmt = select(User).where(
            User.is_admin == False,
            User.created_by_id == admin_id
        )
        
        # 计算总数
        count_stmt = select(func.count()).select_from(stmt)
        total = await self.db.scalar(count_stmt)
        
        # 获取分页数据
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        # 转换为 schema 模型
        user_list = [UserListItem.model_validate(user).model_dump(mode="json") for user in users]
            
        return user_list, total

    async def admin_change_user_password(self, user_id: int, new_password: str) -> bool:
        """管理员修改普通用户密码

        Args:
            user_id (int): 用户ID
            new_password (str): 新密码

        Returns:
            bool: 修改成功返回True，否则返回False
            
        Raises:
            ValidationError: 当用户不存在时抛出验证错误
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValidationError("User not found")
            
        # 更新新密码
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def update_user_status(self, user_id: int, is_active: bool) -> Optional[User]:
        """更新用户状态

        Args:
            user_id (int): 用户ID
            is_active (bool): 是否激活用户

        Returns:
            Optional[User]: 更新成功返回更新后的用户对象，如果用户不存在返回None
            
        Raises:
            ValidationError: 当用户不存在时抛出验证错误
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValidationError("User not found")
            
        user.is_active = is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user