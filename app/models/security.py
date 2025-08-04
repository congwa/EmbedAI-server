from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class TwoFactorMethod(enum.Enum):
    """双因子认证方法枚举"""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"    # SMS verification
    EMAIL = "email"  # Email verification

class SessionStatus(enum.Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPICIOUS = "suspicious"

class SecurityEventType(enum.Enum):
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

class TwoFactorAuth(Base):
    """双因子认证模型
    
    存储用户的双因子认证设置和密钥
    """
    __tablename__ = "two_factor_auth"
    __table_args__ = {'comment': '双因子认证表，存储用户的2FA设置'}

    id = Column(Integer, primary_key=True, index=True, comment='2FA ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, comment='用户ID')
    method = Column(String(20), nullable=False, default=TwoFactorMethod.TOTP.value, comment='认证方法')
    secret_key = Column(String(255), nullable=False, comment='密钥')
    backup_codes = Column(JSON, nullable=True, comment='备用验证码')
    is_enabled = Column(Boolean, default=False, comment='是否启用')
    phone_number = Column(String(20), nullable=True, comment='手机号码')
    email = Column(String(255), nullable=True, comment='邮箱地址')
    last_used_at = Column(DateTime, nullable=True, comment='最后使用时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    user = relationship("User", backref="two_factor_auth", uselist=False)
    
    def __repr__(self):
        return f"<TwoFactorAuth(user_id={self.user_id}, method={self.method})>"

class UserSession(Base):
    """用户会话模型
    
    增强的会话管理，包含安全信息
    """
    __tablename__ = "user_sessions_enhanced"
    __table_args__ = {'comment': '增强用户会话表，包含安全信息'}

    id = Column(Integer, primary_key=True, index=True, comment='会话ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    session_token = Column(String(255), nullable=False, unique=True, index=True, comment='会话令牌')
    refresh_token = Column(String(255), nullable=True, unique=True, comment='刷新令牌')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    user_agent = Column(Text, nullable=True, comment='用户代理')
    device_fingerprint = Column(String(255), nullable=True, comment='设备指纹')
    location = Column(JSON, nullable=True, comment='地理位置信息')
    status = Column(String(20), nullable=False, default=SessionStatus.ACTIVE.value, comment='会话状态')
    is_mobile = Column(Boolean, default=False, comment='是否移动设备')
    is_trusted = Column(Boolean, default=False, comment='是否受信任设备')
    last_activity = Column(DateTime, default=datetime.now, comment='最后活动时间')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    terminated_at = Column(DateTime, nullable=True, comment='终止时间')
    terminated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='终止人')
    
    # 关系定义
    user = relationship("User", foreign_keys=[user_id], backref="enhanced_sessions")
    terminated_by_user = relationship("User", foreign_keys=[terminated_by])
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, status={self.status})>"

class IPWhitelist(Base):
    """IP白名单模型
    
    管理允许访问的IP地址
    """
    __tablename__ = "ip_whitelist"
    __table_args__ = {'comment': 'IP白名单表，管理允许访问的IP地址'}

    id = Column(Integer, primary_key=True, index=True, comment='白名单ID')
    ip_address = Column(String(45), nullable=False, comment='IP地址')
    ip_range = Column(String(50), nullable=True, comment='IP范围(CIDR)')
    description = Column(Text, nullable=True, comment='描述')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='关联用户ID')
    is_active = Column(Boolean, default=True, comment='是否激活')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    user = relationship("User", foreign_keys=[user_id], backref="ip_whitelist_entries")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<IPWhitelist(ip_address={self.ip_address}, active={self.is_active})>"

class IPBlacklist(Base):
    """IP黑名单模型
    
    管理被禁止访问的IP地址
    """
    __tablename__ = "ip_blacklist"
    __table_args__ = {'comment': 'IP黑名单表，管理被禁止访问的IP地址'}

    id = Column(Integer, primary_key=True, index=True, comment='黑名单ID')
    ip_address = Column(String(45), nullable=False, comment='IP地址')
    ip_range = Column(String(50), nullable=True, comment='IP范围(CIDR)')
    reason = Column(Text, nullable=True, comment='封禁原因')
    block_type = Column(String(20), nullable=False, default='manual', comment='封禁类型')
    failed_attempts = Column(Integer, default=0, comment='失败尝试次数')
    is_active = Column(Boolean, default=True, comment='是否激活')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<IPBlacklist(ip_address={self.ip_address}, active={self.is_active})>"

class SecurityEvent(Base):
    """安全事件模型
    
    记录系统安全相关事件
    """
    __tablename__ = "security_events"
    __table_args__ = {'comment': '安全事件表，记录系统安全相关事件'}

    id = Column(Integer, primary_key=True, index=True, comment='事件ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='用户ID')
    event_type = Column(String(50), nullable=False, comment='事件类型')
    severity = Column(String(20), nullable=False, default='info', comment='严重程度')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    user_agent = Column(Text, nullable=True, comment='用户代理')
    session_id = Column(String(255), nullable=True, comment='会话ID')
    details = Column(JSON, nullable=True, comment='事件详情')
    risk_score = Column(Integer, default=0, comment='风险评分')
    is_resolved = Column(Boolean, default=False, comment='是否已处理')
    resolved_at = Column(DateTime, nullable=True, comment='处理时间')
    resolved_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='处理人')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='创建时间')
    
    # 关系定义
    user = relationship("User", foreign_keys=[user_id], backref="security_events")
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f"<SecurityEvent(type={self.event_type}, severity={self.severity})>"

