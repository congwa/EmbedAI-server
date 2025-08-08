from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import io

from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.services.config import ConfigService
from app.core.response import ResponseModel
from app.core.exceptions import (
    APIException,
    SystemException,
    ResourceNotFoundException,
    BusinessException,
    ConfigurationException
)
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
    config_service = ConfigService(db)
    dashboard_data = await config_service.get_dashboard_data()
    
    return ResponseModel.create_success(
        data=dashboard_data,
        message="获取配置仪表板数据成功"
    )

# ==================== 提示词管理配置 ====================

@router.get("/prompt", response_model=ResponseModel[Dict[str, Any]])
async def get_prompt_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词管理配置"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    config = await config_manager.get_prompt_config()
    
    return ResponseModel.create_success(
        data=config,
        message="获取提示词配置成功"
    )

@router.put("/prompt", response_model=ResponseModel[Dict[str, Any]])
async def update_prompt_config(
    config_updates: Dict[str, Any],
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新提示词管理配置"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    
    # 验证配置更新数据
    if not config_updates:
        raise BusinessException("配置更新数据不能为空")
    
    updated_config = await config_manager.update_prompt_config(
        config_updates=config_updates,
        user_id=current_admin.id
    )
    
    return ResponseModel.create_success(
        data=updated_config,
        message="更新提示词配置成功"
    )

@router.post("/prompt/reset", response_model=ResponseModel[Dict[str, Any]])
async def reset_prompt_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """重置提示词配置为默认值"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    reset_config = await config_manager.reset_prompt_config(user_id=current_admin.id)
    
    return ResponseModel.create_success(
        data=reset_config,
        message="重置提示词配置成功"
    )

@router.get("/prompt/history", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_prompt_config_history(
    limit: int = Query(10, ge=1, le=100, description="返回记录数量"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词配置变更历史"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    history = await config_manager.get_config_history(
        config_type="prompt",
        limit=limit
    )
    
    return ResponseModel.create_success(
        data=history,
        message="获取提示词配置历史成功"
    )

@router.post("/prompt/validate", response_model=ResponseModel[Dict[str, Any]])
async def validate_prompt_config(
    config_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """验证提示词配置"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    validation_result = await config_manager.validate_config(
        config_type="prompt",
        config_data=config_data
    )
    
    return ResponseModel.create_success(
        data=validation_result,
        message="验证提示词配置成功"
    )

