from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.auth import get_current_admin_user, get_current_user
from app.services.security import SecurityService
from app.core.response import APIResponse, ResponseModel
from app.schemas.security import (
    TwoFactorSetupRequest, TwoFactorSetupResponse, TwoFactorVerifyRequest,
    TwoFactorStatusResponse, SessionListResponse, SessionTerminateRequest,
    IPWhitelistCreate, IPWhitelistUpdate, IPWhitelistResponse,
    IPBlacklistCreate, IPBlacklistUpdate, IPBlacklistResponse,
    SecurityEventResponse, SecurityEventResolveRequest,
    DeviceFingerprintResponse, DeviceTrustRequest,
    SecurityPolicyCreate, SecurityPolicyUpdate, SecurityPolicyResponse,
    PasswordChangeRequest, SecurityDashboardResponse,
    SecurityAuditRequest, SecurityAuditResponse, BulkIPOperation
)
from app.models.user import User
from app.core.logger import Logger

router = APIRouter(tags=["admin-security"])

# ==================== 安全仪表板 ====================

@router.get("/dashboard", response_model=ResponseModel[SecurityDashboardResponse])
async def get_security_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取安全仪表板数据"""
    try:
        security_service = SecurityService(db)
        dashboard_data = await security_service.get_security_dashboard()
        return APIResponse.success(data=dashboard_data)
        
    except Exception as e:
        Logger.error(f"获取安全仪表板数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取安全仪表板数据失败")

# ==================== 双因子认证 ====================

@router.post("/2fa/setup", response_model=ResponseModel[TwoFactorSetupResponse])
async def setup_two_factor(
    setup_request: TwoFactorSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """设置双因子认证"""
    try:
        security_service = SecurityService(db)
        setup_response = await security_service.setup_two_factor(current_user.id, setup_request)
        return APIResponse.success(data=setup_response)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"设置双因子认证失败: {str(e)}")
        raise HTTPException(status_code=500, detail="设置双因子认证失败")

@router.post("/2fa/verify", response_model=ResponseModel[bool])
async def verify_two_factor(
    verify_request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """验证双因子认证"""
    try:
        security_service = SecurityService(db)
        is_valid = await security_service.verify_two_factor(current_user.id, verify_request)
        return APIResponse.success(data=is_valid)
        
    except Exception as e:
        Logger.error(f"验证双因子认证失败: {str(e)}")
        raise HTTPException(status_code=500, detail="验证双因子认证失败")

@router.get("/2fa/status", response_model=ResponseModel[TwoFactorStatusResponse])
async def get_two_factor_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取双因子认证状态"""
    try:
        security_service = SecurityService(db)
        status = await security_service.get_two_factor_status(current_user.id)
        return APIResponse.success(data=status)
        
    except Exception as e:
        Logger.error(f"获取双因子认证状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取双因子认证状态失败")

@router.delete("/2fa", response_model=ResponseModel[bool])
async def disable_two_factor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """禁用双因子认证"""
    try:
        security_service = SecurityService(db)
        result = await security_service.disable_two_factor(current_user.id)
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"禁用双因子认证失败: {str(e)}")
        raise HTTPException(status_code=500, detail="禁用双因子认证失败")

# ==================== 会话管理 ====================

