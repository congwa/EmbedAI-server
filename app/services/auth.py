from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password
from app.models.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

# 配置OAuth2密码Bearer认证方案，指定token获取的URL端点
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """用户认证函数

    验证用户提供的邮箱和密码是否匹配数据库中的记录

    Args:
        db (Session): 数据库会话
        email (str): 用户邮箱
        password (str): 用户密码

    Returns:
        Optional[User]: 如果认证成功返回用户对象，否则返回None
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """获取当前认证用户

    从请求中获取JWT token并验证，返回对应的用户对象

    Args:
        db (Session): 数据库会话
        token (str): JWT token字符串

    Returns:
        User: 当前认证用户对象

    Raises:
        HTTPException: 当token无效或用户不存在时抛出401认证错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户

    验证当前用户是否具有管理员权限

    Args:
        current_user (User): 当前认证用户对象

    Returns:
        User: 当前管理员用户对象

    Raises:
        HTTPException: 当用户不是管理员时抛出403权限错误
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user