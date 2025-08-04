from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.services.health_monitor import HealthMonitorService
from app.core.response import APIResponse, ResponseModel
from app.schemas.health import (
    SystemHealthOverview, ServiceHealthResponse, SystemAlertResponse,
    SystemResourceMetrics, HealthDashboardData, SystemAlertCreate,
    SystemAlertResolve, PerformanceThresholdResponse, PerformanceThresholdCreate,
    PerformanceThresholdUpdate, HealthCheckConfigResponse, HealthCheckConfigCreate,
    HealthCheckConfigUpdate, UptimeRecordResponse, AlertQuery
)
from app.models.health import SystemAlert, PerformanceThreshold, HealthCheckConfig, UptimeRecord
from app.models.user import User
from app.core.logger import Logger

router = APIRouter(tags=["admin-health"])

@router.get("/dashboard", response_model=ResponseModel[HealthDashboardData])
async def get_health_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取健康监控仪表板数据"""
    try:
        health_service = HealthMonitorService(db)
        
        # 获取系统健康概览
        overview = await health_service.get_system_health_overview()
        
        # 获取服务健康状态
        services = await health_service.get_service_health_status(limit=20)
        
        # 获取最近警告
        recent_alerts_result = await db.execute(
            select(SystemAlert)
            .where(SystemAlert.created_at >= datetime.now() - timedelta(hours=24))
            .order_by(desc(SystemAlert.created_at))
            .limit(10)
        )
        recent_alerts_data = recent_alerts_result.scalars().all()
        
        recent_alerts = [
            SystemAlertResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                level=alert.level,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                metadata=alert.alert_metadata,
                is_resolved=alert.is_resolved,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                created_at=alert.created_at
            ) for alert in recent_alerts_data
        ]
        
        # 获取系统资源指标
        system_resources = await health_service.get_system_resource_metrics()
        
        # 获取运行时间趋势（最近7天）
        start_date = datetime.now() - timedelta(days=7)
        uptime_result = await db.execute(
            select(UptimeRecord)
            .where(UptimeRecord.date >= start_date)
            .order_by(desc(UptimeRecord.date))
            .limit(7)
        )
        uptime_data = uptime_result.scalars().all()
        
        uptime_trends = [
            UptimeRecordResponse(
                service_name=record.service_name,
                date=record.date,
                total_checks=record.total_checks,
                successful_checks=record.successful_checks,
                failed_checks=record.failed_checks,
                uptime_percentage=record.uptime_percentage,
                avg_response_time=record.avg_response_time,
                max_response_time=record.max_response_time,
                min_response_time=record.min_response_time,
                downtime_duration=record.downtime_duration
            ) for record in uptime_data
        ]
        
        dashboard_data = HealthDashboardData(
            overview=overview,
            services=services,
            recent_alerts=recent_alerts,
            system_resources=system_resources,
            uptime_trends=uptime_trends
        )
        
        return APIResponse.success(data=dashboard_data)
        
    except Exception as e:
        Logger.error(f"获取健康监控仪表板失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取健康监控仪表板失败")

@router.get("/overview", response_model=ResponseModel[SystemHealthOverview])
async def get_system_health_overview(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统健康概览"""
    try:
        health_service = HealthMonitorService(db)
        overview = await health_service.get_system_health_overview()
        return APIResponse.success(data=overview)
        
    except Exception as e:
        Logger.error(f"获取系统健康概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统健康概览失败")

@router.get("/services", response_model=ResponseModel[List[ServiceHealthResponse]])
async def get_service_health_status(
    service_name: Optional[str] = Query(None, description="服务名称"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务健康状态"""
    try:
        health_service = HealthMonitorService(db)
        services = await health_service.get_service_health_status(
            service_name=service_name,
            limit=limit
        )
        return APIResponse.success(data=services)
        
    except Exception as e:
        Logger.error(f"获取服务健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取服务健康状态失败")

@router.post("/services/{service_name}/check", response_model=ResponseModel[ServiceHealthResponse])
async def perform_health_check(
    service_name: str,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """执行单个服务的健康检查"""
    try:
        health_service = HealthMonitorService(db)
        result = await health_service.perform_health_check(service_name)
        return APIResponse.success(data=result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        Logger.error(f"执行健康检查失败: {service_name} - {str(e)}")
        raise HTTPException(status_code=500, detail="执行健康检查失败")

@router.get("/resources", response_model=ResponseModel[SystemResourceMetrics])
async def get_system_resources(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统资源指标"""
    try:
        health_service = HealthMonitorService(db)
        resources = await health_service.get_system_resource_metrics()
        return APIResponse.success(data=resources)
        
    except Exception as e:
        Logger.error(f"获取系统资源指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统资源指标失败")

@router.get("/alerts", response_model=ResponseModel[List[SystemAlertResponse]])
async def get_system_alerts(
    level: Optional[str] = Query(None, description="警告级别"),
    alert_type: Optional[str] = Query(None, description="警告类型"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统警告列表"""
    try:
        # 构建查询条件
        conditions = []
        
        if level:
            conditions.append(SystemAlert.level == level)
        if alert_type:
            conditions.append(SystemAlert.alert_type == alert_type)
        if is_resolved is not None:
            conditions.append(SystemAlert.is_resolved == is_resolved)
        if start_date:
            conditions.append(SystemAlert.created_at >= start_date)
        if end_date:
            conditions.append(SystemAlert.created_at <= end_date)
        
        # 执行查询
        query = select(SystemAlert).order_by(desc(SystemAlert.created_at)).limit(limit)
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query)
        alerts_data = result.scalars().all()
        
        alerts = [
            SystemAlertResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                level=alert.level,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                metadata=alert.alert_metadata,
                is_resolved=alert.is_resolved,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                created_at=alert.created_at
            ) for alert in alerts_data
        ]
        
        return APIResponse.success(data=alerts)
        
    except Exception as e:
        Logger.error(f"获取系统警告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统警告失败")

@router.post("/alerts", response_model=ResponseModel[SystemAlertResponse])
async def create_system_alert(
    alert_data: SystemAlertCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建系统警告"""
    try:
        health_service = HealthMonitorService(db)
        alert = await health_service.create_alert(alert_data)
        return APIResponse.success(data=alert)
        
    except Exception as e:
        Logger.error(f"创建系统警告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建系统警告失败")

@router.put("/alerts/{alert_id}/resolve", response_model=ResponseModel[SystemAlertResponse])
async def resolve_system_alert(
    alert_id: int,
    resolve_data: SystemAlertResolve,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """解决系统警告"""
    try:
        # 获取警告
        result = await db.execute(
            select(SystemAlert).where(SystemAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, detail="警告不存在")
        
        if alert.is_resolved:
            raise HTTPException(status_code=400, detail="警告已经被解决")
        
        # 更新警告状态
        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        alert.resolved_by = resolve_data.resolved_by
        
        if resolve_data.resolution_note:
            if not alert.alert_metadata:
                alert.alert_metadata = {}
            alert.alert_metadata["resolution_note"] = resolve_data.resolution_note
        
        await db.commit()
        await db.refresh(alert)
        
        alert_response = SystemAlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            level=alert.level,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            metadata=alert.alert_metadata,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by,
            created_at=alert.created_at
        )
        
        return APIResponse.success(data=alert_response)
        
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"解决系统警告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="解决系统警告失败")
