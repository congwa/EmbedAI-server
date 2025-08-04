from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from .base import CustomBaseModel

class TwoFactorMethod(str, Enum):
    """双因子认证方法枚举"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"

class SessionStatus(str, Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPICIOUS = "suspicious"

class SecurityEventType(str, Enum):
    """安全事件类型枚举"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    IP_BLOCKED = "ip_blocked"
    PERMISSION_DENIED = "permission_denied"

class TwoFactorSetupRequest(CustomBaseModel):
    """双因子认证设置请求模型"""
    method: TwoFactorMethod = Field(..., description="认证方法")
    phone_number: Optional[str] = Field(None, description="手机号码")
    email: Optional[str] = Field(None, description="邮箱地址")

class TwoFactorSetupResponse(CustomBaseModel):
    """双因子认证设置响应模型"""
    secret_key: str = Field(..., description="密钥")
    qr_code_url: str = Field(..., description="二维码URL")
    backup_codes: List[str] = Field(..., description="备用验证码")
    method: TwoFactorMethod = Field(..., description="认证方法")

class TwoFactorVerifyRequest(CustomBaseModel):
    """双因子认证验证请求模型"""
    code: str = Field(..., description="验证码")
    backup_code: Optional[str] = Field(None, description="备用验证码")

class TwoFactorStatusResponse(CustomBaseModel):
    """双因子认证状态响应模型"""
    is_enabled: bool = Field(..., description="是否启用")
    method: Optional[TwoFactorMethod] = Field(None, description="认证方法")
    phone_number: Optional[str] = Field(None, description="手机号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    backup_codes_count: int = Field(0, description="剩余备用验证码数量")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")

class SessionResponse(CustomBaseModel):
    """会话响应模型"""
    id: int = Field(..., description="会话ID")
    session_token: str = Field(..., description="会话令牌")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    device_fingerprint: Optional[str] = Field(None, description="设备指纹")
    location: Optional[Dict[str, Any]] = Field(None, description="地理位置")
    status: SessionStatus = Field(..., description="会话状态")
    is_mobile: bool = Field(..., description="是否移动设备")
    is_trusted: bool = Field(..., description="是否受信任设备")
    last_activity: datetime = Field(..., description="最后活动时间")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(..., description="创建时间")

class SessionListResponse(CustomBaseModel):
    """会话列表响应模型"""
    current_session_id: int = Field(..., description="当前会话ID")
    sessions: List[SessionResponse] = Field(..., description="会话列表")
    total_count: int = Field(..., description="总数量")

class SessionTerminateRequest(CustomBaseModel):
    """会话终止请求模型"""
    session_ids: List[int] = Field(..., description="会话ID列表")
    terminate_all: bool = Field(False, description="是否终止所有会话")

