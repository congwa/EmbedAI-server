from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from enum import Enum

class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertLevel(str, Enum):
    """警告级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ServiceHealth(Base):
    """服务健康状态模型
    
    用于存储各个服务组件的健康状态
    """
    __tablename__ = "service_health"
    __table_args__ = {'comment': '服务健康状态表，存储各服务组件的健康检查结果'}

    id = Column(Integer, primary_key=True, index=True, comment='健康检查ID')
    service_name = Column(String(100), nullable=False, index=True, comment='服务名称')
    service_type = Column(String(50), nullable=False, comment='服务类型')
    status = Column(String(20), nullable=False, comment='健康状态')
    response_time = Column(Float, nullable=True, comment='响应时间(毫秒)')
    error_message = Column(Text, nullable=True, comment='错误信息')
    details = Column(JSON, nullable=True, comment='详细信息')
    timestamp = Column(DateTime, default=datetime.now, index=True, comment='检查时间')
    
    def __repr__(self):
        return f"<ServiceHealth(service={self.service_name}, status={self.status}, time={self.timestamp})>"

class SystemAlert(Base):
    """系统警告模型
    
    用于存储系统警告和通知
    """
    __tablename__ = "system_alerts"
    __table_args__ = {'comment': '系统警告表，存储系统警告和通知信息'}

    id = Column(Integer, primary_key=True, index=True, comment='警告ID')
    alert_type = Column(String(50), nullable=False, index=True, comment='警告类型')
    level = Column(String(20), nullable=False, comment='警告级别')
    title = Column(String(200), nullable=False, comment='警告标题')
    message = Column(Text, nullable=False, comment='警告消息')
    source = Column(String(100), nullable=True, comment='警告来源')
    alert_metadata = Column(JSON, nullable=True, comment='警告元数据')
    is_resolved = Column(Boolean, default=False, comment='是否已解决')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')
    resolved_by = Column(String(100), nullable=True, comment='解决人')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<SystemAlert(type={self.alert_type}, level={self.level}, resolved={self.is_resolved})>"

class PerformanceThreshold(Base):
    """性能阈值模型
    
    用于定义各种性能指标的阈值
    """
    __tablename__ = "performance_thresholds"
    __table_args__ = {'comment': '性能阈值表，定义各种性能指标的警告阈值'}

    id = Column(Integer, primary_key=True, index=True, comment='阈值ID')
    metric_name = Column(String(100), nullable=False, unique=True, comment='指标名称')
    metric_type = Column(String(50), nullable=False, comment='指标类型')
    warning_threshold = Column(Float, nullable=True, comment='警告阈值')
    critical_threshold = Column(Float, nullable=True, comment='严重阈值')
    comparison_operator = Column(String(10), nullable=False, default='gt', comment='比较操作符')
    unit = Column(String(20), nullable=True, comment='单位')
    description = Column(Text, nullable=True, comment='描述')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<PerformanceThreshold(metric={self.metric_name}, warning={self.warning_threshold}, critical={self.critical_threshold})>"

class HealthCheckConfig(Base):
    """健康检查配置模型
    
    用于配置各种健康检查的参数
    """
    __tablename__ = "health_check_configs"
    __table_args__ = {'comment': '健康检查配置表，存储健康检查的配置参数'}

    id = Column(Integer, primary_key=True, index=True, comment='配置ID')
    service_name = Column(String(100), nullable=False, unique=True, comment='服务名称')
    service_type = Column(String(50), nullable=False, comment='服务类型')
    check_interval = Column(Integer, nullable=False, default=60, comment='检查间隔(秒)')
    timeout = Column(Integer, nullable=False, default=30, comment='超时时间(秒)')
    retry_count = Column(Integer, nullable=False, default=3, comment='重试次数')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    check_url = Column(String(500), nullable=True, comment='检查URL')
    check_command = Column(String(500), nullable=True, comment='检查命令')
    expected_response = Column(String(200), nullable=True, comment='期望响应')
    config_data = Column(JSON, nullable=True, comment='额外配置数据')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<HealthCheckConfig(service={self.service_name}, interval={self.check_interval}, enabled={self.is_enabled})>"

class UptimeRecord(Base):
    """运行时间记录模型
    
    用于记录系统和服务的运行时间统计
    """
    __tablename__ = "uptime_records"
    __table_args__ = {'comment': '运行时间记录表，存储系统和服务的运行时间统计'}

    id = Column(Integer, primary_key=True, index=True, comment='记录ID')
    service_name = Column(String(100), nullable=False, index=True, comment='服务名称')
    date = Column(DateTime, nullable=False, index=True, comment='日期')
    total_checks = Column(Integer, nullable=False, default=0, comment='总检查次数')
    successful_checks = Column(Integer, nullable=False, default=0, comment='成功检查次数')
    failed_checks = Column(Integer, nullable=False, default=0, comment='失败检查次数')
    uptime_percentage = Column(Float, nullable=False, default=0.0, comment='运行时间百分比')
    avg_response_time = Column(Float, nullable=True, comment='平均响应时间(毫秒)')
    max_response_time = Column(Float, nullable=True, comment='最大响应时间(毫秒)')
    min_response_time = Column(Float, nullable=True, comment='最小响应时间(毫秒)')
    downtime_duration = Column(Integer, nullable=False, default=0, comment='停机时长(秒)')
    
    def __repr__(self):
        return f"<UptimeRecord(service={self.service_name}, date={self.date}, uptime={self.uptime_percentage}%)>"
