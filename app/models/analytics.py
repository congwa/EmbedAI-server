from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from typing import Dict, Any, Optional

class SystemMetrics(Base):
    """系统指标模型
    
    用于存储系统级别的性能和使用指标
    """
    __tablename__ = "system_metrics"
    __table_args__ = {'comment': '系统指标表，存储系统性能和使用数据'}

    id = Column(Integer, primary_key=True, index=True, comment='指标ID')
    metric_type = Column(String(50), nullable=False, index=True, comment='指标类型')
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    metric_value = Column(Float, nullable=False, comment='指标值')
    metric_unit = Column(String(20), nullable=True, comment='指标单位')
    extra_metadata = Column(JSON, nullable=True, comment='额外元数据')
    timestamp = Column(DateTime, default=datetime.now, index=True, comment='记录时间')
    
    def __repr__(self):
        return f"<SystemMetrics(type={self.metric_type}, name={self.metric_name}, value={self.metric_value})>"

class UserActivityLog(Base):
    """用户活动日志模型
    
    用于跟踪用户的详细活动记录
    """
    __tablename__ = "user_activity_logs"
    __table_args__ = {'comment': '用户活动日志表，记录用户行为和会话信息'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='用户ID')
    session_id = Column(String(64), nullable=True, index=True, comment='会话ID')
    activity_type = Column(String(50), nullable=False, index=True, comment='活动类型')
    activity_details = Column(JSON, nullable=True, comment='活动详情')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    user_agent = Column(String(500), nullable=True, comment='用户代理')
    timestamp = Column(DateTime, default=datetime.now, index=True, comment='活动时间')
    duration = Column(Integer, nullable=True, comment='持续时间(秒)')
    
    # 关系定义
    user = relationship("User", backref="activity_logs")
    
    def __repr__(self):
        return f"<UserActivityLog(user_id={self.user_id}, type={self.activity_type}, time={self.timestamp})>"

class KnowledgeBaseMetrics(Base):
    """知识库指标模型
    
    用于存储知识库的使用统计和性能指标
    """
    __tablename__ = "knowledge_base_metrics"
    __table_args__ = {'comment': '知识库指标表，存储知识库使用统计'}

    id = Column(Integer, primary_key=True, index=True, comment='指标ID')
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment='知识库ID')
    metric_date = Column(DateTime, nullable=False, index=True, comment='指标日期')
    query_count = Column(Integer, default=0, comment='查询次数')
    success_count = Column(Integer, default=0, comment='成功次数')
    error_count = Column(Integer, default=0, comment='错误次数')
    avg_response_time = Column(Float, default=0.0, comment='平均响应时间(秒)')
    total_tokens_used = Column(Integer, default=0, comment='总Token使用量')
    total_cost = Column(Float, default=0.0, comment='总费用')
    unique_users = Column(Integer, default=0, comment='独立用户数')
    
    # 关系定义
    knowledge_base = relationship("KnowledgeBase", backref="metrics")
    
    def __repr__(self):
        return f"<KnowledgeBaseMetrics(kb_id={self.knowledge_base_id}, date={self.metric_date}, queries={self.query_count})>"

class APIMetrics(Base):
    """API指标模型
    
    用于存储API调用的性能和使用统计
    """
    __tablename__ = "api_metrics"
    __table_args__ = {'comment': 'API指标表，存储API调用统计'}

    id = Column(Integer, primary_key=True, index=True, comment='指标ID')
    endpoint = Column(String(200), nullable=False, index=True, comment='API端点')
    method = Column(String(10), nullable=False, comment='HTTP方法')
    status_code = Column(Integer, nullable=False, comment='状态码')
    response_time = Column(Float, nullable=False, comment='响应时间(秒)')
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='用户ID')
    ip_address = Column(String(45), nullable=True, comment='IP地址')
    timestamp = Column(DateTime, default=datetime.now, index=True, comment='调用时间')
    
    # 关系定义
    user = relationship("User", backref="api_metrics")
    
    def __repr__(self):
        return f"<APIMetrics(endpoint={self.endpoint}, status={self.status_code}, time={self.response_time})>"
