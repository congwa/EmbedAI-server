from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from .base import CustomBaseModel

class ConfigType(str, Enum):
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

class ConfigCategory(str, Enum):
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

class SystemConfigBase(CustomBaseModel):
    """系统配置基础模型"""
    key: str = Field(..., description="配置键名")
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    category: ConfigCategory = Field(..., description="配置分类")
    type: ConfigType = Field(ConfigType.STRING, description="配置类型")
    is_sensitive: bool = Field(False, description="是否为敏感信息")
    is_required: bool = Field(False, description="是否必需")
    is_readonly: bool = Field(False, description="是否只读")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    options: Optional[List[str]] = Field(None, description="可选值列表")
    min_value: Optional[str] = Field(None, description="最小值")
    max_value: Optional[str] = Field(None, description="最大值")
    restart_required: bool = Field(False, description="修改后是否需要重启")

class SystemConfigCreate(SystemConfigBase):
    """创建系统配置请求模型"""
    default_value: Optional[str] = Field(None, description="默认值")
    is_system: bool = Field(False, description="是否为系统配置")

class SystemConfigUpdate(CustomBaseModel):
    """更新系统配置请求模型"""
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    is_required: Optional[bool] = Field(None, description="是否必需")
    is_readonly: Optional[bool] = Field(None, description="是否只读")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    options: Optional[List[str]] = Field(None, description="可选值列表")
    min_value: Optional[str] = Field(None, description="最小值")
    max_value: Optional[str] = Field(None, description="最大值")
    restart_required: Optional[bool] = Field(None, description="修改后是否需要重启")

class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模型"""
    id: int = Field(..., description="配置ID")
    default_value: Optional[str] = Field(None, description="默认值")
    is_system: bool = Field(..., description="是否为系统配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 敏感信息处理
    @validator('value', pre=False, always=True)
    def mask_sensitive_value(cls, v, values):
        if values.get('is_sensitive') and v:
            return "***MASKED***"
        return v

class SystemConfigBatchUpdate(CustomBaseModel):
    """批量更新配置请求模型"""
    configs: List[Dict[str, Any]] = Field(..., description="配置列表")
    reason: Optional[str] = Field(None, description="变更原因")

class ConfigChangeLogResponse(CustomBaseModel):
    """配置变更日志响应模型"""
    id: int = Field(..., description="日志ID")
    config_key: str = Field(..., description="配置键名")
    old_value: Optional[str] = Field(None, description="旧值")
    new_value: Optional[str] = Field(None, description="新值")
    change_type: str = Field(..., description="变更类型")
    user_email: Optional[str] = Field(None, description="操作用户邮箱")
    ip_address: Optional[str] = Field(None, description="操作IP地址")
    reason: Optional[str] = Field(None, description="变更原因")
    created_at: datetime = Field(..., description="变更时间")

class ConfigTemplateBase(CustomBaseModel):
    """配置模板基础模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: ConfigCategory = Field(..., description="模板分类")
    template_data: Dict[str, Any] = Field(..., description="模板配置数据")
    version: str = Field("1.0.0", description="模板版本")

class ConfigTemplateCreate(ConfigTemplateBase):
    """创建配置模板请求模型"""
    is_system: bool = Field(False, description="是否为系统模板")
    is_active: bool = Field(True, description="是否激活")

class ConfigTemplateUpdate(CustomBaseModel):
    """更新配置模板请求模型"""
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_data: Optional[Dict[str, Any]] = Field(None, description="模板配置数据")
    is_active: Optional[bool] = Field(None, description="是否激活")
    version: Optional[str] = Field(None, description="模板版本")

class ConfigTemplateResponse(ConfigTemplateBase):
    """配置模板响应模型"""
    id: int = Field(..., description="模板ID")
    is_system: bool = Field(..., description="是否为系统模板")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")

class ConfigBackupCreate(CustomBaseModel):
    """创建配置备份请求模型"""
    name: str = Field(..., description="备份名称")
    description: Optional[str] = Field(None, description="备份描述")
    categories: Optional[List[ConfigCategory]] = Field(None, description="备份的配置分类")

