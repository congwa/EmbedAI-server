from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class ContentStatus(enum.Enum):
    """内容状态枚举"""
    DRAFT = "draft"           # 草稿
    PENDING = "pending"       # 待审核
    APPROVED = "approved"     # 已批准
    REJECTED = "rejected"     # 已拒绝
    PUBLISHED = "published"   # 已发布
    ARCHIVED = "archived"     # 已归档
    DELETED = "deleted"       # 已删除

class ModerationAction(enum.Enum):
    """审核操作枚举"""
    APPROVE = "approve"       # 批准
    REJECT = "reject"         # 拒绝
    FLAG = "flag"            # 标记
    REMOVE = "remove"        # 移除
    EDIT = "edit"            # 编辑

class BulkOperationType(enum.Enum):
    """批量操作类型枚举"""
    DELETE = "delete"         # 删除
    ARCHIVE = "archive"       # 归档
    PUBLISH = "publish"       # 发布
    APPROVE = "approve"       # 批准
    REJECT = "reject"         # 拒绝
    TAG = "tag"              # 标签
    CATEGORY = "category"     # 分类
    EXPORT = "export"         # 导出

class ContentModerationRule(Base):
    """内容审核规则模型
    
    定义自动内容审核的规则和条件
    """
    __tablename__ = "content_moderation_rules"
    __table_args__ = {'comment': '内容审核规则表，定义自动审核规则'}

    id = Column(Integer, primary_key=True, index=True, comment='规则ID')
    name = Column(String(100), nullable=False, comment='规则名称')
    description = Column(Text, nullable=True, comment='规则描述')
    rule_type = Column(String(50), nullable=False, comment='规则类型')
    conditions = Column(JSON, nullable=False, comment='规则条件')
    actions = Column(JSON, nullable=False, comment='执行动作')
    priority = Column(Integer, default=0, comment='优先级')
    is_active = Column(Boolean, default=True, comment='是否激活')
    auto_apply = Column(Boolean, default=False, comment='是否自动应用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<ContentModerationRule(name={self.name}, type={self.rule_type})>"

class ContentModerationLog(Base):
    """内容审核日志模型
    
    记录内容审核的历史和操作
    """
    __tablename__ = "content_moderation_logs"
    __table_args__ = {'comment': '内容审核日志表，记录审核历史'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    content_type = Column(String(50), nullable=False, comment='内容类型')
    content_id = Column(Integer, nullable=False, comment='内容ID')
    rule_id = Column(Integer, ForeignKey('content_moderation_rules.id', ondelete='SET NULL'), nullable=True, comment='规则ID')
    moderator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='审核员ID')
    action = Column(String(20), nullable=False, comment='审核动作')
    reason = Column(Text, nullable=True, comment='审核原因')
    details = Column(JSON, nullable=True, comment='审核详情')
    confidence_score = Column(Float, nullable=True, comment='置信度分数')
    is_automated = Column(Boolean, default=False, comment='是否自动审核')
    previous_status = Column(String(20), nullable=True, comment='之前状态')
    new_status = Column(String(20), nullable=True, comment='新状态')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='创建时间')
    
    # 关系定义
    rule = relationship("ContentModerationRule", foreign_keys=[rule_id])
    moderator = relationship("User", foreign_keys=[moderator_id])
    
    def __repr__(self):
        return f"<ContentModerationLog(content_type={self.content_type}, action={self.action})>"