class PasswordHistory(Base):
    """密码历史模型
    
    记录用户密码变更历史，防止重复使用
    """
    __tablename__ = "password_history"
    __table_args__ = {'comment': '密码历史表，记录用户密码变更历史'}

    id = Column(Integer, primary_key=True, index=True, comment='历史ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='创建时间')
    
    # 关系定义
    user = relationship("User", backref="password_history")
    
    def __repr__(self):
        return f"<PasswordHistory(user_id={self.user_id}, created_at={self.created_at})>"

class DeviceFingerprint(Base):
    """设备指纹模型
    
    记录和识别用户设备
    """
    __tablename__ = "device_fingerprints"
    __table_args__ = {'comment': '设备指纹表，记录和识别用户设备'}

    id = Column(Integer, primary_key=True, index=True, comment='指纹ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    fingerprint_hash = Column(String(255), nullable=False, unique=True, comment='指纹哈希')
    device_info = Column(JSON, nullable=True, comment='设备信息')
    browser_info = Column(JSON, nullable=True, comment='浏览器信息')
    screen_resolution = Column(String(20), nullable=True, comment='屏幕分辨率')
    timezone = Column(String(50), nullable=True, comment='时区')
    language = Column(String(10), nullable=True, comment='语言')
    is_trusted = Column(Boolean, default=False, comment='是否受信任')
    last_seen = Column(DateTime, default=datetime.now, comment='最后见到时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系定义
    user = relationship("User", backref="device_fingerprints")
    
    def __repr__(self):
        return f"<DeviceFingerprint(user_id={self.user_id}, trusted={self.is_trusted})>"

class SecurityPolicy(Base):
    """安全策略模型
    
    定义系统安全策略和规则
    """
    __tablename__ = "security_policies"
    __table_args__ = {'comment': '安全策略表，定义系统安全策略和规则'}

    id = Column(Integer, primary_key=True, index=True, comment='策略ID')
    name = Column(String(100), nullable=False, unique=True, comment='策略名称')
    description = Column(Text, nullable=True, comment='策略描述')
    policy_type = Column(String(50), nullable=False, comment='策略类型')
    rules = Column(JSON, nullable=False, comment='策略规则')
    is_active = Column(Boolean, default=True, comment='是否激活')
    priority = Column(Integer, default=0, comment='优先级')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<SecurityPolicy(name={self.name}, type={self.policy_type})>"