@router.get("/prompt/options", response_model=ResponseModel[Dict[str, Any]])
async def get_prompt_config_options(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词配置选项和限制"""
    options = {
        "max_length": {
            "min": 100,
            "max": 100000,
            "default": 50000,
            "description": "提示词模板最大长度（字符）"
        },
        "max_variables": {
            "min": 1,
            "max": 100,
            "default": 50,
            "description": "模板最大变量数量"
        },
        "version_limit": {
            "min": 10,
            "max": 1000,
            "default": 100,
            "description": "版本历史保留数量"
        },
        "cache_ttl": {
            "min": 60,
            "max": 86400,
            "default": 3600,
            "description": "缓存过期时间（秒）"
        },
        "retention_days": {
            "min": 7,
            "max": 365,
            "default": 90,
            "description": "使用统计数据保留天数"
        },
        "suggestions_limit": {
            "min": 1,
            "max": 50,
            "default": 10,
            "description": "模板建议数量限制"
        },
        "batch_size": {
            "min": 1,
            "max": 1000,
            "default": 100,
            "description": "批处理大小"
        },
        "enable_analytics": {
            "type": "boolean",
            "default": True,
            "description": "是否启用使用统计"
        },
        "enable_auto_optimization": {
            "type": "boolean",
            "default": False,
            "description": "是否启用自动优化建议"
        }
    }
    
    return ResponseModel.create_success(
        data=options,
        message="获取提示词配置选项成功"
    )

@router.get("/prompt/stats", response_model=ResponseModel[Dict[str, Any]])
async def get_prompt_config_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词配置相关统计信息"""
    from app.services.prompt import PromptService
    from app.models.prompt import PromptTemplate, PromptUsageLog
    from sqlalchemy import select, func
    from datetime import datetime
    
    # 获取模板统计
    template_count_result = await db.execute(
        select(func.count(PromptTemplate.id)).filter(PromptTemplate.is_active == True)
    )
    template_count = template_count_result.scalar()
    
    # 获取使用统计
    usage_count_result = await db.execute(
        select(func.count(PromptUsageLog.id))
    )
    usage_count = usage_count_result.scalar()
    
    # 获取今日使用统计
    today = datetime.now().date()
    today_usage_result = await db.execute(
        select(func.count(PromptUsageLog.id)).filter(
            func.date(PromptUsageLog.created_at) == today
        )
    )
    today_usage = today_usage_result.scalar()
    
    stats = {
        "total_templates": template_count,
        "total_usage": usage_count,
        "today_usage": today_usage,
        "config_last_updated": datetime.now().isoformat(),
        "cache_status": "active"
    }
    
    return ResponseModel.create_success(
        data=stats,
        message="获取提示词配置统计成功"
    )

# ==================== RAG配置管理 ====================

@router.get("/rag", response_model=ResponseModel[Dict[str, Any]])
async def get_rag_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取RAG配置"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    config = await config_manager.get_rag_config()
    
    return ResponseModel.create_success(
        data=config,
        message="获取RAG配置成功"
    )

@router.put("/rag", response_model=ResponseModel[Dict[str, Any]])
async def update_rag_config(
    config_updates: Dict[str, Any],
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新RAG配置"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    updated_config = await config_manager.update_rag_config(
        config_updates=config_updates,
        user_id=current_admin.id
    )
    
    return ResponseModel.create_success(
        data=updated_config,
        message="更新RAG配置成功"
    )

@router.post("/rag/reset", response_model=ResponseModel[Dict[str, Any]])
async def reset_rag_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """重置RAG配置为默认值"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    reset_config = await config_manager.reset_rag_config(user_id=current_admin.id)
    
    return ResponseModel.create_success(
        data=reset_config,
        message="重置RAG配置成功"
    )

@router.post("/rag/validate", response_model=ResponseModel[Dict[str, Any]])
async def validate_rag_config(
    config_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """验证RAG配置"""
    from app.services.config_manager import ConfigManager
    config_manager = ConfigManager(db)
    validation_result = await config_manager.validate_config(
        config_type="rag",
        config_data=config_data
    )
    
    return ResponseModel.create_success(
        data=validation_result,
        message="验证RAG配置成功"
    )

@router.get("/rag/options", response_model=ResponseModel[Dict[str, Any]])
async def get_rag_config_options(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取RAG配置选项和限制"""
    options = {
        "chunk_size": {
            "min": 100,
            "max": 10000,
            "default": 1000,
            "description": "文本分块大小（字符）"
        },
        "chunk_overlap": {
            "min": 0,
            "max": 5000,
            "default": 200,
            "description": "文本分块重叠大小（字符）"
        },
        "vector_store_type": {
            "type": "enum",
            "options": ["chroma", "qdrant", "milvus", "pgvector"],
            "default": "chroma",
            "description": "向量存储类型"
        },
        "batch_size": {
            "min": 1,
            "max": 1000,
            "default": 100,
            "description": "批处理大小"
        },
        "retrieval_method": {
            "type": "enum",
            "options": ["semantic_search", "keyword_search", "hybrid_search"],
            "default": "hybrid_search",
            "description": "检索方法"
        },
        "use_rerank": {
            "type": "boolean",
            "default": True,
            "description": "是否使用重排序"
        },
        "rerank_model": {
            "type": "string",
            "default": "bge-reranker-base",
            "description": "重排序模型名称"
        }
    }
    
    return ResponseModel.create_success(
        data=options,
        message="获取RAG配置选项成功"
    )

@router.get("/rag/stats", response_model=ResponseModel[Dict[str, Any]])
async def get_rag_config_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取RAG配置相关统计信息"""
    from app.models.knowledge_base import KnowledgeBase
    from app.models.document import Document
    from sqlalchemy import select, func
    from datetime import datetime
    
    # 获取知识库统计
    kb_count_result = await db.execute(
        select(func.count(KnowledgeBase.id)).filter(KnowledgeBase.is_active == True)
    )
    kb_count = kb_count_result.scalar()
    
    # 获取文档统计
    doc_count_result = await db.execute(
        select(func.count(Document.id))
    )
    doc_count = doc_count_result.scalar()
    
    # 获取今日创建的知识库数量
    today = datetime.now().date()
    today_kb_result = await db.execute(
        select(func.count(KnowledgeBase.id)).filter(
            func.date(KnowledgeBase.created_at) == today
        )
    )
    today_kb_count = today_kb_result.scalar()
    
    stats = {
        "total_knowledge_bases": kb_count,
        "total_documents": doc_count,
        "today_knowledge_bases": today_kb_count,
        "config_last_updated": datetime.now().isoformat(),
        "cache_status": "active"
    }
    
    return ResponseModel.create_success(
        data=stats,
        message="获取RAG配置统计成功"
    )

# ==================== 系统配置管理 ====================

@router.post("/configs", response_model=ResponseModel[SystemConfigResponse])
async def create_config(
    config_data: SystemConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建系统配置"""
    config_service = ConfigService(db)
    config = await config_service.create_config(config_data)
    
    return ResponseModel.create_success(
        data=config,
        message="创建系统配置成功"
    )

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
    config_service = ConfigService(db)
    configs = await config_service.get_configs(
        skip=skip, limit=limit, category=category, 
        search=search, include_sensitive=include_sensitive
    )
    
    return ResponseModel.create_success(
        data=configs,
        message="获取系统配置列表成功"
    )

@router.get("/configs/{config_id}", response_model=ResponseModel[SystemConfigResponse])
async def get_config(
    config_id: int,
    include_sensitive: bool = Query(False, description="是否包含敏感信息"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个系统配置"""
    config_service = ConfigService(db)
    config = await config_service.get_config_by_key(str(config_id), include_sensitive)
    
    if not config:
        raise ResourceNotFoundException("配置", config_id)
    
    return ResponseModel.create_success(
        data=config,
        message="获取系统配置成功"
    )

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
