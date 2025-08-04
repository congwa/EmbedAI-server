from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    comment='角色权限关联表'
)

# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    comment='用户角色关联表'
)

# 用户组成员关联表
user_group_members = Table(
    'user_group_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('user_groups.id', ondelete='CASCADE'), primary_key=True),
    comment='用户组成员关联表'
)

# 用户组角色关联表
group_roles = Table(
    'group_roles',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('user_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    comment='用户组角色关联表'
)

class Permission(Base):
    """权限模型
    
    定义系统中的各种权限
    """
    __tablename__ = "permissions"
    __table_args__ = {'comment': '权限表，定义系统中的各种权限'}

    id = Column(Integer, primary_key=True, index=True, comment='权限ID')
    name = Column(String(100), nullable=False, unique=True, comment='权限名称')
    code = Column(String(100), nullable=False, unique=True, comment='权限代码')
    description = Column(Text, nullable=True, comment='权限描述')
    resource = Column(String(100), nullable=False, comment='资源类型')
    action = Column(String(50), nullable=False, comment='操作类型')
    is_system = Column(Boolean, default=False, comment='是否为系统权限')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(name={self.name}, code={self.code})>"

class Role(Base):
    """角色模型
    
    定义用户角色和权限组合
    """
    __tablename__ = "roles"
    __table_args__ = {'comment': '角色表，定义用户角色和权限组合'}

    id = Column(Integer, primary_key=True, index=True, comment='角色ID')
    name = Column(String(100), nullable=False, unique=True, comment='角色名称')
    code = Column(String(100), nullable=False, unique=True, comment='角色代码')
    description = Column(Text, nullable=True, comment='角色描述')
    is_system = Column(Boolean, default=False, comment='是否为系统角色')
    is_active = Column(Boolean, default=True, comment='是否激活')
    priority = Column(Integer, default=0, comment='角色优先级')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, backref="roles")
    groups = relationship("UserGroup", secondary=group_roles, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(name={self.name}, code={self.code})>"

class UserGroup(Base):
    """用户组模型
    
    用于组织和管理用户
    """
    __tablename__ = "user_groups"
    __table_args__ = {'comment': '用户组表，用于组织和管理用户'}

    id = Column(Integer, primary_key=True, index=True, comment='用户组ID')
    name = Column(String(100), nullable=False, unique=True, comment='用户组名称')
    code = Column(String(100), nullable=False, unique=True, comment='用户组代码')
    description = Column(Text, nullable=True, comment='用户组描述')
    parent_id = Column(Integer, ForeignKey('user_groups.id', ondelete='SET NULL'), nullable=True, comment='父用户组ID')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    parent = relationship("UserGroup", remote_side=[id], backref="children")
    members = relationship("User", secondary=user_group_members, backref="groups")
    roles = relationship("Role", secondary=group_roles, back_populates="groups")
    
    def __repr__(self):
        return f"<UserGroup(name={self.name}, code={self.code})>"

class UserSession(Base):
    """用户会话模型
    
    跟踪用户登录会话
    """
    __tablename__ = "user_sessions"
    __table_args__ = {'comment': '用户会话表，跟踪用户登录会话'}

    id = Column(Integer, primary_key=True, index=True, comment='会话ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    session_token = Column(String(255), nullable=False, unique=True, index=True, comment='会话令牌')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    user_agent = Column(Text, nullable=True, comment='用户代理')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    last_activity = Column(DateTime, default=datetime.now, comment='最后活动时间')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系定义
    user = relationship("User", backref="sessions")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"

class UserLoginLog(Base):
    """用户登录日志模型
    
    记录用户登录历史
    """
    __tablename__ = "user_login_logs"
    __table_args__ = {'comment': '用户登录日志表，记录用户登录历史'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='用户ID')
    email = Column(String(255), nullable=False, comment='登录邮箱')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    user_agent = Column(Text, nullable=True, comment='用户代理')
    login_method = Column(String(50), nullable=False, default='password', comment='登录方式')
    is_successful = Column(Boolean, nullable=False, comment='是否成功')
    failure_reason = Column(String(200), nullable=True, comment='失败原因')
    session_id = Column(String(255), nullable=True, comment='会话ID')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='登录时间')
    
    # 关系定义
    user = relationship("User", backref="login_logs")
    
    def __repr__(self):
        return f"<UserLoginLog(email={self.email}, successful={self.is_successful})>"

class UserSecuritySettings(Base):
    """用户安全设置模型
    
    存储用户的安全相关设置
    """
    __tablename__ = "user_security_settings"
    __table_args__ = {'comment': '用户安全设置表，存储用户的安全相关设置'}

    id = Column(Integer, primary_key=True, index=True, comment='设置ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, comment='用户ID')
    two_factor_enabled = Column(Boolean, default=False, comment='是否启用双因子认证')
    two_factor_secret = Column(String(255), nullable=True, comment='双因子认证密钥')
    backup_codes = Column(Text, nullable=True, comment='备用验证码')
    password_changed_at = Column(DateTime, nullable=True, comment='密码最后修改时间')
    failed_login_attempts = Column(Integer, default=0, comment='失败登录尝试次数')
    account_locked_until = Column(DateTime, nullable=True, comment='账户锁定到期时间')
    last_password_reset = Column(DateTime, nullable=True, comment='最后密码重置时间')
    security_questions = Column(Text, nullable=True, comment='安全问题')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    user = relationship("User", backref="security_settings", uselist=False)
    
    def __repr__(self):
        return f"<UserSecuritySettings(user_id={self.user_id}, 2fa={self.two_factor_enabled})>"
