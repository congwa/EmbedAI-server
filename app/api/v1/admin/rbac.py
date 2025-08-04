from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.services.rbac import RBACService
from app.core.response import APIResponse, ResponseModel
from app.schemas.rbac import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    UserGroupCreate, UserGroupUpdate, UserGroupResponse,
    UserRoleAssignment, UserGroupMembership, BulkUserOperation,
    UserImportRequest, UserImportResult, EnhancedUserResponse
)
from app.models.user import User
from app.core.logger import Logger

router = APIRouter(tags=["admin-rbac"])

# ==================== 权限管理 ====================

@router.post("/permissions", response_model=ResponseModel[PermissionResponse])
async def create_permission(
    permission_data: PermissionCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建权限"""
    try:
        rbac_service = RBACService(db)
        permission = await rbac_service.create_permission(permission_data)
        return APIResponse.success(data=permission)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"创建权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建权限失败")

@router.get("/permissions", response_model=ResponseModel[List[PermissionResponse]])
async def get_permissions(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    resource: Optional[str] = Query(None, description="资源类型"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取权限列表"""
    try:
        rbac_service = RBACService(db)
        permissions = await rbac_service.get_permissions(
            skip=skip, limit=limit, is_active=is_active, resource=resource
        )
        return APIResponse.success(data=permissions)
        
    except Exception as e:
        Logger.error(f"获取权限列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取权限列表失败")

@router.put("/permissions/{permission_id}", response_model=ResponseModel[PermissionResponse])
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新权限"""
    try:
        rbac_service = RBACService(db)
        permission = await rbac_service.update_permission(permission_id, permission_data)
        return APIResponse.success(data=permission)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"更新权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新权限失败")

# ==================== 角色管理 ====================

@router.post("/roles", response_model=ResponseModel[RoleResponse])
async def create_role(
    role_data: RoleCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建角色"""
    try:
        rbac_service = RBACService(db)
        role = await rbac_service.create_role(role_data, current_admin.id)
        return APIResponse.success(data=role)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建角色失败")

@router.get("/roles", response_model=ResponseModel[List[RoleResponse]])
async def get_roles(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取角色列表"""
    try:
        rbac_service = RBACService(db)
        roles = await rbac_service.get_roles(skip=skip, limit=limit, is_active=is_active)
        return APIResponse.success(data=roles)
        
    except Exception as e:
        Logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色列表失败")

@router.put("/roles/{role_id}", response_model=ResponseModel[RoleResponse])
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新角色"""
    try:
        rbac_service = RBACService(db)
        role = await rbac_service.update_role(role_id, role_data)
        return APIResponse.success(data=role)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"更新角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新角色失败")

# ==================== 用户组管理 ====================

@router.post("/groups", response_model=ResponseModel[UserGroupResponse])
async def create_user_group(
    group_data: UserGroupCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建用户组"""
    try:
        rbac_service = RBACService(db)
        group = await rbac_service.create_user_group(group_data, current_admin.id)
        return APIResponse.success(data=group)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"创建用户组失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建用户组失败")

@router.get("/groups", response_model=ResponseModel[List[UserGroupResponse]])
async def get_user_groups(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    parent_id: Optional[int] = Query(None, description="父用户组ID"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户组列表"""
    try:
        rbac_service = RBACService(db)
        groups = await rbac_service.get_user_groups(
            skip=skip, limit=limit, is_active=is_active, parent_id=parent_id
        )
        return APIResponse.success(data=groups)
        
    except Exception as e:
        Logger.error(f"获取用户组列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户组列表失败")

# ==================== 用户角色分配 ====================

@router.post("/users/assign-roles", response_model=ResponseModel[bool])
async def assign_user_roles(
    assignment: UserRoleAssignment,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """分配用户角色"""
    try:
        rbac_service = RBACService(db)
        result = await rbac_service.assign_user_roles(assignment)
        return APIResponse.success(data=result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"分配用户角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="分配用户角色失败")

@router.get("/users/{user_id}/permissions", response_model=ResponseModel[List[str]])
async def get_user_permissions(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户权限列表"""
    try:
        rbac_service = RBACService(db)
        permissions = await rbac_service.get_user_permissions(user_id)
        return APIResponse.success(data=permissions)
        
    except Exception as e:
        Logger.error(f"获取用户权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户权限失败")

@router.get("/users/{user_id}/check-permission/{permission_code}", response_model=ResponseModel[bool])
async def check_user_permission(
    user_id: int,
    permission_code: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """检查用户权限"""
    try:
        rbac_service = RBACService(db)
        has_permission = await rbac_service.check_user_permission(user_id, permission_code)
        return APIResponse.success(data=has_permission)
        
    except Exception as e:
        Logger.error(f"检查用户权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail="检查用户权限失败")

# ==================== 批量操作 ====================

@router.post("/users/bulk-operation", response_model=ResponseModel[dict])
async def bulk_user_operation(
    operation: BulkUserOperation,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量用户操作"""
    try:
        rbac_service = RBACService(db)
        result = await rbac_service.bulk_user_operation(operation)
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"批量用户操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量用户操作失败")

@router.post("/users/import", response_model=ResponseModel[UserImportResult])
async def import_users(
    import_request: UserImportRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量导入用户"""
    try:
        rbac_service = RBACService(db)
        result = await rbac_service.import_users(import_request)
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"批量导入用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量导入用户失败")

@router.get("/users/export")
async def export_users(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """导出用户数据"""
    try:
        rbac_service = RBACService(db)
        csv_data = await rbac_service.export_users_csv()
        
        return StreamingResponse(
            io.BytesIO(csv_data.encode('utf-8-sig')),  # 使用UTF-8 BOM以支持Excel
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users_export.csv"}
        )
        
    except Exception as e:
        Logger.error(f"导出用户数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出用户数据失败")
