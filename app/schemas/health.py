from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .base import CustomBaseModel
from pydantic import ConfigDict

class HealthStatus(str):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertLevel(str):
    """警告级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ServiceHealthResponse(CustomBaseModel):
    """服务健康状态响应模型"""
    service_name: str = Field(..., description="服务名称")
    service_type: str = Field(..., description="服务类型")
    status: str = Field(..., description="健康状态")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")
    error_message: Optional[str] = Field(None, description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    timestamp: datetime = Field(..., description="检查时间")
    uptime_percentage: Optional[float] = Field(None, description="运行时间百分比")

class SystemHealthOverview(CustomBaseModel):
    """系统健康概览模型"""
    overall_status: str = Field(..., description="整体状态")
    healthy_services: int = Field(..., description="健康服务数量")
    warning_services: int = Field(..., description="警告服务数量")
    critical_services: int = Field(..., description="严重服务数量")
    total_services: int = Field(..., description="总服务数量")
    system_uptime: float = Field(..., description="系统运行时间(小时)")
    last_check: datetime = Field(..., description="最后检查时间")

class SystemAlertResponse(CustomBaseModel):
    """系统警告响应模型"""
    id: int = Field(..., description="警告ID")
    alert_type: str = Field(..., description="警告类型")
    level: str = Field(..., description="警告级别")
    title: str = Field(..., description="警告标题")
    message: str = Field(..., description="警告消息")
    source: Optional[str] = Field(None, description="警告来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="警告元数据")
    is_resolved: bool = Field(..., description="是否已解决")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    resolved_by: Optional[str] = Field(None, description="解决人")
    created_at: datetime = Field(..., description="创建时间")

class SystemAlertCreate(CustomBaseModel):
    """创建系统警告请求模型"""
    alert_type: str = Field(..., description="警告类型")
    level: str = Field(..., description="警告级别")
    title: str = Field(..., description="警告标题")
    message: str = Field(..., description="警告消息")
    source: Optional[str] = Field(None, description="警告来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="警告元数据")

class SystemAlertResolve(CustomBaseModel):
    """解决系统警告请求模型"""
    resolved_by: str = Field(..., description="解决人")
    resolution_note: Optional[str] = Field(None, description="解决说明")

class PerformanceThresholdResponse(CustomBaseModel):
    """性能阈值响应模型"""
    id: int = Field(..., description="阈值ID")
    metric_name: str = Field(..., description="指标名称")
    metric_type: str = Field(..., description="指标类型")
    warning_threshold: Optional[float] = Field(None, description="警告阈值")
    critical_threshold: Optional[float] = Field(None, description="严重阈值")
    comparison_operator: str = Field(..., description="比较操作符")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="描述")
    is_enabled: bool = Field(..., description="是否启用")

class PerformanceThresholdCreate(CustomBaseModel):
    """创建性能阈值请求模型"""
    metric_name: str = Field(..., description="指标名称")
    metric_type: str = Field(..., description="指标类型")
    warning_threshold: Optional[float] = Field(None, description="警告阈值")
    critical_threshold: Optional[float] = Field(None, description="严重阈值")
    comparison_operator: str = Field("gt", description="比较操作符")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="描述")
    is_enabled: bool = Field(True, description="是否启用")

class PerformanceThresholdUpdate(CustomBaseModel):
    """更新性能阈值请求模型"""
    warning_threshold: Optional[float] = Field(None, description="警告阈值")
    critical_threshold: Optional[float] = Field(None, description="严重阈值")
    comparison_operator: Optional[str] = Field(None, description="比较操作符")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="描述")
    is_enabled: Optional[bool] = Field(None, description="是否启用")

class HealthCheckConfigResponse(CustomBaseModel):
    """健康检查配置响应模型"""
    id: int = Field(..., description="配置ID")
    service_name: str = Field(..., description="服务名称")
    service_type: str = Field(..., description="服务类型")
    check_interval: int = Field(..., description="检查间隔(秒)")
    timeout: int = Field(..., description="超时时间(秒)")
    retry_count: int = Field(..., description="重试次数")
    is_enabled: bool = Field(..., description="是否启用")
    check_url: Optional[str] = Field(None, description="检查URL")
    check_command: Optional[str] = Field(None, description="检查命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    config_data: Optional[Dict[str, Any]] = Field(None, description="额外配置数据")

class HealthCheckConfigCreate(CustomBaseModel):
    """创建健康检查配置请求模型"""
    service_name: str = Field(..., description="服务名称")
    service_type: str = Field(..., description="服务类型")
    check_interval: int = Field(60, description="检查间隔(秒)")
    timeout: int = Field(30, description="超时时间(秒)")
    retry_count: int = Field(3, description="重试次数")
    is_enabled: bool = Field(True, description="是否启用")
    check_url: Optional[str] = Field(None, description="检查URL")
    check_command: Optional[str] = Field(None, description="检查命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    config_data: Optional[Dict[str, Any]] = Field(None, description="额外配置数据")

class HealthCheckConfigUpdate(CustomBaseModel):
    """更新健康检查配置请求模型"""
    check_interval: Optional[int] = Field(None, description="检查间隔(秒)")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")
    retry_count: Optional[int] = Field(None, description="重试次数")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    check_url: Optional[str] = Field(None, description="检查URL")
    check_command: Optional[str] = Field(None, description="检查命令")
    expected_response: Optional[str] = Field(None, description="期望响应")
    config_data: Optional[Dict[str, Any]] = Field(None, description="额外配置数据")

class UptimeRecordResponse(CustomBaseModel):
    """运行时间记录响应模型"""
    service_name: str = Field(..., description="服务名称")
    date: datetime = Field(..., description="日期")
    total_checks: int = Field(..., description="总检查次数")
    successful_checks: int = Field(..., description="成功检查次数")
    failed_checks: int = Field(..., description="失败检查次数")
    uptime_percentage: float = Field(..., description="运行时间百分比")
    avg_response_time: Optional[float] = Field(None, description="平均响应时间(毫秒)")
    max_response_time: Optional[float] = Field(None, description="最大响应时间(毫秒)")
    min_response_time: Optional[float] = Field(None, description="最小响应时间(毫秒)")
    downtime_duration: int = Field(..., description="停机时长(秒)")

class SystemResourceMetrics(CustomBaseModel):
    """系统资源指标模型"""
    cpu_usage: float = Field(..., description="CPU使用率(%)")
    memory_usage: float = Field(..., description="内存使用率(%)")
    memory_total: int = Field(..., description="总内存(字节)")
    memory_used: int = Field(..., description="已用内存(字节)")
    disk_usage: float = Field(..., description="磁盘使用率(%)")
    disk_total: int = Field(..., description="总磁盘空间(字节)")
    disk_used: int = Field(..., description="已用磁盘空间(字节)")
    network_bytes_sent: int = Field(..., description="网络发送字节数")
    network_bytes_recv: int = Field(..., description="网络接收字节数")
    load_average: float = Field(..., description="系统负载")
    timestamp: datetime = Field(..., description="采集时间")

class HealthDashboardData(CustomBaseModel):
    """健康监控仪表板数据模型"""
    overview: SystemHealthOverview = Field(..., description="系统健康概览")
    services: List[ServiceHealthResponse] = Field(..., description="服务健康状态列表")
    recent_alerts: List[SystemAlertResponse] = Field(..., description="最近警告列表")
    system_resources: SystemResourceMetrics = Field(..., description="系统资源指标")
    uptime_trends: List[UptimeRecordResponse] = Field(..., description="运行时间趋势")

class AlertQuery(CustomBaseModel):
    """警告查询参数模型"""
    level: Optional[str] = Field(None, description="警告级别")
    alert_type: Optional[str] = Field(None, description="警告类型")
    is_resolved: Optional[bool] = Field(None, description="是否已解决")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(50, ge=1, le=200, description="返回数量限制")
