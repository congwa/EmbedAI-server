from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.decorators import admin_required
from app.models.database import get_db
from app.models.user import User
from app.schemas.user import AdminChangeUserPasswordRequest
from app.services.user import UserService
from app.core.response import APIResponse

router = APIRouter()

@router.put("/{user_id}/password", response_model=APIResponse)
@admin_required
async def admin_change_user_password(
    user_id: int,
    password_in: AdminChangeUserPasswordRequest,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
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