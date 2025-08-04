from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from .base import CustomBaseModel

class PermissionBase(CustomBaseModel):
    """权限基础模型"""
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")

class PermissionCreate(PermissionBase):
    """创建权限请求模型"""
    is_system: bool = Field(False, description="是否为系统权限")
    is_active: bool = Field(True, description="是否激活")

class PermissionUpdate(CustomBaseModel):
    """更新权限请求模型"""
    name: Optional[str] = Field(None, description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: Optional[bool] = Field(None, description="是否激活")

class PermissionResponse(PermissionBase):
    """权限响应模型"""
    id: int = Field(..., description="权限ID")
    is_system: bool = Field(..., description="是否为系统权限")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class RoleBase(CustomBaseModel):
    """角色基础模型"""
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    priority: int = Field(0, description="角色优先级")

class RoleCreate(RoleBase):
    """创建角色请求模型"""
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")
    is_system: bool = Field(False, description="是否为系统角色")
    is_active: bool = Field(True, description="是否激活")

class RoleUpdate(CustomBaseModel):
    """更新角色请求模型"""
    name: Optional[str] = Field(None, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    priority: Optional[int] = Field(None, description="角色优先级")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")
    is_active: Optional[bool] = Field(None, description="是否激活")

class RoleResponse(RoleBase):
    """角色响应模型"""
    id: int = Field(..., description="角色ID")
    is_system: bool = Field(..., description="是否为系统角色")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    permissions: List[PermissionResponse] = Field(default_factory=list, description="权限列表")
    user_count: int = Field(0, description="拥有此角色的用户数量")

class UserGroupBase(CustomBaseModel):
    """用户组基础模型"""
    name: str = Field(..., description="用户组名称")
    code: str = Field(..., description="用户组代码")
    description: Optional[str] = Field(None, description="用户组描述")
    parent_id: Optional[int] = Field(None, description="父用户组ID")

class UserGroupCreate(UserGroupBase):
    """创建用户组请求模型"""
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")
    member_ids: List[int] = Field(default_factory=list, description="成员用户ID列表")
    is_active: bool = Field(True, description="是否激活")

class UserGroupUpdate(CustomBaseModel):
    """更新用户组请求模型"""
    name: Optional[str] = Field(None, description="用户组名称")
    description: Optional[str] = Field(None, description="用户组描述")
    parent_id: Optional[int] = Field(None, description="父用户组ID")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")
    is_active: Optional[bool] = Field(None, description="是否激活")

class UserGroupResponse(UserGroupBase):
    """用户组响应模型"""
    id: int = Field(..., description="用户组ID")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    parent: Optional['UserGroupResponse'] = Field(None, description="父用户组")
    children: List['UserGroupResponse'] = Field(default_factory=list, description="子用户组列表")
    roles: List[RoleResponse] = Field(default_factory=list, description="角色列表")
    member_count: int = Field(0, description="成员数量")

class UserRoleAssignment(CustomBaseModel):
    """用户角色分配模型"""
    user_id: int = Field(..., description="用户ID")
    role_ids: List[int] = Field(..., description="角色ID列表")

class UserGroupMembership(CustomBaseModel):
    """用户组成员关系模型"""
    user_id: int = Field(..., description="用户ID")
    group_ids: List[int] = Field(..., description="用户组ID列表")

class BulkUserOperation(CustomBaseModel):
    """批量用户操作模型"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    operation: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['activate', 'deactivate', 'delete', 'assign_role', 'remove_role', 'add_to_group', 'remove_from_group']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_operations)}')
        return v

class UserImportData(CustomBaseModel):
    """用户导入数据模型"""
    email: str = Field(..., description="邮箱")
    password: Optional[str] = Field(None, description="密码")
    is_admin: bool = Field(False, description="是否为管理员")
    role_codes: List[str] = Field(default_factory=list, description="角色代码列表")
    group_codes: List[str] = Field(default_factory=list, description="用户组代码列表")

class UserImportRequest(CustomBaseModel):
    """用户导入请求模型"""
    users: List[UserImportData] = Field(..., description="用户数据列表")
    send_welcome_email: bool = Field(False, description="是否发送欢迎邮件")
    force_password_reset: bool = Field(True, description="是否强制密码重置")

class UserImportResult(CustomBaseModel):
    """用户导入结果模型"""
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    created_users: List[int] = Field(default_factory=list, description="创建的用户ID列表")

class UserSessionResponse(CustomBaseModel):
    """用户会话响应模型"""
    id: int = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    is_active: bool = Field(..., description="是否活跃")
    last_activity: datetime = Field(..., description="最后活动时间")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(..., description="创建时间")

class UserLoginLogResponse(CustomBaseModel):
    """用户登录日志响应模型"""
    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    email: str = Field(..., description="登录邮箱")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    login_method: str = Field(..., description="登录方式")
    is_successful: bool = Field(..., description="是否成功")
    failure_reason: Optional[str] = Field(None, description="失败原因")
    created_at: datetime = Field(..., description="登录时间")

class UserSecuritySettingsResponse(CustomBaseModel):
    """用户安全设置响应模型"""
    user_id: int = Field(..., description="用户ID")
    two_factor_enabled: bool = Field(..., description="是否启用双因子认证")
    password_changed_at: Optional[datetime] = Field(None, description="密码最后修改时间")
    failed_login_attempts: int = Field(..., description="失败登录尝试次数")
    account_locked_until: Optional[datetime] = Field(None, description="账户锁定到期时间")
    last_password_reset: Optional[datetime] = Field(None, description="最后密码重置时间")

class UserSecuritySettingsUpdate(CustomBaseModel):
    """用户安全设置更新模型"""
    two_factor_enabled: Optional[bool] = Field(None, description="是否启用双因子认证")
    reset_failed_attempts: bool = Field(False, description="是否重置失败尝试次数")
    unlock_account: bool = Field(False, description="是否解锁账户")

class EnhancedUserResponse(CustomBaseModel):
    """增强用户响应模型"""
    id: int = Field(..., description="用户ID")
    email: str = Field(..., description="邮箱")
    is_admin: bool = Field(..., description="是否为管理员")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    roles: List[RoleResponse] = Field(default_factory=list, description="角色列表")
    groups: List[UserGroupResponse] = Field(default_factory=list, description="用户组列表")
    permissions: List[str] = Field(default_factory=list, description="权限代码列表")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(0, description="登录次数")
    session_count: int = Field(0, description="活跃会话数")

# 解决前向引用问题
UserGroupResponse.model_rebuild()
