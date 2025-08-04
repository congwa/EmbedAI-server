from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from .base import CustomBaseModel

class ContentStatus(str, Enum):
    """内容状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ModerationAction(str, Enum):
    """审核操作枚举"""
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    REMOVE = "remove"
    EDIT = "edit"

class BulkOperationType(str, Enum):
    """批量操作类型枚举"""
    DELETE = "delete"
    ARCHIVE = "archive"
    PUBLISH = "publish"
    APPROVE = "approve"
    REJECT = "reject"
    TAG = "tag"
    CATEGORY = "category"
    EXPORT = "export"

class ContentModerationRuleCreate(CustomBaseModel):
    """内容审核规则创建请求模型"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    rule_type: str = Field(..., description="规则类型")
    conditions: Dict[str, Any] = Field(..., description="规则条件")
    actions: Dict[str, Any] = Field(..., description="执行动作")
    priority: int = Field(0, description="优先级")
    auto_apply: bool = Field(False, description="是否自动应用")

class ContentModerationRuleUpdate(CustomBaseModel):
    """内容审核规则更新请求模型"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    conditions: Optional[Dict[str, Any]] = Field(None, description="规则条件")
    actions: Optional[Dict[str, Any]] = Field(None, description="执行动作")
    priority: Optional[int] = Field(None, description="优先级")
    is_active: Optional[bool] = Field(None, description="是否激活")
    auto_apply: Optional[bool] = Field(None, description="是否自动应用")

class ContentModerationRuleResponse(CustomBaseModel):
    """内容审核规则响应模型"""
    id: int = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    rule_type: str = Field(..., description="规则类型")
    conditions: Dict[str, Any] = Field(..., description="规则条件")
    actions: Dict[str, Any] = Field(..., description="执行动作")
    priority: int = Field(..., description="优先级")
    is_active: bool = Field(..., description="是否激活")
    auto_apply: bool = Field(..., description="是否自动应用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人")

class ContentModerationRequest(CustomBaseModel):
    """内容审核请求模型"""
    content_type: str = Field(..., description="内容类型")
    content_id: int = Field(..., description="内容ID")
    action: ModerationAction = Field(..., description="审核动作")
    reason: Optional[str] = Field(None, description="审核原因")
    details: Optional[Dict[str, Any]] = Field(None, description="审核详情")

class ContentModerationLogResponse(CustomBaseModel):
    """内容审核日志响应模型"""
    id: int = Field(..., description="日志ID")
    content_type: str = Field(..., description="内容类型")
    content_id: int = Field(..., description="内容ID")
    rule_id: Optional[int] = Field(None, description="规则ID")
    moderator_id: Optional[int] = Field(None, description="审核员ID")
    action: str = Field(..., description="审核动作")
    reason: Optional[str] = Field(None, description="审核原因")
    details: Optional[Dict[str, Any]] = Field(None, description="审核详情")
    confidence_score: Optional[float] = Field(None, description="置信度分数")
    is_automated: bool = Field(..., description="是否自动审核")
    previous_status: Optional[str] = Field(None, description="之前状态")
    new_status: Optional[str] = Field(None, description="新状态")
    created_at: datetime = Field(..., description="创建时间")

class BulkOperationCreate(CustomBaseModel):
    """批量操作创建请求模型"""
    name: str = Field(..., description="操作名称")
    operation_type: BulkOperationType = Field(..., description="操作类型")
    target_type: str = Field(..., description="目标类型")
    target_ids: List[int] = Field(..., description="目标ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")

class BulkOperationResponse(CustomBaseModel):
    """批量操作响应模型"""
    id: int = Field(..., description="操作ID")
    name: str = Field(..., description="操作名称")
    operation_type: str = Field(..., description="操作类型")
    target_type: str = Field(..., description="目标类型")
    target_ids: List[int] = Field(..., description="目标ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")
    status: str = Field(..., description="操作状态")
    progress: int = Field(..., description="进度百分比")
    total_items: int = Field(..., description="总项目数")
    processed_items: int = Field(..., description="已处理项目数")
    success_items: int = Field(..., description="成功项目数")
    failed_items: int = Field(..., description="失败项目数")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    result_data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class ContentTagCreate(CustomBaseModel):
    """内容标签创建请求模型"""
    name: str = Field(..., description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色")
    category: Optional[str] = Field(None, description="标签分类")

class ContentTagUpdate(CustomBaseModel):
    """内容标签更新请求模型"""
    name: Optional[str] = Field(None, description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色")
    category: Optional[str] = Field(None, description="标签分类")
    is_active: Optional[bool] = Field(None, description="是否激活")

class ContentTagResponse(CustomBaseModel):
    """内容标签响应模型"""
    id: int = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色")
    category: Optional[str] = Field(None, description="标签分类")
    usage_count: int = Field(..., description="使用次数")
    is_system: bool = Field(..., description="是否系统标签")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人")

class ContentCategoryCreate(CustomBaseModel):
    """内容分类创建请求模型"""
    name: str = Field(..., description="分类名称")
    slug: str = Field(..., description="分类标识")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    icon: Optional[str] = Field(None, description="分类图标")
    color: Optional[str] = Field(None, description="分类颜色")
    sort_order: int = Field(0, description="排序顺序")

class ContentCategoryUpdate(CustomBaseModel):
    """内容分类更新请求模型"""
    name: Optional[str] = Field(None, description="分类名称")
    slug: Optional[str] = Field(None, description="分类标识")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    icon: Optional[str] = Field(None, description="分类图标")
    color: Optional[str] = Field(None, description="分类颜色")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")

class ContentCategoryResponse(CustomBaseModel):
    """内容分类响应模型"""
    id: int = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    slug: str = Field(..., description="分类标识")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    level: int = Field(..., description="分类层级")
    sort_order: int = Field(..., description="排序顺序")
    icon: Optional[str] = Field(None, description="分类图标")
    color: Optional[str] = Field(None, description="分类颜色")
    is_active: bool = Field(..., description="是否激活")
    content_count: int = Field(..., description="内容数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人")

class SearchRequest(CustomBaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    content_types: Optional[List[str]] = Field(None, description="内容类型过滤")
    categories: Optional[List[int]] = Field(None, description="分类过滤")
    tags: Optional[List[int]] = Field(None, description="标签过滤")
    status: Optional[List[ContentStatus]] = Field(None, description="状态过滤")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    sort_by: str = Field("relevance", description="排序方式")
    sort_order: str = Field("desc", description="排序顺序")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

class SearchResult(CustomBaseModel):
    """搜索结果项模型"""
    content_type: str = Field(..., description="内容类型")
    content_id: int = Field(..., description="内容ID")
    title: str = Field(..., description="标题")
    snippet: str = Field(..., description="摘要")
    score: float = Field(..., description="相关性分数")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    url: Optional[str] = Field(None, description="链接")

class SearchResponse(CustomBaseModel):
    """搜索响应模型"""
    query: str = Field(..., description="搜索查询")
    total_count: int = Field(..., description="总结果数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    results: List[SearchResult] = Field(..., description="搜索结果")
    facets: Optional[Dict[str, Any]] = Field(None, description="分面统计")
    suggestions: Optional[List[str]] = Field(None, description="搜索建议")
    search_time: float = Field(..., description="搜索耗时")

class DataExportRequest(CustomBaseModel):
    """数据导出请求模型"""
    name: str = Field(..., description="任务名称")
    export_type: str = Field(..., description="导出类型")
    data_type: str = Field(..., description="数据类型")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    format: str = Field("csv", description="导出格式")
    include_headers: bool = Field(True, description="是否包含表头")
    date_format: str = Field("ISO", description="日期格式")

class DataExportResponse(CustomBaseModel):
    """数据导出响应模型"""
    id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    export_type: str = Field(..., description="导出类型")
    data_type: str = Field(..., description="数据类型")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    format: str = Field(..., description="导出格式")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    total_records: int = Field(..., description="总记录数")
    exported_records: int = Field(..., description="已导出记录数")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    download_url: Optional[str] = Field(None, description="下载链接")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人")

class ContentStatisticsResponse(CustomBaseModel):
    """内容统计响应模型"""
    date: datetime = Field(..., description="统计日期")
    content_type: str = Field(..., description="内容类型")
    total_count: int = Field(..., description="总数量")
    published_count: int = Field(..., description="已发布数量")
    draft_count: int = Field(..., description="草稿数量")
    pending_count: int = Field(..., description="待审核数量")
    approved_count: int = Field(..., description="已批准数量")
    rejected_count: int = Field(..., description="已拒绝数量")
    archived_count: int = Field(..., description="已归档数量")
    deleted_count: int = Field(..., description="已删除数量")
    views_count: int = Field(..., description="浏览次数")
    downloads_count: int = Field(..., description="下载次数")
    shares_count: int = Field(..., description="分享次数")

class ContentDashboardResponse(CustomBaseModel):
    """内容管理仪表板响应模型"""
    total_content: int = Field(..., description="总内容数")
    published_content: int = Field(..., description="已发布内容数")
    pending_moderation: int = Field(..., description="待审核内容数")
    total_categories: int = Field(..., description="总分类数")
    total_tags: int = Field(..., description="总标签数")
    active_bulk_operations: int = Field(..., description="活跃批量操作数")
    recent_moderation_logs: List[ContentModerationLogResponse] = Field(..., description="最近审核日志")
    content_by_status: Dict[str, int] = Field(..., description="按状态统计内容")
    content_by_type: Dict[str, int] = Field(..., description="按类型统计内容")
    top_categories: List[Dict[str, Any]] = Field(..., description="热门分类")
    top_tags: List[Dict[str, Any]] = Field(..., description="热门标签")

class AdvancedSearchFilters(CustomBaseModel):
    """高级搜索过滤器模型"""
    content_types: Optional[List[str]] = Field(None, description="内容类型")
    categories: Optional[List[int]] = Field(None, description="分类ID")
    tags: Optional[List[int]] = Field(None, description="标签ID")
    authors: Optional[List[int]] = Field(None, description="作者ID")
    status: Optional[List[ContentStatus]] = Field(None, description="内容状态")
    created_date_from: Optional[datetime] = Field(None, description="创建开始日期")
    created_date_to: Optional[datetime] = Field(None, description="创建结束日期")
    updated_date_from: Optional[datetime] = Field(None, description="更新开始日期")
    updated_date_to: Optional[datetime] = Field(None, description="更新结束日期")
    has_attachments: Optional[bool] = Field(None, description="是否有附件")
    min_views: Optional[int] = Field(None, description="最小浏览数")
    max_views: Optional[int] = Field(None, description="最大浏览数")
    language: Optional[str] = Field(None, description="语言")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")

class BatchTagOperation(CustomBaseModel):
    """批量标签操作模型"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    tag_ids: List[int] = Field(..., description="标签ID列表")
    operation: str = Field(..., description="操作类型")  # add, remove, replace

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['add', 'remove', 'replace']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_operations)}')
        return v
