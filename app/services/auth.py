from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import verify_password, verify_signature
from app.models.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData
from datetime import datetime, timedelta

# 配置OAuth2密码Bearer认证方案，指定token获取的URL端点
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/admin/login",
    auto_error=True  # 当请求没有token时自动返回401错误
)

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """用户认证函数

    验证用户提供的邮箱和密码是否匹配数据库中的记录

    Args:
        db (AsyncSession): 数据库会话
        email (str): 用户邮箱
        password (str): 用户密码

    Returns:
        Optional[User]: 如果认证成功返回用户对象，否则返回None
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户

    从token中解析用户信息并验证用户是否存在

    Args:
        token (str): JWT token
        db (AsyncSession): 数据库会话

    Returns:
        User: 当前用户对象

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

    stmt = select(User).where(User.email == token_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
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

async def verify_sdk_auth(headers: dict, body_str: str) -> tuple[bool, Optional[User], Optional[str]]:
    """验证SDK认证信息

    验证SDK密钥、时间戳、随机数和签名是否有效

    Args:
        headers (dict): 包含SDK认证信息的请求头字典
        body_str (str): 请求体字符串

    Returns:
        tuple[bool, Optional[User], Optional[str]]: 
            - 验证是否成功
            - 如果成功，返回用户对象；否则返回None
            - 如果失败，返回错误信息；否则返回None
    """
    # 验证必要的请求头
    if not all(headers.values()):
        return False, None, "Missing required SDK authentication headers"

    # 验证时间戳（5分钟有效期）
    try:
        ts = int(headers['timestamp'])
        current_time = datetime.now().timestamp()
        if abs(current_time - ts) > 300:
            return False, None, "Request timestamp expired"
    except ValueError:
        return False, None, "Invalid timestamp format"

    # 获取数据库会话并查找用户
    db: AsyncSession = next(get_db())
    user = db.query(User).filter(User.sdk_key == headers['sdk_key']).first()

    if not user or not user.secret_key:
        return False, None, "Invalid SDK key"

    # 验证签名
    if not verify_signature(
        headers['timestamp'],
        headers['nonce'],
        body_str,
        user.secret_key,
        headers['signature']
    ):
        return False, None, "Invalid signature"

    return True, user, None