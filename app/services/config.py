import json
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, delete
from sqlalchemy.orm import selectinload

from app.models.config import (
    SystemConfig, ConfigChangeLog, ConfigTemplate, ConfigBackup,
    EnvironmentVariable, ConfigValidationRule, ConfigType, ConfigCategory
)
from app.schemas.config import (
    SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse,
    ConfigTemplateCreate, ConfigTemplateUpdate, ConfigTemplateResponse,
    ConfigBackupCreate, ConfigBackupResponse, ConfigRestoreRequest,
    EnvironmentVariableCreate, EnvironmentVariableUpdate, EnvironmentVariableResponse,
    ConfigValidationRequest, ConfigValidationResult, ConfigExportRequest,
    ConfigImportRequest, ConfigImportResult, ConfigDashboardResponse,
    SystemConfigBatchUpdate, ConfigChangeLogResponse
)
from app.core.logger import Logger
from app.core.redis_manager import redis_manager

class ConfigService:
    """配置管理服务
    
    提供系统配置、环境变量、配置模板等管理功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 系统配置管理 ====================
    
    async def get_dashboard_data(self) -> ConfigDashboardResponse:
        """获取配置管理仪表板数据"""
        try:
            # 总配置数量
            total_configs_result = await self.db.execute(select(func.count(SystemConfig.id)))
            total_configs = total_configs_result.scalar() or 0
            
            # 按分类统计
            category_stats = await self.db.execute(
                select(SystemConfig.category, func.count(SystemConfig.id))
                .group_by(SystemConfig.category)
            )
            configs_by_category = {cat.value: count for cat, count in category_stats.fetchall()}
            
            # 敏感配置数量
            sensitive_result = await self.db.execute(
                select(func.count(SystemConfig.id)).where(SystemConfig.is_sensitive == True)
            )
            sensitive_configs = sensitive_result.scalar() or 0
            
            # 只读配置数量
            readonly_result = await self.db.execute(
                select(func.count(SystemConfig.id)).where(SystemConfig.is_readonly == True)
            )
            readonly_configs = readonly_result.scalar() or 0
            
            # 最近变更记录
            recent_changes_result = await self.db.execute(
                select(ConfigChangeLog)
                .order_by(desc(ConfigChangeLog.created_at))
                .limit(10)
            )
            recent_changes = [
                ConfigChangeLogResponse(
                    id=log.id,
                    config_key=log.config_key,
                    old_value=log.old_value if not log.config_key.endswith('_password') else "***MASKED***",
                    new_value=log.new_value if not log.config_key.endswith('_password') else "***MASKED***",
                    change_type=log.change_type,
                    user_email=log.user_email,
                    ip_address=log.ip_address,
                    reason=log.reason,
                    created_at=log.created_at
                ) for log in recent_changes_result.scalars().all()
            ]
            
            # 备份数量
            backup_result = await self.db.execute(select(func.count(ConfigBackup.id)))
            backup_count = backup_result.scalar() or 0
            
            # 模板数量
            template_result = await self.db.execute(select(func.count(ConfigTemplate.id)))
            template_count = template_result.scalar() or 0
            
            # 环境变量数量
            env_var_result = await self.db.execute(select(func.count(EnvironmentVariable.id)))
            env_var_count = env_var_result.scalar() or 0
            
            return ConfigDashboardResponse(
                total_configs=total_configs,
                configs_by_category=configs_by_category,
                sensitive_configs=sensitive_configs,
                readonly_configs=readonly_configs,
                recent_changes=recent_changes,
                backup_count=backup_count,
                template_count=template_count,
                env_var_count=env_var_count
            )
            
        except Exception as e:
            Logger.error(f"获取配置仪表板数据失败: {str(e)}")
            raise
    
    async def create_config(self, config_data: SystemConfigCreate) -> SystemConfigResponse:
        """创建系统配置"""
        try:
            # 检查配置键是否已存在
            existing = await self.db.execute(
                select(SystemConfig).where(SystemConfig.key == config_data.key)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"配置键 {config_data.key} 已存在")
            
            # 验证配置值
            if config_data.value is not None:
                await self._validate_config_value(config_data.key, config_data.value, config_data.type, config_data.validation_rule)
            
            config = SystemConfig(**config_data.model_dump())
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            
            # 清除配置缓存
            await self._clear_config_cache()
            
            return await self._build_config_response(config)
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建系统配置失败: {str(e)}")
            raise
    
    async def get_configs(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[ConfigCategory] = None,
        search: Optional[str] = None,
        include_sensitive: bool = False
    ) -> List[SystemConfigResponse]:
        """获取系统配置列表"""
        try:
            query = select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
            
            if category:
                query = query.where(SystemConfig.category == category)
            
            if search:
                query = query.where(
                    or_(
                        SystemConfig.key.ilike(f"%{search}%"),
                        SystemConfig.description.ilike(f"%{search}%")
                    )
                )
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            configs = result.scalars().all()
            
            return [await self._build_config_response(config, include_sensitive) for config in configs]
            
        except Exception as e:
            Logger.error(f"获取系统配置列表失败: {str(e)}")
            raise
    
    async def get_config_by_key(self, key: str, include_sensitive: bool = False) -> Optional[SystemConfigResponse]:
        """根据键获取配置"""
        try:
            # 先尝试从缓存获取
            if not include_sensitive:
                cached_config = await redis_manager.get(f"config:{key}")
                if cached_config:
                    return SystemConfigResponse.parse_raw(cached_config)
            
            config = await self.db.get(SystemConfig, key)
            if not config:
                return None
            
            response = await self._build_config_response(config, include_sensitive)
            
            # 缓存非敏感配置
            if not config.is_sensitive:
                await redis_manager.set(f"config:{key}", response.json(), expire=3600)
            
            return response
            
        except Exception as e:
            Logger.error(f"获取配置失败: {str(e)}")
            return None
    
    async def update_config(
        self,
        config_id: int,
        config_data: SystemConfigUpdate,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> SystemConfigResponse:
        """更新系统配置"""
        try:
            config = await self.db.get(SystemConfig, config_id)
            if not config:
                raise ValueError("配置不存在")
            
            if config.is_readonly:
                raise ValueError("只读配置不能修改")
            
            # 记录旧值
            old_value = config.value
            
            # 验证新值
            if config_data.value is not None:
                await self._validate_config_value(config.key, config_data.value, config.type, config_data.validation_rule or config.validation_rule)
            
            # 更新配置
            update_data = config_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
            
            await self.db.commit()
            await self.db.refresh(config)
            
            # 记录变更日志
            if old_value != config.value:
                await self._log_config_change(
                    config=config,
                    old_value=old_value,
                    new_value=config.value,
                    change_type="update",
                    user_id=user_id,
                    user_email=user_email,
                    ip_address=ip_address,
                    reason=reason
                )
            
            # 清除配置缓存
            await self._clear_config_cache(config.key)
            
            return await self._build_config_response(config)
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"更新系统配置失败: {str(e)}")
            raise
    
    async def batch_update_configs(
        self,
        batch_data: SystemConfigBatchUpdate,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量更新配置"""
        try:
            results = {
                "total": len(batch_data.configs),
                "success": 0,
                "failed": 0,
                "errors": []
            }
            
            for config_item in batch_data.configs:
                try:
                    config_id = config_item.get("id")
                    if not config_id:
                        raise ValueError("配置ID不能为空")
                    
                    update_data = SystemConfigUpdate(**{k: v for k, v in config_item.items() if k != "id"})
                    await self.update_config(
                        config_id=config_id,
                        config_data=update_data,
                        user_id=user_id,
                        user_email=user_email,
                        ip_address=ip_address,
                        reason=batch_data.reason
                    )
                    results["success"] += 1
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "config_id": config_item.get("id"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            Logger.error(f"批量更新配置失败: {str(e)}")
            raise
    
    # ==================== 配置模板管理 ====================
    
    async def create_template(self, template_data: ConfigTemplateCreate, created_by: Optional[int] = None) -> ConfigTemplateResponse:
        """创建配置模板"""
        try:
            # 检查模板名称是否已存在
            existing = await self.db.execute(
                select(ConfigTemplate).where(ConfigTemplate.name == template_data.name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"模板名称 {template_data.name} 已存在")
            
            template = ConfigTemplate(**template_data.model_dump(), created_by=created_by)
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            return ConfigTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                category=template.category,
                template_data=template.template_data,
                is_system=template.is_system,
                is_active=template.is_active,
                version=template.version,
                created_at=template.created_at,
                updated_at=template.updated_at,
                created_by=template.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建配置模板失败: {str(e)}")
            raise
    
    async def apply_template(self, template_id: int, overwrite_existing: bool = False) -> Dict[str, Any]:
        """应用配置模板"""
        try:
            template = await self.db.get(ConfigTemplate, template_id)
            if not template:
                raise ValueError("模板不存在")
            
            if not template.is_active:
                raise ValueError("模板未激活")
            
            results = {
                "total": len(template.template_data),
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "errors": []
            }
            
            for config_key, config_data in template.template_data.items():
                try:
                    # 检查配置是否已存在
                    existing = await self.db.execute(
                        select(SystemConfig).where(SystemConfig.key == config_key)
                    )
                    existing_config = existing.scalar_one_or_none()
                    
                    if existing_config:
                        if overwrite_existing and not existing_config.is_readonly:
                            # 更新现有配置
                            for field, value in config_data.items():
                                if hasattr(existing_config, field):
                                    setattr(existing_config, field, value)
                            results["updated"] += 1
                        else:
                            results["skipped"] += 1
                    else:
                        # 创建新配置
                        new_config = SystemConfig(key=config_key, **config_data)
                        self.db.add(new_config)
                        results["created"] += 1
                        
                except Exception as e:
                    results["errors"].append({
                        "config_key": config_key,
                        "error": str(e)
                    })
            
            await self.db.commit()
            await self._clear_config_cache()
            
            return results
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"应用配置模板失败: {str(e)}")
            raise
    
    # ==================== 配置备份与恢复 ====================
    
    async def create_backup(
        self,
        backup_data: ConfigBackupCreate,
        created_by: Optional[int] = None,
        created_by_email: Optional[str] = None
    ) -> ConfigBackupResponse:
        """创建配置备份"""
        try:
            # 获取要备份的配置
            query = select(SystemConfig)
            if backup_data.categories:
                query = query.where(SystemConfig.category.in_(backup_data.categories))
            
            result = await self.db.execute(query)
            configs = result.scalars().all()
            
            # 构建备份数据
            backup_configs = {}
            for config in configs:
                backup_configs[config.key] = {
                    "value": config.value,
                    "default_value": config.default_value,
                    "description": config.description,
                    "category": config.category.value,
                    "type": config.type.value,
                    "is_sensitive": config.is_sensitive,
                    "is_required": config.is_required,
                    "is_readonly": config.is_readonly,
                    "is_system": config.is_system,
                    "validation_rule": config.validation_rule,
                    "options": config.options,
                    "min_value": config.min_value,
                    "max_value": config.max_value,
                    "restart_required": config.restart_required
                }
            
            backup = ConfigBackup(
                name=backup_data.name,
                description=backup_data.description,
                backup_data=backup_configs,
                config_count=len(backup_configs),
                backup_type="manual",
                created_by=created_by,
                created_by_email=created_by_email
            )
            
            self.db.add(backup)
            await self.db.commit()
            await self.db.refresh(backup)
            
            return ConfigBackupResponse(
                id=backup.id,
                name=backup.name,
                description=backup.description,
                config_count=backup.config_count,
                backup_type=backup.backup_type,
                created_at=backup.created_at,
                created_by_email=backup.created_by_email
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建配置备份失败: {str(e)}")
            raise
    
    # ==================== 辅助方法 ====================
    
    async def _build_config_response(self, config: SystemConfig, include_sensitive: bool = False) -> SystemConfigResponse:
        """构建配置响应对象"""
        value = config.value
        if config.is_sensitive and not include_sensitive and value:
            value = "***MASKED***"
        
        return SystemConfigResponse(
            id=config.id,
            key=config.key,
            value=value,
            default_value=config.default_value,
            description=config.description,
            category=config.category,
            type=config.type,
            is_sensitive=config.is_sensitive,
            is_required=config.is_required,
            is_readonly=config.is_readonly,
            is_system=config.is_system,
            validation_rule=config.validation_rule,
            options=config.options,
            min_value=config.min_value,
            max_value=config.max_value,
            restart_required=config.restart_required,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    
    async def _validate_config_value(self, key: str, value: str, config_type: ConfigType, validation_rule: Optional[str] = None) -> bool:
        """验证配置值"""
        try:
            # 类型验证
            if config_type == ConfigType.INTEGER:
                int(value)
            elif config_type == ConfigType.FLOAT:
                float(value)
            elif config_type == ConfigType.BOOLEAN:
                if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    raise ValueError("布尔值必须是 true/false, 1/0, yes/no")
            elif config_type == ConfigType.JSON:
                json.loads(value)
            elif config_type == ConfigType.EMAIL:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, value):
                    raise ValueError("无效的邮箱格式")
            elif config_type == ConfigType.URL:
                url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                if not re.match(url_pattern, value):
                    raise ValueError("无效的URL格式")
            
            # 自定义验证规则
            if validation_rule:
                if not re.match(validation_rule, value):
                    raise ValueError(f"值不符合验证规则: {validation_rule}")
            
            return True
            
        except Exception as e:
            raise ValueError(f"配置值验证失败: {str(e)}")
    
    async def _log_config_change(
        self,
        config: SystemConfig,
        old_value: Optional[str],
        new_value: Optional[str],
        change_type: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """记录配置变更日志"""
        try:
            log = ConfigChangeLog(
                config_id=config.id,
                config_key=config.key,
                old_value=old_value if not config.is_sensitive else "***MASKED***",
                new_value=new_value if not config.is_sensitive else "***MASKED***",
                change_type=change_type,
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                reason=reason
            )
            self.db.add(log)
            await self.db.commit()
            
        except Exception as e:
            Logger.warning(f"记录配置变更日志失败: {str(e)}")
    
    async def _clear_config_cache(self, key: Optional[str] = None):
        """清除配置缓存"""
        try:
            if key:
                await redis_manager.delete(f"config:{key}")
            else:
                # 清除所有配置缓存
                keys = await redis_manager.keys("config:*")
                if keys:
                    await redis_manager.delete(*keys)
        except Exception as e:
            Logger.warning(f"清除配置缓存失败: {str(e)}")

    # ==================== 环境变量管理 ====================

    async def create_env_var(self, env_data: EnvironmentVariableCreate) -> EnvironmentVariableResponse:
        """创建环境变量"""
        try:
            # 检查变量名是否已存在
            existing = await self.db.execute(
                select(EnvironmentVariable).where(EnvironmentVariable.name == env_data.name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"环境变量 {env_data.name} 已存在")

            # 验证变量值
            if env_data.value is not None and env_data.validation_rule:
                if not re.match(env_data.validation_rule, env_data.value):
                    raise ValueError(f"变量值不符合验证规则: {env_data.validation_rule}")

            env_var = EnvironmentVariable(**env_data.model_dump())
            self.db.add(env_var)
            await self.db.commit()
            await self.db.refresh(env_var)

            return await self._build_env_var_response(env_var)

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建环境变量失败: {str(e)}")
            raise

    async def get_env_vars(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[ConfigCategory] = None,
        include_sensitive: bool = False
    ) -> List[EnvironmentVariableResponse]:
        """获取环境变量列表"""
        try:
            query = select(EnvironmentVariable).order_by(EnvironmentVariable.category, EnvironmentVariable.name)

            if category:
                query = query.where(EnvironmentVariable.category == category)

            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            env_vars = result.scalars().all()

            return [await self._build_env_var_response(env_var, include_sensitive) for env_var in env_vars]

        except Exception as e:
            Logger.error(f"获取环境变量列表失败: {str(e)}")
            raise

    async def update_env_var(
        self,
        env_var_id: int,
        env_data: EnvironmentVariableUpdate
    ) -> EnvironmentVariableResponse:
        """更新环境变量"""
        try:
            env_var = await self.db.get(EnvironmentVariable, env_var_id)
            if not env_var:
                raise ValueError("环境变量不存在")

            if env_var.is_system:
                raise ValueError("系统环境变量不能修改")

            # 验证新值
            if env_data.value is not None and (env_data.validation_rule or env_var.validation_rule):
                validation_rule = env_data.validation_rule or env_var.validation_rule
                if not re.match(validation_rule, env_data.value):
                    raise ValueError(f"变量值不符合验证规则: {validation_rule}")

            # 更新环境变量
            update_data = env_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(env_var, field, value)

            await self.db.commit()
            await self.db.refresh(env_var)

            return await self._build_env_var_response(env_var)

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"更新环境变量失败: {str(e)}")
            raise

    async def sync_env_vars_to_os(self) -> Dict[str, Any]:
        """同步环境变量到操作系统"""
        try:
            result = await self.db.execute(select(EnvironmentVariable))
            env_vars = result.scalars().all()

            results = {
                "total": len(env_vars),
                "synced": 0,
                "errors": []
            }

            for env_var in env_vars:
                try:
                    if env_var.value is not None:
                        os.environ[env_var.name] = env_var.value
                        results["synced"] += 1
                except Exception as e:
                    results["errors"].append({
                        "name": env_var.name,
                        "error": str(e)
                    })

            return results

        except Exception as e:
            Logger.error(f"同步环境变量失败: {str(e)}")
            raise

    # ==================== 配置验证 ====================

    async def validate_configs(self, validation_request: ConfigValidationRequest) -> ConfigValidationResult:
        """验证配置"""
        try:
            errors = []
            warnings = []

            for config_data in validation_request.configs:
                config_key = config_data.get("key")
                config_value = config_data.get("value")
                config_type = config_data.get("type", "string")
                validation_rule = config_data.get("validation_rule")

                if not config_key:
                    errors.append({"key": "unknown", "error": "配置键不能为空"})
                    continue

                try:
                    # 类型验证
                    if config_value is not None:
                        await self._validate_config_value(config_key, str(config_value), ConfigType(config_type), validation_rule)

                    # 检查是否与现有配置冲突
                    existing = await self.db.execute(
                        select(SystemConfig).where(SystemConfig.key == config_key)
                    )
                    if existing.scalar_one_or_none():
                        warnings.append({"key": config_key, "warning": "配置键已存在，导入时将被跳过"})

                except Exception as e:
                    errors.append({"key": config_key, "error": str(e)})

            return ConfigValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            Logger.error(f"验证配置失败: {str(e)}")
            raise

    # ==================== 配置导入导出 ====================

    async def export_configs(self, export_request: ConfigExportRequest) -> Dict[str, Any]:
        """导出配置"""
        try:
            query = select(SystemConfig)

            if export_request.categories:
                query = query.where(SystemConfig.category.in_(export_request.categories))

            result = await self.db.execute(query)
            configs = result.scalars().all()

            export_data = {}
            for config in configs:
                value = config.value
                if config.is_sensitive and not export_request.include_sensitive:
                    value = None

                export_data[config.key] = {
                    "value": value,
                    "default_value": config.default_value,
                    "description": config.description,
                    "category": config.category.value,
                    "type": config.type.value,
                    "is_sensitive": config.is_sensitive,
                    "is_required": config.is_required,
                    "is_readonly": config.is_readonly,
                    "validation_rule": config.validation_rule,
                    "options": config.options,
                    "min_value": config.min_value,
                    "max_value": config.max_value,
                    "restart_required": config.restart_required
                }

            return {
                "format": export_request.format,
                "exported_at": datetime.now().isoformat(),
                "config_count": len(export_data),
                "data": export_data
            }

        except Exception as e:
            Logger.error(f"导出配置失败: {str(e)}")
            raise

    async def import_configs(self, import_request: ConfigImportRequest) -> ConfigImportResult:
        """导入配置"""
        try:
            results = ConfigImportResult(
                total_count=len(import_request.data),
                success_count=0,
                failed_count=0,
                skipped_count=0,
                errors=[]
            )

            if import_request.validate_only:
                # 仅验证，不实际导入
                validation_request = ConfigValidationRequest(
                    configs=[{"key": k, **v} for k, v in import_request.data.items()]
                )
                validation_result = await self.validate_configs(validation_request)
                results.errors = validation_result.errors
                results.failed_count = len(validation_result.errors)
                results.success_count = results.total_count - results.failed_count
                return results

            for config_key, config_data in import_request.data.items():
                try:
                    # 检查配置是否已存在
                    existing = await self.db.execute(
                        select(SystemConfig).where(SystemConfig.key == config_key)
                    )
                    existing_config = existing.scalar_one_or_none()

                    if existing_config:
                        if import_request.overwrite_existing and not existing_config.is_readonly:
                            # 更新现有配置
                            for field, value in config_data.items():
                                if hasattr(existing_config, field) and field != "is_system":
                                    setattr(existing_config, field, value)
                            results.success_count += 1
                        else:
                            results.skipped_count += 1
                    else:
                        # 创建新配置
                        new_config = SystemConfig(key=config_key, **config_data)
                        self.db.add(new_config)
                        results.success_count += 1

                except Exception as e:
                    results.failed_count += 1
                    results.errors.append({
                        "key": config_key,
                        "error": str(e)
                    })

            if not import_request.validate_only:
                await self.db.commit()
                await self._clear_config_cache()

            return results

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"导入配置失败: {str(e)}")
            raise

    # ==================== 辅助方法 ====================

    async def _build_env_var_response(self, env_var: EnvironmentVariable, include_sensitive: bool = False) -> EnvironmentVariableResponse:
        """构建环境变量响应对象"""
        value = env_var.value
        if env_var.is_sensitive and not include_sensitive and value:
            value = "***MASKED***"

        return EnvironmentVariableResponse(
            id=env_var.id,
            name=env_var.name,
            value=value,
            description=env_var.description,
            category=env_var.category,
            is_sensitive=env_var.is_sensitive,
            is_required=env_var.is_required,
            is_system=env_var.is_system,
            validation_rule=env_var.validation_rule,
            default_value=env_var.default_value,
            restart_required=env_var.restart_required,
            created_at=env_var.created_at,
            updated_at=env_var.updated_at
        )
