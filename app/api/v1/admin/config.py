from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import io

from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.services.config import ConfigService
from app.core.response import APIResponse, ResponseModel
from app.schemas.config import (
    SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse,
    ConfigTemplateCreate, ConfigTemplateUpdate, ConfigTemplateResponse,
    ConfigBackupCreate, ConfigBackupResponse, ConfigRestoreRequest,
    EnvironmentVariableCreate, EnvironmentVariableUpdate, EnvironmentVariableResponse,
    ConfigValidationRequest, ConfigValidationResult, ConfigExportRequest,
    ConfigImportRequest, ConfigImportResult, ConfigDashboardResponse,
    SystemConfigBatchUpdate, ConfigChangeLogResponse, ConfigCategory
)
from app.models.user import User
from app.core.logger import Logger

router = APIRouter(tags=["admin-config"])

# ==================== 配置管理仪表板 ====================

@router.get("/dashboard", response_model=ResponseModel[ConfigDashboardResponse])
async def get_config_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取配置管理仪表板数据"""
    try:
        config_service = ConfigService(db)
        dashboard_data = await config_service.get_dashboard_data()
        return APIResponse.success(data=dashboard_data)
        
    except Exception as e:
        Logger.error(f"获取配置仪表板数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置仪表板数据失败")

# ==================== 系统配置管理 ====================

@router.post("/configs", response_model=ResponseModel[SystemConfigResponse])
async def create_config(
    config_data: SystemConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建系统配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.create_config(config_data)
        return APIResponse.success(data=config)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"创建系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建系统配置失败")

@router.get("/configs", response_model=ResponseModel[List[SystemConfigResponse]])
async def get_configs(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    category: Optional[ConfigCategory] = Query(None, description="配置分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    include_sensitive: bool = Query(False, description="是否包含敏感信息"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统配置列表"""
    try:
        config_service = ConfigService(db)
        configs = await config_service.get_configs(
            skip=skip, limit=limit, category=category, 
            search=search, include_sensitive=include_sensitive
        )
        return APIResponse.success(data=configs)
        
    except Exception as e:
        Logger.error(f"获取系统配置列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统配置列表失败")

@router.get("/configs/{config_id}", response_model=ResponseModel[SystemConfigResponse])
async def get_config(
    config_id: int,
    include_sensitive: bool = Query(False, description="是否包含敏感信息"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个系统配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_key(str(config_id), include_sensitive)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        return APIResponse.success(data=config)
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统配置失败")

@router.put("/configs/{config_id}", response_model=ResponseModel[SystemConfigResponse])
async def update_config(
    config_id: int,
    config_data: SystemConfigUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新系统配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.update_config(
            config_id=config_id,
            config_data=config_data,
            user_id=current_admin.id,
            user_email=current_admin.email,
            ip_address=request.client.host if request.client else None
        )
        return APIResponse.success(data=config)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"更新系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新系统配置失败")

@router.post("/configs/batch-update", response_model=ResponseModel[dict])
async def batch_update_configs(
    batch_data: SystemConfigBatchUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新系统配置"""
    try:
        config_service = ConfigService(db)
        result = await config_service.batch_update_configs(
            batch_data=batch_data,
            user_id=current_admin.id,
            user_email=current_admin.email,
            ip_address=request.client.host if request.client else None
        )
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"批量更新系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量更新系统配置失败")

# ==================== 配置模板管理 ====================

@router.post("/templates", response_model=ResponseModel[ConfigTemplateResponse])
async def create_template(
    template_data: ConfigTemplateCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建配置模板"""
    try:
        config_service = ConfigService(db)
        template = await config_service.create_template(template_data, current_admin.id)
        return APIResponse.success(data=template)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"创建配置模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建配置模板失败")

@router.post("/templates/{template_id}/apply", response_model=ResponseModel[dict])
async def apply_template(
    template_id: int,
    overwrite_existing: bool = Query(False, description="是否覆盖现有配置"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """应用配置模板"""
    try:
        config_service = ConfigService(db)
        result = await config_service.apply_template(template_id, overwrite_existing)
        return APIResponse.success(data=result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"应用配置模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail="应用配置模板失败")

# ==================== 配置备份与恢复 ====================

@router.post("/backups", response_model=ResponseModel[ConfigBackupResponse])
async def create_backup(
    backup_data: ConfigBackupCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建配置备份"""
    try:
        config_service = ConfigService(db)
        backup = await config_service.create_backup(
            backup_data=backup_data,
            created_by=current_admin.id,
            created_by_email=current_admin.email
        )
        return APIResponse.success(data=backup)
        
    except Exception as e:
        Logger.error(f"创建配置备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建配置备份失败")

# ==================== 环境变量管理 ====================

@router.post("/env-vars", response_model=ResponseModel[EnvironmentVariableResponse])
async def create_env_var(
    env_data: EnvironmentVariableCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建环境变量"""
    try:
        config_service = ConfigService(db)
        env_var = await config_service.create_env_var(env_data)
        return APIResponse.success(data=env_var)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"创建环境变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建环境变量失败")

@router.get("/env-vars", response_model=ResponseModel[List[EnvironmentVariableResponse]])
async def get_env_vars(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    category: Optional[ConfigCategory] = Query(None, description="变量分类"),
    include_sensitive: bool = Query(False, description="是否包含敏感信息"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取环境变量列表"""
    try:
        config_service = ConfigService(db)
        env_vars = await config_service.get_env_vars(
            skip=skip, limit=limit, category=category, include_sensitive=include_sensitive
        )
        return APIResponse.success(data=env_vars)
        
    except Exception as e:
        Logger.error(f"获取环境变量列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取环境变量列表失败")

@router.put("/env-vars/{env_var_id}", response_model=ResponseModel[EnvironmentVariableResponse])
async def update_env_var(
    env_var_id: int,
    env_data: EnvironmentVariableUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新环境变量"""
    try:
        config_service = ConfigService(db)
        env_var = await config_service.update_env_var(env_var_id, env_data)
        return APIResponse.success(data=env_var)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"更新环境变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新环境变量失败")

@router.post("/env-vars/sync", response_model=ResponseModel[dict])
async def sync_env_vars(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """同步环境变量到操作系统"""
    try:
        config_service = ConfigService(db)
        result = await config_service.sync_env_vars_to_os()
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"同步环境变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail="同步环境变量失败")

# ==================== 配置验证 ====================

@router.post("/validate", response_model=ResponseModel[ConfigValidationResult])
async def validate_configs(
    validation_request: ConfigValidationRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """验证配置"""
    try:
        config_service = ConfigService(db)
        result = await config_service.validate_configs(validation_request)
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"验证配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="验证配置失败")

# ==================== 配置导入导出 ====================

@router.post("/export")
async def export_configs(
    export_request: ConfigExportRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """导出配置"""
    try:
        config_service = ConfigService(db)
        export_data = await config_service.export_configs(export_request)
        
        if export_request.format == "json":
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            return StreamingResponse(
                io.BytesIO(json_data.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=config_export.json"}
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"导出配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出配置失败")

@router.post("/import", response_model=ResponseModel[ConfigImportResult])
async def import_configs(
    import_request: ConfigImportRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """导入配置"""
    try:
        config_service = ConfigService(db)
        result = await config_service.import_configs(import_request)
        return APIResponse.success(data=result)
        
    except Exception as e:
        Logger.error(f"导入配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导入配置失败")