class BulkOperation(Base):
    """批量操作模型
    
    记录和管理批量操作任务
    """
    __tablename__ = "bulk_operations"
    __table_args__ = {'comment': '批量操作表，记录批量操作任务'}

    id = Column(Integer, primary_key=True, index=True, comment='操作ID')
    name = Column(String(100), nullable=False, comment='操作名称')
    operation_type = Column(String(50), nullable=False, comment='操作类型')
    target_type = Column(String(50), nullable=False, comment='目标类型')
    target_ids = Column(JSON, nullable=False, comment='目标ID列表')
    parameters = Column(JSON, nullable=True, comment='操作参数')
    status = Column(String(20), nullable=False, default='pending', comment='操作状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    total_items = Column(Integer, nullable=False, comment='总项目数')
    processed_items = Column(Integer, default=0, comment='已处理项目数')
    success_items = Column(Integer, default=0, comment='成功项目数')
    failed_items = Column(Integer, default=0, comment='失败项目数')
    error_details = Column(JSON, nullable=True, comment='错误详情')
    result_data = Column(JSON, nullable=True, comment='结果数据')
    started_at = Column(DateTime, nullable=True, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<BulkOperation(name={self.name}, type={self.operation_type}, status={self.status})>"

class ContentTag(Base):
    """内容标签模型
    
    管理内容标签系统
    """
    __tablename__ = "content_tags"
    __table_args__ = {'comment': '内容标签表，管理标签系统'}

    id = Column(Integer, primary_key=True, index=True, comment='标签ID')
    name = Column(String(50), nullable=False, unique=True, comment='标签名称')
    description = Column(Text, nullable=True, comment='标签描述')
    color = Column(String(7), nullable=True, comment='标签颜色')
    category = Column(String(50), nullable=True, comment='标签分类')
    usage_count = Column(Integer, default=0, comment='使用次数')
    is_system = Column(Boolean, default=False, comment='是否系统标签')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<ContentTag(name={self.name}, category={self.category})>"

class ContentCategory(Base):
    """内容分类模型
    
    管理内容分类系统
    """
    __tablename__ = "content_categories"
    __table_args__ = {'comment': '内容分类表，管理分类系统'}

    id = Column(Integer, primary_key=True, index=True, comment='分类ID')
    name = Column(String(100), nullable=False, comment='分类名称')
    slug = Column(String(100), nullable=False, unique=True, comment='分类标识')
    description = Column(Text, nullable=True, comment='分类描述')
    parent_id = Column(Integer, ForeignKey('content_categories.id', ondelete='CASCADE'), nullable=True, comment='父分类ID')
    level = Column(Integer, default=0, comment='分类层级')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    icon = Column(String(50), nullable=True, comment='分类图标')
    color = Column(String(7), nullable=True, comment='分类颜色')
    is_active = Column(Boolean, default=True, comment='是否激活')
    content_count = Column(Integer, default=0, comment='内容数量')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    parent = relationship("ContentCategory", remote_side=[id], backref="children")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<ContentCategory(name={self.name}, level={self.level})>"

class SearchIndex(Base):
    """搜索索引模型
    
    管理全文搜索索引
    """
    __tablename__ = "search_indexes"
    __table_args__ = {'comment': '搜索索引表，管理全文搜索'}

    id = Column(Integer, primary_key=True, index=True, comment='索引ID')
    content_type = Column(String(50), nullable=False, comment='内容类型')
    content_id = Column(Integer, nullable=False, comment='内容ID')
    title = Column(String(255), nullable=True, comment='标题')
    content = Column(Text, nullable=True, comment='内容')
    keywords = Column(Text, nullable=True, comment='关键词')
    meta_data = Column(JSON, nullable=True, comment='元数据')
    language = Column(String(10), nullable=True, comment='语言')
    search_vector = Column(Text, nullable=True, comment='搜索向量')
    boost_score = Column(Float, default=1.0, comment='权重分数')
    is_active = Column(Boolean, default=True, comment='是否激活')
    last_indexed = Column(DateTime, default=datetime.now, comment='最后索引时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<SearchIndex(content_type={self.content_type}, content_id={self.content_id})>"

class ContentStatistics(Base):
    """内容统计模型
    
    记录内容相关的统计数据
    """
    __tablename__ = "content_statistics"
    __table_args__ = {'comment': '内容统计表，记录统计数据'}

    id = Column(Integer, primary_key=True, index=True, comment='统计ID')
    date = Column(DateTime, nullable=False, comment='统计日期')
    content_type = Column(String(50), nullable=False, comment='内容类型')
    total_count = Column(Integer, default=0, comment='总数量')
    published_count = Column(Integer, default=0, comment='已发布数量')
    draft_count = Column(Integer, default=0, comment='草稿数量')
    pending_count = Column(Integer, default=0, comment='待审核数量')
    approved_count = Column(Integer, default=0, comment='已批准数量')
    rejected_count = Column(Integer, default=0, comment='已拒绝数量')
    archived_count = Column(Integer, default=0, comment='已归档数量')
    deleted_count = Column(Integer, default=0, comment='已删除数量')
    views_count = Column(Integer, default=0, comment='浏览次数')
    downloads_count = Column(Integer, default=0, comment='下载次数')
    shares_count = Column(Integer, default=0, comment='分享次数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f"<ContentStatistics(date={self.date}, type={self.content_type})>"

class DataExportTask(Base):
    """数据导出任务模型
    
    管理数据导出任务
    """
    __tablename__ = "data_export_tasks"
    __table_args__ = {'comment': '数据导出任务表，管理导出任务'}

    id = Column(Integer, primary_key=True, index=True, comment='任务ID')
    name = Column(String(100), nullable=False, comment='任务名称')
    export_type = Column(String(50), nullable=False, comment='导出类型')
    data_type = Column(String(50), nullable=False, comment='数据类型')
    filters = Column(JSON, nullable=True, comment='过滤条件')
    format = Column(String(20), nullable=False, default='csv', comment='导出格式')
    status = Column(String(20), nullable=False, default='pending', comment='任务状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    total_records = Column(Integer, default=0, comment='总记录数')
    exported_records = Column(Integer, default=0, comment='已导出记录数')
    file_path = Column(String(255), nullable=True, comment='文件路径')
    file_size = Column(Integer, nullable=True, comment='文件大小')
    download_url = Column(String(255), nullable=True, comment='下载链接')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')
    error_message = Column(Text, nullable=True, comment='错误信息')
    started_at = Column(DateTime, nullable=True, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建人')
    
    # 关系定义
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<DataExportTask(name={self.name}, type={self.export_type}, status={self.status})>"
