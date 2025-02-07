from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import authenticate_user
from app.core.security import create_access_token, get_password_hash
from app.core.response import APIResponse
from app.schemas.user import Token
from app.schemas.admin import AdminRegister
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/admin/register")
async def register_admin(
    admin_data: AdminRegister,
    db: Session = Depends(get_db)
):
    """管理员注册接口

    通过特殊的注册码创建管理员账户

    Args:
        admin_data (AdminRegister): 包含邮箱、密码和注册码的数据
        db (Session): 数据库会话对象

    Returns:
        APIResponse: 包含注册成功信息的响应对象

    Raises:
        HTTPException: 当注册码无效或邮箱已存在时抛出相应错误
    """
    if admin_data.register_code != settings.ADMIN_REGISTER_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid register code"
        )

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == admin_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建管理员用户
    user = User(
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return APIResponse.success(message="Admin user created successfully")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录接口

    验证用户的邮箱和密码，如果验证成功则生成并返回访问令牌

    Args:
        form_data (OAuth2PasswordRequestForm): 包含用户名(邮箱)和密码的表单数据
        db (Session): 数据库会话对象

    Returns:
        APIResponse: 包含访问令牌和令牌类型的响应对象

    Raises:
        HTTPException: 当用户名或密码错误时抛出401认证错误
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return APIResponse.success(data={
        "access_token": access_token,
        "token_type": "bearer"
    })