class IPWhitelistCreate(CustomBaseModel):
    """IP白名单创建请求模型"""
    ip_address: str = Field(..., description="IP地址")
    ip_range: Optional[str] = Field(None, description="IP范围(CIDR)")
    description: Optional[str] = Field(None, description="描述")
    user_id: Optional[int] = Field(None, description="关联用户ID")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class IPWhitelistUpdate(CustomBaseModel):
    """IP白名单更新请求模型"""
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class IPWhitelistResponse(CustomBaseModel):
    """IP白名单响应模型"""
    id: int = Field(..., description="白名单ID")
    ip_address: str = Field(..., description="IP地址")
    ip_range: Optional[str] = Field(None, description="IP范围")
    description: Optional[str] = Field(None, description="描述")
    user_id: Optional[int] = Field(None, description="关联用户ID")
    is_active: bool = Field(..., description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class IPBlacklistCreate(CustomBaseModel):
    """IP黑名单创建请求模型"""
    ip_address: str = Field(..., description="IP地址")
    ip_range: Optional[str] = Field(None, description="IP范围(CIDR)")
    reason: Optional[str] = Field(None, description="封禁原因")
    block_type: str = Field("manual", description="封禁类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class IPBlacklistUpdate(CustomBaseModel):
    """IP黑名单更新请求模型"""
    reason: Optional[str] = Field(None, description="封禁原因")
    is_active: Optional[bool] = Field(None, description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class IPBlacklistResponse(CustomBaseModel):
    """IP黑名单响应模型"""
    id: int = Field(..., description="黑名单ID")
    ip_address: str = Field(..., description="IP地址")
    ip_range: Optional[str] = Field(None, description="IP范围")
    reason: Optional[str] = Field(None, description="封禁原因")
    block_type: str = Field(..., description="封禁类型")
    failed_attempts: int = Field(..., description="失败尝试次数")
    is_active: bool = Field(..., description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class SecurityEventCreate(CustomBaseModel):
    """安全事件创建请求模型"""
    event_type: SecurityEventType = Field(..., description="事件类型")
    severity: str = Field("info", description="严重程度")
    details: Optional[Dict[str, Any]] = Field(None, description="事件详情")
    risk_score: int = Field(0, description="风险评分")

class SecurityEventResponse(CustomBaseModel):
    """安全事件响应模型"""
    id: int = Field(..., description="事件ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    event_type: str = Field(..., description="事件类型")
    severity: str = Field(..., description="严重程度")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    session_id: Optional[str] = Field(None, description="会话ID")
    details: Optional[Dict[str, Any]] = Field(None, description="事件详情")
    risk_score: int = Field(..., description="风险评分")
    is_resolved: bool = Field(..., description="是否已处理")
    resolved_at: Optional[datetime] = Field(None, description="处理时间")
    resolved_by: Optional[int] = Field(None, description="处理人")
    created_at: datetime = Field(..., description="创建时间")

class SecurityEventResolveRequest(CustomBaseModel):
    """安全事件处理请求模型"""
    event_ids: List[int] = Field(..., description="事件ID列表")
    resolution_note: Optional[str] = Field(None, description="处理说明")

class DeviceFingerprintResponse(CustomBaseModel):
    """设备指纹响应模型"""
    id: int = Field(..., description="指纹ID")
    fingerprint_hash: str = Field(..., description="指纹哈希")
    device_info: Optional[Dict[str, Any]] = Field(None, description="设备信息")
    browser_info: Optional[Dict[str, Any]] = Field(None, description="浏览器信息")
    screen_resolution: Optional[str] = Field(None, description="屏幕分辨率")
    timezone: Optional[str] = Field(None, description="时区")
    language: Optional[str] = Field(None, description="语言")
    is_trusted: bool = Field(..., description="是否受信任")
    last_seen: datetime = Field(..., description="最后见到时间")
    created_at: datetime = Field(..., description="创建时间")

class DeviceTrustRequest(CustomBaseModel):
    """设备信任请求模型"""
    fingerprint_id: int = Field(..., description="指纹ID")
    is_trusted: bool = Field(..., description="是否信任")

class SecurityPolicyCreate(CustomBaseModel):
    """安全策略创建请求模型"""
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    policy_type: str = Field(..., description="策略类型")
    rules: Dict[str, Any] = Field(..., description="策略规则")
    priority: int = Field(0, description="优先级")

class SecurityPolicyUpdate(CustomBaseModel):
    """安全策略更新请求模型"""
    name: Optional[str] = Field(None, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    rules: Optional[Dict[str, Any]] = Field(None, description="策略规则")
    is_active: Optional[bool] = Field(None, description="是否激活")
    priority: Optional[int] = Field(None, description="优先级")

class SecurityPolicyResponse(CustomBaseModel):
    """安全策略响应模型"""
    id: int = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    policy_type: str = Field(..., description="策略类型")
    rules: Dict[str, Any] = Field(..., description="策略规则")
    is_active: bool = Field(..., description="是否激活")
    priority: int = Field(..., description="优先级")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人")

class PasswordChangeRequest(CustomBaseModel):
    """密码修改请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., description="新密码")
    confirm_password: str = Field(..., description="确认密码")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码和确认密码不匹配')
        return v

class SecurityDashboardResponse(CustomBaseModel):
    """安全仪表板响应模型"""
    active_sessions: int = Field(..., description="活跃会话数")
    failed_logins_24h: int = Field(..., description="24小时内失败登录次数")
    blocked_ips: int = Field(..., description="被封禁IP数量")
    security_events_24h: int = Field(..., description="24小时内安全事件数")
    two_factor_enabled_users: int = Field(..., description="启用2FA的用户数")
    suspicious_activities: int = Field(..., description="可疑活动数量")
    recent_events: List[SecurityEventResponse] = Field(..., description="最近安全事件")
    top_risk_ips: List[Dict[str, Any]] = Field(..., description="高风险IP列表")

class SecurityAuditRequest(CustomBaseModel):
    """安全审计请求模型"""
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    event_types: Optional[List[SecurityEventType]] = Field(None, description="事件类型")
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表")
    ip_addresses: Optional[List[str]] = Field(None, description="IP地址列表")
    severity_levels: Optional[List[str]] = Field(None, description="严重程度列表")

class SecurityAuditResponse(CustomBaseModel):
    """安全审计响应模型"""
    total_events: int = Field(..., description="总事件数")
    events_by_type: Dict[str, int] = Field(..., description="按类型统计的事件")
    events_by_severity: Dict[str, int] = Field(..., description="按严重程度统计的事件")
    top_users: List[Dict[str, Any]] = Field(..., description="活跃用户排行")
    top_ips: List[Dict[str, Any]] = Field(..., description="活跃IP排行")
    timeline_data: List[Dict[str, Any]] = Field(..., description="时间线数据")
    risk_analysis: Dict[str, Any] = Field(..., description="风险分析")

class BulkIPOperation(CustomBaseModel):
    """批量IP操作模型"""
    ip_addresses: List[str] = Field(..., description="IP地址列表")
    operation: str = Field(..., description="操作类型")
    reason: Optional[str] = Field(None, description="操作原因")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['whitelist', 'blacklist', 'remove_whitelist', 'remove_blacklist']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_operations)}')
        return v