@router.get("/sessions", response_model=ResponseModel[SessionListResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户会话列表"""
    try:
        security_service = SecurityService(db)
        sessions = await security_service.get_user_sessions(current_user.id)
        return APIResponse.success(data=sessions)
        
    except Exception as e:
        Logger.error(f"获取用户会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户会话列表失败")

@router.post("/sessions/terminate", response_model=ResponseModel[int])
async def terminate_sessions(
    terminate_request: SessionTerminateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """终止用户会话"""
    try:
        security_service = SecurityService(db)
        terminated_count = await security_service.terminate_sessions(
            user_id=current_user.id,
            session_ids=terminate_request.session_ids,
            terminated_by=current_user.id,
            terminate_all=terminate_request.terminate_all
        )
        return APIResponse.success(data=terminated_count)
        
    except Exception as e:
        Logger.error(f"终止用户会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail="终止用户会话失败")

# ==================== IP控制管理 ====================

@router.post("/ip/whitelist", response_model=ResponseModel[IPWhitelistResponse])
async def add_ip_whitelist(
    whitelist_data: IPWhitelistCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """添加IP白名单"""
    try:
        security_service = SecurityService(db)
        whitelist = await security_service.add_ip_whitelist(whitelist_data, current_admin.id)
        return APIResponse.success(data=whitelist)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"添加IP白名单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加IP白名单失败")

@router.get("/ip/whitelist", response_model=ResponseModel[List[IPWhitelistResponse]])
async def get_ip_whitelist(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取IP白名单列表"""
    try:
        # 这里需要在SecurityService中实现get_ip_whitelist方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取IP白名单列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取IP白名单列表失败")

@router.post("/ip/blacklist", response_model=ResponseModel[IPBlacklistResponse])
async def add_ip_blacklist(
    blacklist_data: IPBlacklistCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """添加IP黑名单"""
    try:
        security_service = SecurityService(db)
        blacklist = await security_service.add_ip_blacklist(blacklist_data, current_admin.id)
        return APIResponse.success(data=blacklist)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"添加IP黑名单失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加IP黑名单失败")

@router.get("/ip/blacklist", response_model=ResponseModel[List[IPBlacklistResponse]])
async def get_ip_blacklist(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取IP黑名单列表"""
    try:
        # 这里需要在SecurityService中实现get_ip_blacklist方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取IP黑名单列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取IP黑名单列表失败")

@router.post("/ip/check", response_model=ResponseModel[dict])
async def check_ip_access(
    ip_address: str = Query(..., description="IP地址"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """检查IP访问权限"""
    try:
        security_service = SecurityService(db)
        is_allowed, reason = await security_service.check_ip_access(ip_address)
        return APIResponse.success(data={
            "ip_address": ip_address,
            "is_allowed": is_allowed,
            "reason": reason
        })
        
    except Exception as e:
        Logger.error(f"检查IP访问权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail="检查IP访问权限失败")

@router.post("/ip/bulk-operation", response_model=ResponseModel[dict])
async def bulk_ip_operation(
    operation: BulkIPOperation,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量IP操作"""
    try:
        security_service = SecurityService(db)
        result = await security_service.bulk_ip_operation(operation, current_admin.id)
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"批量IP操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量IP操作失败")

# ==================== 安全审计 ====================

@router.post("/audit", response_model=ResponseModel[SecurityAuditResponse])
async def generate_security_audit(
    audit_request: SecurityAuditRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """生成安全审计报告"""
    try:
        security_service = SecurityService(db)
        audit_response = await security_service.generate_security_audit(audit_request)
        return APIResponse.success(data=audit_response)
        
    except Exception as e:
        Logger.error(f"生成安全审计报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="生成安全审计报告失败")

@router.get("/events", response_model=ResponseModel[List[SecurityEventResponse]])
async def get_security_events(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    is_resolved: Optional[bool] = Query(None, description="是否已处理"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取安全事件列表"""
    try:
        # 这里需要在SecurityService中实现get_security_events方法
        # 为了简化，暂时返回空列表
        return APIResponse.success(data=[])
        
    except Exception as e:
        Logger.error(f"获取安全事件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取安全事件列表失败")

@router.post("/events/resolve", response_model=ResponseModel[bool])
async def resolve_security_events(
    resolve_request: SecurityEventResolveRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """处理安全事件"""
    try:
        # 这里需要在SecurityService中实现resolve_security_events方法
        # 为了简化，暂时返回True
        return APIResponse.success(data=True)
        
    except Exception as e:
        Logger.error(f"处理安全事件失败: {str(e)}")
        raise HTTPException(status_code=500, detail="处理安全事件失败")

# ==================== 密码安全 ====================

@router.post("/password/change", response_model=ResponseModel[bool])
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    try:
        security_service = SecurityService(db)
        result = await security_service.change_password(
            user_id=current_user.id,
            current_password=password_request.current_password,
            new_password=password_request.new_password
        )
        return APIResponse.success(data=result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="修改密码失败")
