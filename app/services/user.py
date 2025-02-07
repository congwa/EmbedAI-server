from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    """用户服务类

    处理用户相关的业务逻辑，包括用户的创建、查询和更新等操作
    """
    def __init__(self, db: Session):
        """初始化用户服务

        Args:
            db (Session): 数据库会话对象
        """
        self.db = db

    async def create(self, user_in: UserCreate) -> User:
        """创建新用户

        根据提供的用户信息创建新的用户记录

        Args:
            user_in (UserCreate): 用户创建模型，包含email、password和is_admin信息

        Returns:
            User: 创建成功的用户对象
        """
        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_admin=user_in.is_admin
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查询用户

        Args:
            email (str): 用户邮箱地址

        Returns:
            Optional[User]: 如果用户存在则返回用户对象，否则返回None
        """
        return self.db.query(User).filter(User.email == email).first()

    async def update(self, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """更新用户信息

        根据提供的信息更新指定用户的记录

        Args:
            user_id (int): 要更新的用户ID
            user_in (UserUpdate): 用户更新模型，包含需要更新的字段

        Returns:
            Optional[User]: 更新成功返回更新后的用户对象，如果用户不存在返回None
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        update_data = user_in.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        for field, value in update_data.items():
            setattr(user, field, value)
            
        self.db.commit()
        self.db.refresh(user)
        return user