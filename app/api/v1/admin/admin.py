from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.core.response import APIResponse
from app.schemas.admin import AdminRegister
from app.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    AdminChangeUserPasswordRequest,
    UserStatusUpdate
)
from app.services.user import UserService
from app.core.decorators import admin_required

router = APIRouter(tags=["admin"])

@router.post("/register")
async def register_admin(
    admin_data: AdminRegister,
    db: AsyncSession = Depends(get_db)
):
    """管理员注册接口

    通过特殊的注册码创建管理员账户

    Args:
        admin_data (AdminRegister): 包含邮箱、密码和注册码的数据
        db (AsyncSession): 数据库会话对象

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
        stmt = select(User).where(User.email == admin_data.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
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
            await db.commit()
            await db.refresh(user)
        except Exception as e:
            await db.rollback()
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建普通用户

    创建一个新的普通用户，只有管理员可以执行此操作。
    系统会自动为新用户生成SDK密钥和密钥对。

    Args:
        user_data (UserCreate): 用户创建模型，包含email和password信息
        db (AsyncSession): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含创建成功的用户信息的响应对象
    """
    user_service = UserService(db)
    result = await user_service.create(user_data, current_user.id)
    # 将SQLAlchemy模型转换为Pydantic模型
    response_data = UserResponse.model_validate(result)
    return APIResponse.success(data=response_data)

@router.get("/users", dependencies=[Depends(get_current_admin_user)])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取用户列表

    获取当前管理员创建的所有普通用户列表，支持分页查询。

    Args:
        page (int): 页码，从1开始
        page_size (int): 每页显示的数量，1-100之间
        db (AsyncSession): 数据库会话对象
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

@router.put("/users/{user_id}/password", dependencies=[Depends(get_current_admin_user)])
async def admin_change_user_password(
    user_id: int,
    password_in: AdminChangeUserPasswordRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员修改普通用户密码
    
    Args:
        user_id: 要修改密码的用户ID
        password_in: 新密码信息
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        APIResponse: 修改结果
        
    Raises:
        HTTPException: 当用户不存在或操作失败时抛出相应的错误
    """
    user_service = UserService(db)
    try:
        success = await user_service.admin_change_user_password(user_id, password_in.new_password)
        if success:
            return APIResponse.success(message="Password updated successfully")
        return APIResponse.error(code=400, message="Failed to update password")
    except Exception as e:
        return APIResponse.error(code=400, message=str(e))

@router.put("/users/{user_id}/status", dependencies=[Depends(get_current_admin_user)])
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户状态

    管理员可以通过此接口启用或禁用用户账户。

    Args:
        user_id (int): 要更新状态的用户ID
        status_update (UserStatusUpdate): 状态更新信息
        current_user (User): 当前管理员用户
        db (AsyncSession): 数据库会话

    Returns:
        APIResponse: 更新结果
        
    Raises:
        HTTPException: 当用户不存在或操作失败时抛出相应的错误
    """
    user_service = UserService(db)
    try:
        user = await user_service.update_user_status(user_id, status_update.is_active)
        if user:
            return APIResponse.success(
                message="User status updated successfully",
                data={"id": user.id, "is_active": user.is_active}
            )
        return APIResponse.error(code=404, message="User not found")
    except Exception as e:
        return APIResponse.error(code=400, message=str(e))

@router.post("/users/{user_id}/reset-keys", dependencies=[Depends(get_current_admin_user)])
async def reset_user_keys(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """重置用户的SDK密钥和密钥对

    管理员可以通过此接口重置用户的SDK密钥和密钥对。

    Args:
        user_id (int): 要重置密钥的用户ID
        current_user (User): 当前管理员用户
        db (AsyncSession): 数据库会话

    Returns:
        APIResponse: 重置结果
        
    Raises:
        HTTPException: 当用户不存在或操作失败时抛出相应的错误
    """
    user_service = UserService(db)
    try:
        user = await user_service.reset_user_keys(user_id)
        if user:
            return APIResponse.success(
                message="User keys reset successfully",
                data=UserResponse.model_validate(user)
            )
        return APIResponse.error(code=404, message="User not found")
    except Exception as e:
        return APIResponse.error(code=400, message=str(e)) 