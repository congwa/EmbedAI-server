import io
import csv
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.services.analytics import AnalyticsService
from app.core.response import APIResponse, ResponseModel
from app.schemas.analytics import (
    SystemOverviewResponse, UserActivityStats, KnowledgeBaseStats,
    PerformanceMetrics, CostAnalysis, TimeSeriesData, AnalyticsQuery,
    DashboardData, ExportRequest
)
from app.models.user import User
from app.core.logger import Logger

router = APIRouter(tags=["admin-analytics"])

@router.get("/dashboard", response_model=ResponseModel[DashboardData])
async def get_dashboard_data(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仪表板数据
    
    返回管理员仪表板所需的所有关键指标和统计信息
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # 获取系统概览
        overview = await analytics_service.get_system_overview()
        
        # 获取最近用户活动
        recent_activities = await analytics_service.get_user_activity_stats(limit=10)
        
        # 获取热门知识库
        top_knowledge_bases = await analytics_service.get_knowledge_base_stats(limit=5)
        
        # 获取性能趋势数据(最近7天)
        performance_trends = await analytics_service.get_performance_trends(days=7)
        
        # 获取费用摘要
        cost_summary = await analytics_service.get_cost_analysis(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # 获取系统警告
        alerts = await analytics_service.get_system_alerts()
        
        dashboard_data = DashboardData(
            overview=overview,
            recent_activities=recent_activities,
            top_knowledge_bases=top_knowledge_bases,
            performance_trends=performance_trends,
            cost_summary=cost_summary,
            alerts=alerts
        )
        
        return APIResponse.success(data=dashboard_data)
        
    except Exception as e:
        Logger.error(f"获取仪表板数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取仪表板数据失败")

@router.get("/overview", response_model=ResponseModel[SystemOverviewResponse])
async def get_system_overview(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统概览统计"""
    try:
        analytics_service = AnalyticsService(db)
        overview = await analytics_service.get_system_overview()
        return APIResponse.success(data=overview)
        
    except Exception as e:
        Logger.error(f"获取系统概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统概览失败")

@router.get("/users/activity", response_model=ResponseModel[List[UserActivityStats]])
async def get_user_activity_stats(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户活动统计"""
    try:
        analytics_service = AnalyticsService(db)
        stats = await analytics_service.get_user_activity_stats(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        return APIResponse.success(data=stats)
        
    except Exception as e:
        Logger.error(f"获取用户活动统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户活动统计失败")

@router.get("/knowledge-bases/stats", response_model=ResponseModel[List[KnowledgeBaseStats]])
async def get_knowledge_base_stats(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库统计"""
    try:
        analytics_service = AnalyticsService(db)
        stats = await analytics_service.get_knowledge_base_stats(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        return APIResponse.success(data=stats)
        
    except Exception as e:
        Logger.error(f"获取知识库统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取知识库统计失败")

@router.get("/performance/metrics", response_model=ResponseModel[List[PerformanceMetrics]])
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="时间范围(小时)"),
    granularity: str = Query("hour", description="时间粒度: hour, day"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取性能指标"""
    try:
        analytics_service = AnalyticsService(db)
        metrics = await analytics_service.get_performance_metrics(
            hours=hours,
            granularity=granularity
        )
        return APIResponse.success(data=metrics)
        
    except Exception as e:
        Logger.error(f"获取性能指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取性能指标失败")

@router.get("/costs/analysis", response_model=ResponseModel[CostAnalysis])
async def get_cost_analysis(
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    kb_id: Optional[int] = Query(None, description="知识库ID"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取费用分析"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        analytics_service = AnalyticsService(db)
        analysis = await analytics_service.get_cost_analysis(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            kb_id=kb_id
        )
        return APIResponse.success(data=analysis)
        
    except Exception as e:
        Logger.error(f"获取费用分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取费用分析失败")

@router.post("/export")
async def export_analytics_data(
    export_request: ExportRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """导出分析数据"""
    try:
        analytics_service = AnalyticsService(db)
        
        # 根据报告类型获取数据
        if export_request.report_type == "overview":
            data = await analytics_service.get_system_overview()
        elif export_request.report_type == "users":
            data = await analytics_service.get_user_activity_stats()
        elif export_request.report_type == "knowledge_bases":
            data = await analytics_service.get_knowledge_base_stats()
        elif export_request.report_type == "costs":
            filters = export_request.filters or AnalyticsQuery()
            data = await analytics_service.get_cost_analysis(
                start_date=filters.start_date,
                end_date=filters.end_date,
                user_id=filters.user_id,
                kb_id=filters.kb_id
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的报告类型")
        
        # 根据格式导出数据
        if export_request.format == "csv":
            return await _export_csv(data, export_request.report_type)
        elif export_request.format == "json":
            return await _export_json(data, export_request.report_type)
        elif export_request.format == "pdf":
            return await _export_pdf(data, export_request.report_type, export_request.include_charts)
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except Exception as e:
        Logger.error(f"导出分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出分析数据失败")

async def _export_csv(data: Any, report_type: str) -> StreamingResponse:
    """导出CSV格式"""
    output = io.StringIO()
    
    if report_type == "overview":
        writer = csv.writer(output)
        writer.writerow(["指标", "数值"])
        for key, value in data.dict().items():
            writer.writerow([key, value])
    elif report_type == "users":
        writer = csv.DictWriter(output, fieldnames=data[0].dict().keys() if data else [])
        writer.writeheader()
        for item in data:
            writer.writerow(item.dict())
    elif report_type == "knowledge_bases":
        writer = csv.DictWriter(output, fieldnames=data[0].dict().keys() if data else [])
        writer.writeheader()
        for item in data:
            writer.writerow(item.dict())
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )

async def _export_json(data: Any, report_type: str) -> Response:
    """导出JSON格式"""
    if hasattr(data, 'dict'):
        json_data = data.dict()
    elif isinstance(data, list):
        json_data = [item.dict() if hasattr(item, 'dict') else item for item in data]
    else:
        json_data = data
    
    return Response(
        content=json.dumps(json_data, indent=2, default=str, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.json"}
    )

async def _export_pdf(data: Any, report_type: str, include_charts: bool = False) -> Response:
    """导出PDF格式"""
    # 这里需要实现PDF生成逻辑
    # 可以使用reportlab或其他PDF库
    # 暂时返回错误，提示需要实现
    raise HTTPException(status_code=501, detail="PDF导出功能正在开发中")
