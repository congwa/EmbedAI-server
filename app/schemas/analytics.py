from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from pydantic import BaseModel, Field
from .base import CustomBaseModel
from pydantic import ConfigDict

class SystemOverviewResponse(CustomBaseModel):
    """系统概览响应模型"""
    active_users: int = Field(..., description="活跃用户数")
    total_users: int = Field(..., description="总用户数")
    knowledge_bases: int = Field(..., description="知识库数量")
    total_documents: int = Field(..., description="文档总数")
    total_queries: int = Field(..., description="查询总数")
    system_uptime: float = Field(..., description="系统运行时间(小时)")
    avg_response_time: float = Field(..., description="平均响应时间(秒)")
    success_rate: float = Field(..., description="成功率(%)")
    total_cost: float = Field(..., description="总费用")

class UserActivityStats(CustomBaseModel):
    """用户活动统计模型"""
    user_id: int
    email: str
    login_count: int = Field(..., description="登录次数")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    session_duration_avg: float = Field(..., description="平均会话时长(分钟)")
    total_queries: int = Field(..., description="总查询数")
    active_days: int = Field(..., description="活跃天数")

class KnowledgeBaseStats(CustomBaseModel):
    """知识库统计模型"""
    kb_id: int
    kb_name: str
    query_count: int = Field(..., description="查询次数")
    success_rate: float = Field(..., description="成功率(%)")
    avg_response_time: float = Field(..., description="平均响应时间(秒)")
    total_cost: float = Field(..., description="总费用")
    unique_users: int = Field(..., description="独立用户数")
    documents_count: int = Field(..., description="文档数量")

class PerformanceMetrics(CustomBaseModel):
    """性能指标模型"""
    timestamp: datetime
    cpu_usage: float = Field(..., description="CPU使用率(%)")
    memory_usage: float = Field(..., description="内存使用率(%)")
    disk_usage: float = Field(..., description="磁盘使用率(%)")
    api_response_time: float = Field(..., description="API响应时间(秒)")
    error_rate: float = Field(..., description="错误率(%)")
    throughput: float = Field(..., description="吞吐量(请求/秒)")

class CostAnalysis(CustomBaseModel):
    """费用分析模型"""
    user_id: Optional[int] = None
    kb_id: Optional[int] = None
    period_start: datetime
    period_end: datetime
    total_cost: float = Field(..., description="总费用")
    token_cost: float = Field(..., description="Token费用")
    model_breakdown: Dict[str, float] = Field(..., description="模型费用分解")
    daily_costs: List[Dict[str, Any]] = Field(..., description="每日费用")

class TimeSeriesData(CustomBaseModel):
    """时间序列数据模型"""
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsQuery(CustomBaseModel):
    """分析查询参数模型"""
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    user_id: Optional[int] = Field(None, description="用户ID")
    kb_id: Optional[int] = Field(None, description="知识库ID")
    metric_type: Optional[str] = Field(None, description="指标类型")
    granularity: str = Field("day", description="时间粒度: hour, day, week, month")
    limit: int = Field(100, ge=1, le=1000, description="返回数量限制")

class ExportRequest(CustomBaseModel):
    """导出请求模型"""
    report_type: str = Field(..., description="报告类型")
    format: str = Field("csv", description="导出格式: csv, json, pdf")
    filters: Optional[AnalyticsQuery] = Field(None, description="过滤条件")
    include_charts: bool = Field(False, description="是否包含图表(PDF)")

class DashboardData(CustomBaseModel):
    """仪表板数据模型"""
    overview: SystemOverviewResponse
    recent_activities: List[UserActivityStats]
    top_knowledge_bases: List[KnowledgeBaseStats]
    performance_trends: List[TimeSeriesData]
    cost_summary: CostAnalysis
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="系统警告")

class AlertConfig(CustomBaseModel):
    """警告配置模型"""
    metric_name: str = Field(..., description="指标名称")
    threshold: float = Field(..., description="阈值")
    operator: str = Field(..., description="操作符: gt, lt, eq")
    enabled: bool = Field(True, description="是否启用")
    notification_channels: List[str] = Field(default_factory=list, description="通知渠道")

class ReportTemplate(CustomBaseModel):
    """报告模板模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    metrics: List[str] = Field(..., description="包含的指标")
    filters: Optional[AnalyticsQuery] = Field(None, description="默认过滤条件")
    schedule: Optional[str] = Field(None, description="定时生成: daily, weekly, monthly")
