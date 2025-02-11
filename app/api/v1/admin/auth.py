from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import authenticate_user
from app.core.security import create_access_token
from app.core.response import APIResponse
from app.schemas.user import Token, UserInfo
from app.schemas.auth import OAuth2EmailPasswordRequestForm

router = APIRouter(tags=["admin"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2EmailPasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """管理员登录接口

    验证管理员的邮箱和密码，如果验证成功则生成并返回访问令牌

    Args:
        form_data (OAuth2EmailPasswordRequestForm): 包含邮箱和密码的表单数据
        db (Session): 数据库会话对象

    Returns:
        APIResponse: 包含访问令牌和令牌类型的响应对象

    Raises:
        HTTPException: 当邮箱或密码错误时抛出401认证错误
    """
    user = await authenticate_user(db, form_data.email, form_data.password)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    # 使用 Pydantic 模型创建响应
    print(user.created_at)
    token_response = Token(
        access_token=access_token,
        user=UserInfo(
            id=user.id,
            email=user.email,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
    )
        
    return APIResponse.success(data=token_response.model_dump())