from typing import Optional, Dict, Any, List
from pydantic import Field, BaseModel, ConfigDict, validator
from .base import CustomBaseModel
from datetime import datetime
import re


class PromptVariableDefinition(BaseModel):
    """提示词变量定义"""
    name: str = Field(..., description="变量名称")
    type: str = Field(..., description="变量类型：string, integer, float, boolean, array, object")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")
    description: Optional[str] = Field(default=None, description="变量描述")
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['string', 'integer', 'float', 'boolean', 'array', 'object']
        if v not in valid_types:
            raise ValueError(f'变量类型必须是以下之一: {", ".join(valid_types)}')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('变量名只能包含字母、数字和下划线，且不能以数字开头')
        return v


class PromptTemplateCreate(CustomBaseModel):
    """创建提示词模板请求"""
    name: str = Field(..., min_length=1, max_length=255, description="模板名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    category_id: Optional[int] = Field(default=None, description="分类ID")
    content: str = Field(..., min_length=1, description="提示词内容，支持{{variable_name}}格式的变量")
    variables: Optional[List[PromptVariableDefinition]] = Field(default=[], description="变量定义列表")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    is_system: bool = Field(default=False, description="是否为系统模板")
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('提示词内容不能为空')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 20:
            raise ValueError('标签数量不能超过20个')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "知识库问答模板",
                "description": "用于知识库问答的标准提示词模板",
                "category_id": 1,
                "content": "你是一个专业的AI助手，基于以下上下文回答用户问题。\n\n上下文信息：\n{{context}}\n\n用户问题：\n{{query}}\n\n请基于上下文信息给出准确、有用的回答。",
                "variables": [
                    {
                        "name": "context",
                        "type": "string",
                        "required": True,
                        "description": "检索到的上下文信息"
                    },
                    {
                        "name": "query",
                        "type": "string", 
                        "required": True,
                        "description": "用户查询内容"
                    }
                ],
                "tags": ["问答", "知识库", "RAG"],
                "is_system": False
            }
        }
    )


class PromptTemplateUpdate(CustomBaseModel):
    """更新提示词模板请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="模板名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    category_id: Optional[int] = Field(default=None, description="分类ID")
    content: Optional[str] = Field(default=None, min_length=1, description="提示词内容")
    variables: Optional[List[PromptVariableDefinition]] = Field(default=None, description="变量定义列表")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    is_active: Optional[bool] = Field(default=None, description="是否激活")
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None and not v.strip():
            raise ValueError('提示词内容不能为空')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('标签数量不能超过20个')
        return v


class PromptTemplateResponse(CustomBaseModel):
    """提示词模板响应"""
    id: int
    name: str
    description: Optional[str]
    category_id: Optional[int]
    content: str
    variables: List[PromptVariableDefinition]
    tags: List[str]
    is_system: bool
    is_active: bool
    owner_id: int
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # 关联信息
    category_name: Optional[str] = Field(default=None, description="分类名称")
    owner_email: Optional[str] = Field(default=None, description="所有者邮箱")
    
    model_config = ConfigDict(from_attributes=True)


class PromptTemplateList(CustomBaseModel):
    """提示词模板列表响应"""
    templates: List[PromptTemplateResponse]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "templates": [
                    {
                        "id": 1,
                        "name": "知识库问答模板",
                        "description": "用于知识库问答的标准提示词模板",
                        "category_id": 1,
                        "content": "你是一个专业的AI助手...",
                        "variables": [],
                        "tags": ["问答", "知识库"],
                        "is_system": False,
                        "is_active": True,
                        "owner_id": 1,
                        "usage_count": 10,
                        "last_used_at": "2024-08-07T10:00:00",
                        "created_at": "2024-08-07T09:00:00",
                        "updated_at": "2024-08-07T09:30:00",
                        "category_name": "问答类",
                        "owner_email": "user@example.com"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
    )


class PromptTemplateRenderRequest(CustomBaseModel):
    """提示词模板渲染请求"""
    variables: Dict[str, Any] = Field(..., description="变量值映射")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "variables": {
                    "context": "这是检索到的上下文信息...",
                    "query": "用户的问题是什么？",
                    "max_tokens": 1000
                }
            }
        }
    )


class PromptTemplateRenderResponse(CustomBaseModel):
    """提示词模板渲染响应"""
    rendered_content: str = Field(..., description="渲染后的提示词内容")
    variables_used: Dict[str, Any] = Field(..., description="实际使用的变量值")
    missing_variables: List[str] = Field(default=[], description="缺失的必需变量")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rendered_content": "你是一个专业的AI助手，基于以下上下文回答用户问题。\n\n上下文信息：\n这是检索到的上下文信息...\n\n用户问题：\n用户的问题是什么？\n\n请基于上下文信息给出准确、有用的回答。",
                "variables_used": {
                    "context": "这是检索到的上下文信息...",
                    "query": "用户的问题是什么？"
                },
                "missing_variables": []
            }
        }
    )


class PromptTemplateValidateRequest(CustomBaseModel):
    """提示词模板验证请求"""
    content: str = Field(..., description="要验证的提示词内容")
    variables: Optional[List[PromptVariableDefinition]] = Field(default=[], description="变量定义列表")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "你好，{{name}}！今天是{{date}}。",
                "variables": [
                    {
                        "name": "name",
                        "type": "string",
                        "required": True,
                        "description": "用户姓名"
                    },
                    {
                        "name": "date",
                        "type": "string",
                        "required": True,
                        "description": "当前日期"
                    }
                ]
            }
        }
    )


class PromptTemplateValidateResponse(CustomBaseModel):
    """提示词模板验证响应"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default=[], description="错误信息列表")
    warnings: List[str] = Field(default=[], description="警告信息列表")
    extracted_variables: List[str] = Field(default=[], description="从内容中提取的变量名")
    undefined_variables: List[str] = Field(default=[], description="未定义的变量")
    unused_variables: List[str] = Field(default=[], description="定义但未使用的变量")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["变量 'optional_var' 已定义但未在内容中使用"],
                "extracted_variables": ["name", "date"],
                "undefined_variables": [],
                "unused_variables": ["optional_var"]
            }
        }
    )

