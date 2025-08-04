from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class ConfigType(enum.Enum):
    """配置类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    PASSWORD = "password"
    EMAIL = "email"
    URL = "url"
    FILE_PATH = "file_path"

class ConfigCategory(enum.Enum):
    """配置分类枚举"""
    SYSTEM = "system"
    DATABASE = "database"
    REDIS = "redis"
    EMAIL = "email"
    STORAGE = "storage"
    AI_MODEL = "ai_model"
    SECURITY = "security"
    LOGGING = "logging"
    MONITORING = "monitoring"
    INTEGRATION = "integration"

class SystemConfig(Base):
    """系统配置模型
    
    存储系统的各种配置参数
    """
    __tablename__ = "system_configs"
    __table_args__ = {'comment': '系统配置表，存储系统的各种配置参数'}

    id = Column(Integer, primary_key=True, index=True, comment='配置ID')
    key = Column(String(100), nullable=False, unique=True, index=True, comment='配置键名')
    value = Column(Text, nullable=True, comment='配置值')
    default_value = Column(Text, nullable=True, comment='默认值')
    description = Column(Text, nullable=True, comment='配置描述')
    category = Column(SQLEnum(ConfigCategory), nullable=False, comment='配置分类')
    type = Column(SQLEnum(ConfigType), nullable=False, default=ConfigType.STRING, comment='配置类型')
    is_sensitive = Column(Boolean, default=False, comment='是否为敏感信息')
    is_required = Column(Boolean, default=False, comment='是否必需')
    is_readonly = Column(Boolean, default=False, comment='是否只读')
    is_system = Column(Boolean, default=False, comment='是否为系统配置')
    validation_rule = Column(Text, nullable=True, comment='验证规则（正则表达式或JSON）')
    options = Column(JSON, nullable=True, comment='可选值列表（用于枚举类型）')
    min_value = Column(String(50), nullable=True, comment='最小值')
    max_value = Column(String(50), nullable=True, comment='最大值')
    restart_required = Column(Boolean, default=False, comment='修改后是否需要重启')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    change_logs = relationship("ConfigChangeLog", back_populates="config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SystemConfig(key={self.key}, category={self.category.value})>"

class ConfigChangeLog(Base):
    """配置变更日志模型
    
    记录配置的变更历史
    """
    __tablename__ = "config_change_logs"
    __table_args__ = {'comment': '配置变更日志表，记录配置的变更历史'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    config_id = Column(Integer, ForeignKey('system_configs.id', ondelete='CASCADE'), nullable=False, comment='配置ID')
    config_key = Column(String(100), nullable=False, comment='配置键名')
    old_value = Column(Text, nullable=True, comment='旧值')
    new_value = Column(Text, nullable=True, comment='新值')
    change_type = Column(String(20), nullable=False, comment='变更类型')
    user_id = Column(Integer, nullable=True, comment='操作用户ID')
    user_email = Column(String(255), nullable=True, comment='操作用户邮箱')
    ip_address = Column(String(45), nullable=True, comment='操作IP地址')
    user_agent = Column(Text, nullable=True, comment='用户代理')
    reason = Column(Text, nullable=True, comment='变更原因')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='变更时间')
    
    # 关系定义
    config = relationship("SystemConfig", back_populates="change_logs")
    
    def __repr__(self):
        return f"<ConfigChangeLog(config_key={self.config_key}, change_type={self.change_type})>"

class ConfigTemplate(Base):
    """配置模板模型
    
    预定义的配置模板，用于快速部署
    """
    __tablename__ = "config_templates"
    __table_args__ = {'comment': '配置模板表，预定义的配置模板'}

    id = Column(Integer, primary_key=True, index=True, comment='模板ID')
    name = Column(String(100), nullable=False, unique=True, comment='模板名称')
    description = Column(Text, nullable=True, comment='模板描述')
    category = Column(SQLEnum(ConfigCategory), nullable=False, comment='模板分类')
    template_data = Column(JSON, nullable=False, comment='模板配置数据')
    is_system = Column(Boolean, default=False, comment='是否为系统模板')
    is_active = Column(Boolean, default=True, comment='是否激活')
    version = Column(String(20), nullable=False, default='1.0.0', comment='模板版本')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, nullable=True, comment='创建人ID')
    
    def __repr__(self):
        return f"<ConfigTemplate(name={self.name}, category={self.category.value})>"

class ConfigBackup(Base):
    """配置备份模型
    
    系统配置的备份记录
    """
    __tablename__ = "config_backups"
    __table_args__ = {'comment': '配置备份表，系统配置的备份记录'}

    id = Column(Integer, primary_key=True, index=True, comment='备份ID')
    name = Column(String(100), nullable=False, comment='备份名称')
    description = Column(Text, nullable=True, comment='备份描述')
    backup_data = Column(JSON, nullable=False, comment='备份的配置数据')
    config_count = Column(Integer, nullable=False, default=0, comment='配置项数量')
    backup_type = Column(String(20), nullable=False, default='manual', comment='备份类型')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='备份时间')
    created_by = Column(Integer, nullable=True, comment='备份人ID')
    created_by_email = Column(String(255), nullable=True, comment='备份人邮箱')
    
    def __repr__(self):
        return f"<ConfigBackup(name={self.name}, config_count={self.config_count})>"

class EnvironmentVariable(Base):
    """环境变量模型
    
    管理系统环境变量
    """
    __tablename__ = "environment_variables"
    __table_args__ = {'comment': '环境变量表，管理系统环境变量'}

    id = Column(Integer, primary_key=True, index=True, comment='变量ID')
    name = Column(String(100), nullable=False, unique=True, index=True, comment='变量名')
    value = Column(Text, nullable=True, comment='变量值')
    description = Column(Text, nullable=True, comment='变量描述')
    category = Column(SQLEnum(ConfigCategory), nullable=False, comment='变量分类')
    is_sensitive = Column(Boolean, default=False, comment='是否为敏感信息')
    is_required = Column(Boolean, default=False, comment='是否必需')
    is_system = Column(Boolean, default=False, comment='是否为系统变量')
    validation_rule = Column(Text, nullable=True, comment='验证规则')
    default_value = Column(Text, nullable=True, comment='默认值')
    restart_required = Column(Boolean, default=True, comment='修改后是否需要重启')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<EnvironmentVariable(name={self.name}, category={self.category.value})>"

class ConfigValidationRule(Base):
    """配置验证规则模型
    
    定义配置项的验证规则
    """
    __tablename__ = "config_validation_rules"
    __table_args__ = {'comment': '配置验证规则表，定义配置项的验证规则'}

    id = Column(Integer, primary_key=True, index=True, comment='规则ID')
    name = Column(String(100), nullable=False, unique=True, comment='规则名称')
    description = Column(Text, nullable=True, comment='规则描述')
    rule_type = Column(String(50), nullable=False, comment='规则类型')
    rule_data = Column(JSON, nullable=False, comment='规则数据')
    error_message = Column(Text, nullable=True, comment='错误消息模板')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<ConfigValidationRule(name={self.name}, rule_type={self.rule_type})>"
