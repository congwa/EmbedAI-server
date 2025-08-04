import asyncio
import json
import psutil
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from app.models.analytics import SystemMetrics, UserActivityLog, KnowledgeBaseMetrics, APIMetrics
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.llm_usage_log import LLMUsageLog
from app.schemas.analytics import (
    SystemOverviewResponse, UserActivityStats, KnowledgeBaseStats,
    PerformanceMetrics, CostAnalysis, TimeSeriesData, AnalyticsQuery,
    DashboardData
)
from app.core.logger import Logger
from app.core.redis_manager import redis_manager

class AnalyticsService:
    """分析服务
    
    提供系统分析、用户活动跟踪、性能监控等功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_system_overview(self) -> SystemOverviewResponse:
        """获取系统概览数据"""
        try:
            # 获取用户统计
            total_users_result = await self.db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar() or 0
            
            # 获取活跃用户数(最近7天有活动)
            seven_days_ago = datetime.now() - timedelta(days=7)
            active_users_result = await self.db.execute(
                select(func.count(func.distinct(UserActivityLog.user_id)))
                .where(UserActivityLog.timestamp >= seven_days_ago)
            )
            active_users = active_users_result.scalar() or 0
            
            # 获取知识库数量
            kb_count_result = await self.db.execute(select(func.count(KnowledgeBase.id)))
            knowledge_bases = kb_count_result.scalar() or 0
            
            # 获取文档总数
            doc_count_result = await self.db.execute(select(func.count(Document.id)))
            total_documents = doc_count_result.scalar() or 0
            
            # 获取查询总数
            query_count_result = await self.db.execute(
                select(func.sum(KnowledgeBaseMetrics.query_count))
            )
            total_queries = query_count_result.scalar() or 0
            
            # 获取系统运行时间(从Redis或配置中获取)
            system_uptime = await self._get_system_uptime()
            
            # 获取平均响应时间
            avg_response_result = await self.db.execute(
                select(func.avg(APIMetrics.response_time))
                .where(APIMetrics.timestamp >= seven_days_ago)
            )
            avg_response_time = avg_response_result.scalar() or 0.0
            
            # 计算成功率
            success_rate = await self._calculate_success_rate(seven_days_ago)
            
            # 获取总费用
            total_cost_result = await self.db.execute(
                select(func.sum(LLMUsageLog.cost))
            )
            total_cost = total_cost_result.scalar() or 0.0
            
            return SystemOverviewResponse(
                active_users=active_users,
                total_users=total_users,
                knowledge_bases=knowledge_bases,
                total_documents=total_documents,
                total_queries=total_queries,
                system_uptime=system_uptime,
                avg_response_time=avg_response_time,
                success_rate=success_rate,
                total_cost=total_cost
            )
            
        except Exception as e:
            Logger.error(f"获取系统概览失败: {str(e)}")
            raise
    
    async def get_user_activity_stats(
        self, 
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UserActivityStats]:
        """获取用户活动统计"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # 构建查询
            query = select(
                User.id,
                User.email,
                func.count(UserActivityLog.id).label('login_count'),
                func.max(UserActivityLog.timestamp).label('last_login'),
                func.avg(UserActivityLog.duration).label('avg_duration'),
                func.count(func.distinct(func.date(UserActivityLog.timestamp))).label('active_days')
            ).select_from(
                User
            ).outerjoin(
                UserActivityLog, 
                and_(
                    User.id == UserActivityLog.user_id,
                    UserActivityLog.timestamp.between(start_date, end_date),
                    UserActivityLog.activity_type == 'login'
                )
            ).group_by(User.id, User.email).limit(limit)
            
            result = await self.db.execute(query)
            users_data = result.fetchall()
            
            stats = []
            for user_data in users_data:
                # 获取用户查询数
                query_count_result = await self.db.execute(
                    select(func.count(LLMUsageLog.id))
                    .where(
                        and_(
                            LLMUsageLog.user_id == user_data.id,
                            LLMUsageLog.created_at.between(start_date, end_date)
                        )
                    )
                )
                total_queries = query_count_result.scalar() or 0
                
                stats.append(UserActivityStats(
                    user_id=user_data.id,
                    email=user_data.email,
                    login_count=user_data.login_count or 0,
                    last_login=user_data.last_login,
                    session_duration_avg=(user_data.avg_duration or 0) / 60,  # 转换为分钟
                    total_queries=total_queries,
                    active_days=user_data.active_days or 0
                ))
            
            return stats
            
        except Exception as e:
            Logger.error(f"获取用户活动统计失败: {str(e)}")
            raise
    
    async def get_knowledge_base_stats(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[KnowledgeBaseStats]:
        """获取知识库统计"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # 获取知识库基本信息和指标
            query = select(
                KnowledgeBase.id,
                KnowledgeBase.name,
                func.sum(KnowledgeBaseMetrics.query_count).label('total_queries'),
                func.sum(KnowledgeBaseMetrics.success_count).label('total_success'),
                func.avg(KnowledgeBaseMetrics.avg_response_time).label('avg_response_time'),
                func.sum(KnowledgeBaseMetrics.total_cost).label('total_cost'),
                func.sum(KnowledgeBaseMetrics.unique_users).label('unique_users')
            ).select_from(
                KnowledgeBase
            ).outerjoin(
                KnowledgeBaseMetrics,
                and_(
                    KnowledgeBase.id == KnowledgeBaseMetrics.knowledge_base_id,
                    KnowledgeBaseMetrics.metric_date.between(start_date, end_date)
                )
            ).group_by(
                KnowledgeBase.id, KnowledgeBase.name
            ).order_by(
                desc('total_queries')
            ).limit(limit)
            
            result = await self.db.execute(query)
            kb_data = result.fetchall()
            
            stats = []
            for kb in kb_data:
                # 获取文档数量
                doc_count_result = await self.db.execute(
                    select(func.count(Document.id))
                    .where(Document.knowledge_base_id == kb.id)
                )
                documents_count = doc_count_result.scalar() or 0
                
                # 计算成功率
                total_queries = kb.total_queries or 0
                total_success = kb.total_success or 0
                success_rate = (total_success / total_queries * 100) if total_queries > 0 else 0
                
                stats.append(KnowledgeBaseStats(
                    kb_id=kb.id,
                    kb_name=kb.name,
                    query_count=total_queries,
                    success_rate=success_rate,
                    avg_response_time=kb.avg_response_time or 0.0,
                    total_cost=kb.total_cost or 0.0,
                    unique_users=kb.unique_users or 0,
                    documents_count=documents_count
                ))
            
            return stats
            
        except Exception as e:
            Logger.error(f"获取知识库统计失败: {str(e)}")
            raise
    
    async def record_system_metrics(self, metrics: Dict[str, Any]) -> None:
        """记录系统指标"""
        try:
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, dict):
                    # 复杂指标，存储为JSON
                    system_metric = SystemMetrics(
                        metric_type="system",
                        metric_name=metric_name,
                        metric_value=0.0,  # 复杂指标值设为0
                        metadata=metric_value
                    )
                else:
                    # 简单数值指标
                    system_metric = SystemMetrics(
                        metric_type="system",
                        metric_name=metric_name,
                        metric_value=float(metric_value)
                    )
                
                self.db.add(system_metric)
            
            await self.db.commit()
            Logger.debug(f"系统指标记录成功: {list(metrics.keys())}")
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"记录系统指标失败: {str(e)}")
            raise
    
    async def record_user_activity(
        self,
        user_id: int,
        activity_type: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration: Optional[int] = None
    ) -> None:
        """记录用户活动"""
        try:
            activity_log = UserActivityLog(
                user_id=user_id,
                session_id=session_id,
                activity_type=activity_type,
                activity_details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                duration=duration
            )
            
            self.db.add(activity_log)
            await self.db.commit()
            
            Logger.debug(f"用户活动记录成功: user_id={user_id}, type={activity_type}")
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"记录用户活动失败: {str(e)}")
            raise
    
    async def _get_system_uptime(self) -> float:
        """获取系统运行时间"""
        try:
            # 尝试从Redis获取启动时间
            start_time_str = await redis_manager.get("system:start_time")
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                uptime_seconds = (datetime.now() - start_time).total_seconds()
                return uptime_seconds / 3600  # 转换为小时
            else:
                # 如果Redis中没有，使用系统启动时间
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime_seconds = (datetime.now() - boot_time).total_seconds()
                return uptime_seconds / 3600
        except Exception:
            return 0.0
    
    async def _calculate_success_rate(self, start_date: datetime) -> float:
        """计算成功率"""
        try:
            total_requests_result = await self.db.execute(
                select(func.count(APIMetrics.id))
                .where(APIMetrics.timestamp >= start_date)
            )
            total_requests = total_requests_result.scalar() or 0

            if total_requests == 0:
                return 100.0

            success_requests_result = await self.db.execute(
                select(func.count(APIMetrics.id))
                .where(
                    and_(
                        APIMetrics.timestamp >= start_date,
                        APIMetrics.status_code < 400
                    )
                )
            )
            success_requests = success_requests_result.scalar() or 0

            return (success_requests / total_requests) * 100

        except Exception:
            return 0.0

    async def get_performance_trends(self, days: int = 7) -> List[TimeSeriesData]:
        """获取性能趋势数据"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            # 获取每日平均响应时间
            query = select(
                func.date(APIMetrics.timestamp).label('date'),
                func.avg(APIMetrics.response_time).label('avg_response_time')
            ).where(
                APIMetrics.timestamp >= start_date
            ).group_by(
                func.date(APIMetrics.timestamp)
            ).order_by('date')

            result = await self.db.execute(query)
            trends_data = result.fetchall()

            trends = []
            for trend in trends_data:
                trends.append(TimeSeriesData(
                    timestamp=datetime.combine(trend.date, datetime.min.time()),
                    value=trend.avg_response_time or 0.0,
                    metadata={"metric": "avg_response_time", "unit": "seconds"}
                ))

            return trends

        except Exception as e:
            Logger.error(f"获取性能趋势失败: {str(e)}")
            return []

    async def get_cost_analysis(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None
    ) -> CostAnalysis:
        """获取费用分析"""
        try:
            # 构建基础查询条件
            conditions = [
                LLMUsageLog.created_at.between(start_date, end_date)
            ]

            if user_id:
                conditions.append(LLMUsageLog.user_id == user_id)
            if kb_id:
                conditions.append(LLMUsageLog.knowledge_base_id == kb_id)

            # 获取总费用
            total_cost_result = await self.db.execute(
                select(func.sum(LLMUsageLog.cost))
                .where(and_(*conditions))
            )
            total_cost = total_cost_result.scalar() or 0.0

            # 获取模型费用分解
            model_breakdown_result = await self.db.execute(
                select(
                    LLMUsageLog.model_name,
                    func.sum(LLMUsageLog.cost).label('model_cost')
                ).where(and_(*conditions))
                .group_by(LLMUsageLog.model_name)
            )
            model_breakdown = {
                row.model_name: row.model_cost
                for row in model_breakdown_result.fetchall()
            }

            # 获取每日费用
            daily_costs_result = await self.db.execute(
                select(
                    func.date(LLMUsageLog.created_at).label('date'),
                    func.sum(LLMUsageLog.cost).label('daily_cost')
                ).where(and_(*conditions))
                .group_by(func.date(LLMUsageLog.created_at))
                .order_by('date')
            )

            daily_costs = []
            for row in daily_costs_result.fetchall():
                daily_costs.append({
                    "date": row.date.isoformat(),
                    "cost": row.daily_cost
                })

            return CostAnalysis(
                user_id=user_id,
                kb_id=kb_id,
                period_start=start_date,
                period_end=end_date,
                total_cost=total_cost,
                token_cost=total_cost,  # 目前所有费用都是token费用
                model_breakdown=model_breakdown,
                daily_costs=daily_costs
            )

        except Exception as e:
            Logger.error(f"获取费用分析失败: {str(e)}")
            raise

    async def get_performance_metrics(
        self,
        hours: int = 24,
        granularity: str = "hour"
    ) -> List[PerformanceMetrics]:
        """获取性能指标"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)

            # 根据粒度确定时间分组函数
            if granularity == "hour":
                time_group = func.date_trunc('hour', SystemMetrics.timestamp)
            else:  # day
                time_group = func.date_trunc('day', SystemMetrics.timestamp)

            # 获取系统指标
            query = select(
                time_group.label('time_period'),
                func.avg(
                    func.case(
                        (SystemMetrics.metric_name == 'cpu_usage', SystemMetrics.metric_value),
                        else_=None
                    )
                ).label('cpu_usage'),
                func.avg(
                    func.case(
                        (SystemMetrics.metric_name == 'memory_usage', SystemMetrics.metric_value),
                        else_=None
                    )
                ).label('memory_usage'),
                func.avg(
                    func.case(
                        (SystemMetrics.metric_name == 'disk_usage', SystemMetrics.metric_value),
                        else_=None
                    )
                ).label('disk_usage')
            ).where(
                and_(
                    SystemMetrics.timestamp >= start_time,
                    SystemMetrics.metric_type == 'system'
                )
            ).group_by(time_group).order_by(time_group)

            result = await self.db.execute(query)
            metrics_data = result.fetchall()

            # 获取API指标
            api_query = select(
                time_group.label('time_period'),
                func.avg(APIMetrics.response_time).label('avg_response_time'),
                func.count(APIMetrics.id).label('total_requests'),
                func.sum(
                    func.case(
                        (APIMetrics.status_code >= 400, 1),
                        else_=0
                    )
                ).label('error_count')
            ).where(
                APIMetrics.timestamp >= start_time
            ).group_by(time_group).order_by(time_group)

            api_result = await self.db.execute(api_query)
            api_data = {row.time_period: row for row in api_result.fetchall()}

            metrics = []
            for row in metrics_data:
                api_row = api_data.get(row.time_period)

                # 计算错误率和吞吐量
                total_requests = api_row.total_requests if api_row else 0
                error_count = api_row.error_count if api_row else 0
                error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

                # 计算吞吐量(请求/秒)
                time_window_seconds = 3600 if granularity == "hour" else 86400
                throughput = total_requests / time_window_seconds if total_requests > 0 else 0

                metrics.append(PerformanceMetrics(
                    timestamp=row.time_period,
                    cpu_usage=row.cpu_usage or 0.0,
                    memory_usage=row.memory_usage or 0.0,
                    disk_usage=row.disk_usage or 0.0,
                    api_response_time=api_row.avg_response_time if api_row else 0.0,
                    error_rate=error_rate,
                    throughput=throughput
                ))

            return metrics

        except Exception as e:
            Logger.error(f"获取性能指标失败: {str(e)}")
            return []

    async def get_system_alerts(self) -> List[Dict[str, Any]]:
        """获取系统警告"""
        try:
            alerts = []

            # 检查高错误率
            one_hour_ago = datetime.now() - timedelta(hours=1)
            error_rate_result = await self.db.execute(
                select(
                    func.count(APIMetrics.id).label('total'),
                    func.sum(
                        func.case(
                            (APIMetrics.status_code >= 400, 1),
                            else_=0
                        )
                    ).label('errors')
                ).where(APIMetrics.timestamp >= one_hour_ago)
            )

            error_data = error_rate_result.first()
            if error_data and error_data.total > 0:
                error_rate = (error_data.errors / error_data.total) * 100
                if error_rate > 5:  # 错误率超过5%
                    alerts.append({
                        "type": "error_rate",
                        "level": "warning" if error_rate < 10 else "critical",
                        "message": f"API错误率过高: {error_rate:.1f}%",
                        "timestamp": datetime.now().isoformat()
                    })

            # 检查响应时间
            avg_response_result = await self.db.execute(
                select(func.avg(APIMetrics.response_time))
                .where(APIMetrics.timestamp >= one_hour_ago)
            )
            avg_response = avg_response_result.scalar()
            if avg_response and avg_response > 2.0:  # 响应时间超过2秒
                alerts.append({
                    "type": "response_time",
                    "level": "warning" if avg_response < 5.0 else "critical",
                    "message": f"API响应时间过长: {avg_response:.2f}秒",
                    "timestamp": datetime.now().isoformat()
                })

            return alerts

        except Exception as e:
            Logger.error(f"获取系统警告失败: {str(e)}")
            return []