class PromptCategoryCreate(CustomBaseModel):
    """创建提示词分类请求"""
    name: str = Field(..., min_length=1, max_length=255, description="分类名称")
    description: Optional[str] = Field(default=None, description="分类描述")
    parent_id: Optional[int] = Field(default=None, description="父分类ID")
    sort_order: int = Field(default=0, description="排序顺序")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "问答类",
                "description": "用于问答场景的提示词模板",
                "parent_id": None,
                "sort_order": 1
            }
        }
    )


class PromptCategoryUpdate(CustomBaseModel):
    """更新提示词分类请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="分类名称")
    description: Optional[str] = Field(default=None, description="分类描述")
    parent_id: Optional[int] = Field(default=None, description="父分类ID")
    sort_order: Optional[int] = Field(default=None, description="排序顺序")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


class PromptCategoryResponse(CustomBaseModel):
    """提示词分类响应"""
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    sort_order: int
    is_active: bool
    template_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # 关联信息
    parent_name: Optional[str] = Field(default=None, description="父分类名称")
    full_path: Optional[str] = Field(default=None, description="完整路径")
    children: Optional[List['PromptCategoryResponse']] = Field(default=[], description="子分类列表")
    
    model_config = ConfigDict(from_attributes=True)


class PromptVersionCreate(CustomBaseModel):
    """创建提示词版本请求"""
    content: str = Field(..., min_length=1, description="版本内容")
    variables: Optional[List[PromptVariableDefinition]] = Field(default=[], description="变量定义列表")
    change_log: Optional[str] = Field(default=None, description="版本变更说明")
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('版本内容不能为空')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "你是一个专业的AI助手，基于以下上下文回答用户问题...",
                "variables": [
                    {
                        "name": "context",
                        "type": "string",
                        "required": True,
                        "description": "上下文信息"
                    }
                ],
                "change_log": "优化了提示词的表达方式，提高了回答质量"
            }
        }
    )


class PromptVersionResponse(CustomBaseModel):
    """提示词版本响应"""
    id: int
    template_id: int
    version_number: str
    content: str
    variables: List[PromptVariableDefinition]
    change_log: Optional[str]
    is_published: bool
    is_current: bool
    created_by: Optional[int]
    created_at: Optional[datetime]
    published_at: Optional[datetime]
    
    # 关联信息
    creator_email: Optional[str] = Field(default=None, description="创建者邮箱")
    
    model_config = ConfigDict(from_attributes=True)


class PromptVersionList(CustomBaseModel):
    """提示词版本列表响应"""
    versions: List[PromptVersionResponse]
    total: int
    template_id: int
    template_name: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "versions": [
                    {
                        "id": 1,
                        "template_id": 1,
                        "version_number": "v1.0.0",
                        "content": "你是一个专业的AI助手...",
                        "variables": [],
                        "change_log": "初始版本",
                        "is_published": True,
                        "is_current": True,
                        "created_by": 1,
                        "created_at": "2024-08-07T09:00:00",
                        "published_at": "2024-08-07T09:30:00",
                        "creator_email": "user@example.com"
                    }
                ],
                "total": 1,
                "template_id": 1,
                "template_name": "知识库问答模板"
            }
        }
    )


class PromptVersionCompareRequest(CustomBaseModel):
    """版本比较请求"""
    version1_id: int = Field(..., description="版本1的ID")
    version2_id: int = Field(..., description="版本2的ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version1_id": 1,
                "version2_id": 2
            }
        }
    )


class PromptVersionCompareResponse(CustomBaseModel):
    """版本比较响应"""
    version1: PromptVersionResponse
    version2: PromptVersionResponse
    differences: Dict[str, Any] = Field(..., description="差异信息")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version1": {
                    "id": 1,
                    "version_number": "v1.0.0",
                    "content": "原始内容..."
                },
                "version2": {
                    "id": 2,
                    "version_number": "v1.1.0", 
                    "content": "修改后的内容..."
                },
                "differences": {
                    "content_changed": True,
                    "variables_changed": False,
                    "added_lines": ["新增的行内容"],
                    "removed_lines": ["删除的行内容"],
                    "modified_lines": [
                        {
                            "line_number": 5,
                            "old": "旧内容",
                            "new": "新内容"
                        }
                    ]
                }
            }
        }
    )


class PromptVersionRollbackRequest(CustomBaseModel):
    """版本回滚请求"""
    version_id: int = Field(..., description="要回滚到的版本ID")
    change_log: Optional[str] = Field(default=None, description="回滚说明")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version_id": 1,
                "change_log": "回滚到稳定版本v1.0.0"
            }
        }
    )


class PromptUsageLogResponse(CustomBaseModel):
    """提示词使用日志响应"""
    id: int
    template_id: int
    version_id: Optional[int]
    user_id: Optional[int]
    kb_id: Optional[int]
    query: Optional[str]
    variables_used: Dict[str, Any]
    response_quality: Optional[float]
    execution_time: Optional[float]
    token_count: Optional[int]
    cost: Optional[float]
    success: bool
    error_message: Optional[str]
    created_at: Optional[datetime]
    
    # 关联信息
    template_name: Optional[str] = Field(default=None, description="模板名称")
    version_number: Optional[str] = Field(default=None, description="版本号")
    user_email: Optional[str] = Field(default=None, description="用户邮箱")
    kb_name: Optional[str] = Field(default=None, description="知识库名称")
    
    model_config = ConfigDict(from_attributes=True)


class PromptUsageStats(CustomBaseModel):
    """提示词使用统计"""
    template_id: int
    template_name: str
    total_usage: int
    success_rate: float
    avg_execution_time: Optional[float]
    avg_response_quality: Optional[float]
    total_cost: Optional[float]
    last_used_at: Optional[datetime]
    usage_trend: List[Dict[str, Any]] = Field(default=[], description="使用趋势数据")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "template_id": 1,
                "template_name": "知识库问答模板",
                "total_usage": 100,
                "success_rate": 0.95,
                "avg_execution_time": 1.2,
                "avg_response_quality": 0.85,
                "total_cost": 0.05,
                "last_used_at": "2024-08-07T10:00:00",
                "usage_trend": [
                    {
                        "date": "2024-08-01",
                        "usage_count": 10,
                        "success_rate": 0.9
                    }
                ]
            }
        }
    )


# 解决循环引用问题
PromptCategoryResponse.model_rebuild()