class ConfigBackupResponse(CustomBaseModel):
    """配置备份响应模型"""
    id: int = Field(..., description="备份ID")
    name: str = Field(..., description="备份名称")
    description: Optional[str] = Field(None, description="备份描述")
    config_count: int = Field(..., description="配置项数量")
    backup_type: str = Field(..., description="备份类型")
    created_at: datetime = Field(..., description="备份时间")
    created_by_email: Optional[str] = Field(None, description="备份人邮箱")

class ConfigRestoreRequest(CustomBaseModel):
    """配置恢复请求模型"""
    backup_id: int = Field(..., description="备份ID")
    categories: Optional[List[ConfigCategory]] = Field(None, description="恢复的配置分类")
    overwrite_existing: bool = Field(False, description="是否覆盖现有配置")

class EnvironmentVariableBase(CustomBaseModel):
    """环境变量基础模型"""
    name: str = Field(..., description="变量名")
    value: Optional[str] = Field(None, description="变量值")
    description: Optional[str] = Field(None, description="变量描述")
    category: ConfigCategory = Field(..., description="变量分类")
    is_sensitive: bool = Field(False, description="是否为敏感信息")
    is_required: bool = Field(False, description="是否必需")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    default_value: Optional[str] = Field(None, description="默认值")
    restart_required: bool = Field(True, description="修改后是否需要重启")

class EnvironmentVariableCreate(EnvironmentVariableBase):
    """创建环境变量请求模型"""
    is_system: bool = Field(False, description="是否为系统变量")

class EnvironmentVariableUpdate(CustomBaseModel):
    """更新环境变量请求模型"""
    value: Optional[str] = Field(None, description="变量值")
    description: Optional[str] = Field(None, description="变量描述")
    is_required: Optional[bool] = Field(None, description="是否必需")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    restart_required: Optional[bool] = Field(None, description="修改后是否需要重启")

class EnvironmentVariableResponse(EnvironmentVariableBase):
    """环境变量响应模型"""
    id: int = Field(..., description="变量ID")
    is_system: bool = Field(..., description="是否为系统变量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 敏感信息处理
    @validator('value', pre=False, always=True)
    def mask_sensitive_value(cls, v, values):
        if values.get('is_sensitive') and v:
            return "***MASKED***"
        return v

class ConfigValidationRequest(CustomBaseModel):
    """配置验证请求模型"""
    configs: List[Dict[str, Any]] = Field(..., description="待验证的配置列表")

class ConfigValidationResult(CustomBaseModel):
    """配置验证结果模型"""
    is_valid: bool = Field(..., description="是否验证通过")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="验证错误列表")
    warnings: List[Dict[str, str]] = Field(default_factory=list, description="验证警告列表")

class ConfigExportRequest(CustomBaseModel):
    """配置导出请求模型"""
    categories: Optional[List[ConfigCategory]] = Field(None, description="导出的配置分类")
    include_sensitive: bool = Field(False, description="是否包含敏感信息")
    format: str = Field("json", description="导出格式")

class ConfigImportRequest(CustomBaseModel):
    """配置导入请求模型"""
    data: Dict[str, Any] = Field(..., description="导入的配置数据")
    overwrite_existing: bool = Field(False, description="是否覆盖现有配置")
    validate_only: bool = Field(False, description="是否仅验证不导入")

class ConfigImportResult(CustomBaseModel):
    """配置导入结果模型"""
    total_count: int = Field(..., description="总配置数量")
    success_count: int = Field(..., description="成功导入数量")
    failed_count: int = Field(..., description="失败数量")
    skipped_count: int = Field(..., description="跳过数量")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="错误列表")

class ConfigDashboardResponse(CustomBaseModel):
    """配置管理仪表板响应模型"""
    total_configs: int = Field(..., description="总配置数量")
    configs_by_category: Dict[str, int] = Field(..., description="按分类统计的配置数量")
    sensitive_configs: int = Field(..., description="敏感配置数量")
    readonly_configs: int = Field(..., description="只读配置数量")
    recent_changes: List[ConfigChangeLogResponse] = Field(..., description="最近变更记录")
    backup_count: int = Field(..., description="备份数量")
    template_count: int = Field(..., description="模板数量")
    env_var_count: int = Field(..., description="环境变量数量")
