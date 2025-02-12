from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.core.response import APIResponse
from app.schemas.admin import AdminRegister
from app.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash
from app.schemas.user import UserCreate
from app.services.user import UserService

router = APIRouter(tags=["admin"])

@router.post("/register")
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
    try:
        # 验证注册码
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
            is_admin=True,
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

        return APIResponse.success(
            message="Admin user created successfully",
            data={
                "id": user.id,
                "email": user.email,
                "is_admin": user.is_admin
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/users", dependencies=[Depends(get_current_admin_user)])
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建普通用户

    创建一个新的普通用户，只有管理员可以执行此操作。
    系统会自动为新用户生成SDK密钥和密钥对。

    Args:
        user_data (UserCreate): 用户创建模型，包含email和password信息
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含创建成功的用户信息的响应对象
    """
    user_service = UserService(db)
    result = await user_service.create(user_data, current_user.id)
    return APIResponse.success(data=result)

@router.get("/users", dependencies=[Depends(get_current_admin_user)])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取用户列表

    获取当前管理员创建的所有普通用户列表，支持分页查询。

    Args:
        page (int): 页码，从1开始
        page_size (int): 每页显示的数量，1-100之间
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含用户列表和分页信息的响应对象
    """
    user_service = UserService(db)
    users, total = await user_service.get_users(page, page_size, current_user.id)
    
    return APIResponse.pagination(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        message="获取用户列表成功"
    )  