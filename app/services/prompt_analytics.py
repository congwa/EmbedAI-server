from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, text
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import json
from collections import defaultdict

from app.models.prompt import PromptTemplate, PromptUsageLog, PromptVersion
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.schemas.prompt import PromptUsageStats, PromptUsageLogResponse
from app.core.logger import Logger


class PromptAnalyticsService:
    """提示词分析服务类
    
    处理提示词使用统计和性能分析相关的业务逻辑
    包括使用统计、性能分析、趋势分析等功能
    """
    
    def __init__(self, db: AsyncSession):
        """初始化分析服务
        
        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db
    
    async def log_usage(
        self,
        template_id: int,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        query: Optional[str] = None,
        variables_used: Optional[Dict[str, Any]] = None,
        rendered_content: Optional[str] = None,
        response_quality: Optional[float] = None,
        execution_time: Optional[float] = None,
        token_count: Optional[int] = None,
        cost: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        version_id: Optional[int] = None
    ) -> PromptUsageLog:
        """记录提示词使用情况
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
            kb_id: 知识库ID
            query: 查询内容
            variables_used: 使用的变量
            rendered_content: 渲染后的内容
            response_quality: 响应质量评分（0-1）
            execution_time: 执行时间（秒）
            token_count: token数量
            cost: 使用成本（美元）
            success: 是否成功
            error_message: 错误信息
            version_id: 版本ID
            
        Returns:
            PromptUsageLog: 使用日志记录
            
        Raises:
            HTTPException: 当记录失败时
        """
        try:
            Logger.info(f"记录提示词使用: template_id={template_id}, user_id={user_id}")
            
            # 验证模板是否存在
            template_result = await self.db.execute(
                select(PromptTemplate).filter(
                    and_(
                        PromptTemplate.id == template_id,
                        PromptTemplate.is_active == True
                    )
                )
            )
            template = template_result.scalar_one_or_none()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="提示词模板不存在"
                )
            
            # 创建使用日志
            usage_log = PromptUsageLog(
                template_id=template_id,
                version_id=version_id,
                user_id=user_id,
                kb_id=kb_id,
                query=query,
                variables_used=variables_used or {},
                rendered_content=rendered_content,
                response_quality=response_quality,
                execution_time=execution_time,
                token_count=token_count,
                cost=cost,
                success=success,
                error_message=error_message
            )
            
            self.db.add(usage_log)
            
            # 更新模板使用统计
            template.usage_count += 1
            template.last_used_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(usage_log)
            
            Logger.info(f"提示词使用记录成功: log_id={usage_log.id}")
            return usage_log
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"记录提示词使用失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"记录使用情况失败: {str(e)}"
            )
    
    async def get_usage_stats(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_trend: bool = True
    ) -> List[PromptUsageStats]:
        """获取使用统计数据
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            start_date: 开始日期
            end_date: 结束日期
            include_trend: 是否包含趋势数据
            
        Returns:
            List[PromptUsageStats]: 使用统计列表
        """
        try:
            Logger.info(f"获取使用统计: template_id={template_id}, user_id={user_id}")
            
            # 构建查询条件
            conditions = []
            
            if template_id:
                conditions.append(PromptUsageLog.template_id == template_id)
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            if kb_id:
                conditions.append(PromptUsageLog.kb_id == kb_id)
            
            if start_date:
                conditions.append(PromptUsageLog.created_at >= start_date)
            
            if end_date:
                conditions.append(PromptUsageLog.created_at <= end_date)
            
            # 查询统计数据
            stats_query = select(
                PromptUsageLog.template_id,
                PromptTemplate.name.label('template_name'),
                func.count(PromptUsageLog.id).label('total_usage'),
                func.avg(
                    func.case(
                        (PromptUsageLog.success == True, 1.0),
                        else_=0.0
                    )
                ).label('success_rate'),
                func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.sum(PromptUsageLog.cost).label('total_cost'),
                func.max(PromptUsageLog.created_at).label('last_used_at')
            ).select_from(
                PromptUsageLog.__table__.join(
                    PromptTemplate.__table__,
                    PromptUsageLog.template_id == PromptTemplate.id
                )
            ).filter(
                and_(*conditions) if conditions else True
            ).group_by(
                PromptUsageLog.template_id,
                PromptTemplate.name
            ).order_by(
                desc('total_usage')
            )
            
            result = await self.db.execute(stats_query)
            stats_data = result.fetchall()
            
            # 构建统计结果
            stats_list = []
            for row in stats_data:
                stats = PromptUsageStats(
                    template_id=row.template_id,
                    template_name=row.template_name,
                    total_usage=row.total_usage,
                    success_rate=float(row.success_rate or 0),
                    avg_execution_time=float(row.avg_execution_time) if row.avg_execution_time else None,
                    avg_response_quality=float(row.avg_response_quality) if row.avg_response_quality else None,
                    total_cost=float(row.total_cost) if row.total_cost else None,
                    last_used_at=row.last_used_at,
                    usage_trend=[]
                )
                
                # 获取趋势数据
                if include_trend:
                    trend_data = await self._get_usage_trend(
                        row.template_id, 
                        start_date, 
                        end_date,
                        user_id,
                        kb_id
                    )
                    stats.usage_trend = trend_data
                
                stats_list.append(stats)
            
            Logger.info(f"获取使用统计成功: 共{len(stats_list)}条记录")
            return stats_list
            
        except Exception as e:
            Logger.error(f"获取使用统计失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取使用统计失败: {str(e)}"
            )
    
    async def get_usage_logs(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[PromptUsageLogResponse], int]:
        """获取使用日志列表
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            start_date: 开始日期
            end_date: 结束日期
            success_only: 只显示成功的记录
            page: 页码
            page_size: 每页大小
            
        Returns:
            Tuple[List[PromptUsageLogResponse], int]: 日志列表和总数
        """
        try:
            # 构建查询条件
            conditions = []
            
            if template_id:
                conditions.append(PromptUsageLog.template_id == template_id)
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            if kb_id:
                conditions.append(PromptUsageLog.kb_id == kb_id)
            
            if start_date:
                conditions.append(PromptUsageLog.created_at >= start_date)
            
            if end_date:
                conditions.append(PromptUsageLog.created_at <= end_date)
            
            if success_only is not None:
                conditions.append(PromptUsageLog.success == success_only)
            
            # 查询总数
            count_result = await self.db.execute(
                select(func.count(PromptUsageLog.id)).filter(
                    and_(*conditions) if conditions else True
                )
            )
            total = count_result.scalar()
            
            # 查询数据
            offset = (page - 1) * page_size
            result = await self.db.execute(
                select(PromptUsageLog)
                .options(
                    selectinload(PromptUsageLog.template),
                    selectinload(PromptUsageLog.version),
                    selectinload(PromptUsageLog.user),
                    selectinload(PromptUsageLog.knowledge_base)
                )
                .filter(and_(*conditions) if conditions else True)
                .order_by(desc(PromptUsageLog.created_at))
                .offset(offset)
                .limit(page_size)
            )
            logs = result.scalars().all()
            
            # 转换为响应格式
            log_responses = []
            for log in logs:
                log_response = PromptUsageLogResponse(
                    id=log.id,
                    template_id=log.template_id,
                    version_id=log.version_id,
                    user_id=log.user_id,
                    kb_id=log.kb_id,
                    query=log.query,
                    variables_used=log.variables_used or {},
                    response_quality=log.response_quality,
                    execution_time=log.execution_time,
                    token_count=log.token_count,
                    cost=log.cost,
                    success=log.success,
                    error_message=log.error_message,
                    created_at=log.created_at,
                    template_name=log.template.name if log.template else None,
                    version_number=log.version.version_number if log.version else None,
                    user_email=log.user.email if log.user else None,
                    kb_name=log.knowledge_base.name if log.knowledge_base else None
                )
                log_responses.append(log_response)
            
            return log_responses, total
            
        except Exception as e:
            Logger.error(f"获取使用日志失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取使用日志失败: {str(e)}"
            )  
  
    async def _get_usage_trend(
        self,
        template_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取使用趋势数据
        
        Args:
            template_id: 模板ID
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            days: 默认天数
            
        Returns:
            List[Dict[str, Any]]: 趋势数据列表
        """
        try:
            # 设置默认时间范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                PromptUsageLog.template_id == template_id,
                PromptUsageLog.created_at >= start_date,
                PromptUsageLog.created_at <= end_date
            ]
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            if kb_id:
                conditions.append(PromptUsageLog.kb_id == kb_id)
            
            # 按日期分组统计
            trend_query = select(
                func.date(PromptUsageLog.created_at).label('date'),
                func.count(PromptUsageLog.id).label('usage_count'),
                func.avg(
                    func.case(
                        (PromptUsageLog.success == True, 1.0),
                        else_=0.0
                    )
                ).label('success_rate'),
                func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.sum(PromptUsageLog.cost).label('daily_cost')
            ).filter(
                and_(*conditions)
            ).group_by(
                func.date(PromptUsageLog.created_at)
            ).order_by(
                func.date(PromptUsageLog.created_at)
            )
            
            result = await self.db.execute(trend_query)
            trend_data = result.fetchall()
            
            # 转换为趋势数据格式
            trend_list = []
            for row in trend_data:
                trend_item = {
                    "date": row.date.isoformat() if row.date else None,
                    "usage_count": row.usage_count,
                    "success_rate": float(row.success_rate or 0),
                    "avg_execution_time": float(row.avg_execution_time) if row.avg_execution_time else None,
                    "avg_response_quality": float(row.avg_response_quality) if row.avg_response_quality else None,
                    "daily_cost": float(row.daily_cost) if row.daily_cost else None
                }
                trend_list.append(trend_item)
            
            return trend_list
            
        except Exception as e:
            Logger.error(f"获取使用趋势失败: {str(e)}")
            return []
    
    async def get_template_performance_summary(
        self,
        template_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取模板性能摘要
        
        Args:
            template_id: 模板ID
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 性能摘要数据
        """
        try:
            Logger.info(f"获取模板性能摘要: template_id={template_id}")
            
            # 设置时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 查询基础统计
            stats_query = select(
                func.count(PromptUsageLog.id).label('total_usage'),
                func.count(func.case((PromptUsageLog.success == True, 1))).label('success_count'),
                func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                func.min(PromptUsageLog.execution_time).label('min_execution_time'),
                func.max(PromptUsageLog.execution_time).label('max_execution_time'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.sum(PromptUsageLog.cost).label('total_cost'),
                func.sum(PromptUsageLog.token_count).label('total_tokens')
            ).filter(
                and_(
                    PromptUsageLog.template_id == template_id,
                    PromptUsageLog.created_at >= start_date,
                    PromptUsageLog.created_at <= end_date
                )
            )
            
            result = await self.db.execute(stats_query)
            stats = result.fetchone()
            
            if not stats or stats.total_usage == 0:
                return {
                    "template_id": template_id,
                    "period_days": days,
                    "total_usage": 0,
                    "success_rate": 0.0,
                    "avg_execution_time": None,
                    "min_execution_time": None,
                    "max_execution_time": None,
                    "avg_response_quality": None,
                    "total_cost": None,
                    "total_tokens": None,
                    "daily_average_usage": 0.0,
                    "error_rate": 0.0
                }
            
            # 计算衍生指标
            success_rate = float(stats.success_count) / float(stats.total_usage) if stats.total_usage > 0 else 0.0
            error_rate = 1.0 - success_rate
            daily_average_usage = float(stats.total_usage) / float(days)
            
            return {
                "template_id": template_id,
                "period_days": days,
                "total_usage": stats.total_usage,
                "success_rate": success_rate,
                "error_rate": error_rate,
                "avg_execution_time": float(stats.avg_execution_time) if stats.avg_execution_time else None,
                "min_execution_time": float(stats.min_execution_time) if stats.min_execution_time else None,
                "max_execution_time": float(stats.max_execution_time) if stats.max_execution_time else None,
                "avg_response_quality": float(stats.avg_response_quality) if stats.avg_response_quality else None,
                "total_cost": float(stats.total_cost) if stats.total_cost else None,
                "total_tokens": stats.total_tokens,
                "daily_average_usage": daily_average_usage
            }
            
        except Exception as e:
            Logger.error(f"获取模板性能摘要失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取性能摘要失败: {str(e)}"
            )
    
    async def get_top_templates_by_usage(
        self,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取使用量最高的模板排行
        
        Args:
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            days: 统计天数
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 模板排行列表
        """
        try:
            Logger.info(f"获取热门模板排行: user_id={user_id}, days={days}")
            
            # 设置时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                PromptUsageLog.created_at >= start_date,
                PromptUsageLog.created_at <= end_date
            ]
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            if kb_id:
                conditions.append(PromptUsageLog.kb_id == kb_id)
            
            # 查询热门模板
            top_query = select(
                PromptUsageLog.template_id,
                PromptTemplate.name.label('template_name'),
                func.count(PromptUsageLog.id).label('usage_count'),
                func.avg(
                    func.case(
                        (PromptUsageLog.success == True, 1.0),
                        else_=0.0
                    )
                ).label('success_rate'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.sum(PromptUsageLog.cost).label('total_cost')
            ).select_from(
                PromptUsageLog.__table__.join(
                    PromptTemplate.__table__,
                    PromptUsageLog.template_id == PromptTemplate.id
                )
            ).filter(
                and_(*conditions)
            ).group_by(
                PromptUsageLog.template_id,
                PromptTemplate.name
            ).order_by(
                desc('usage_count')
            ).limit(limit)
            
            result = await self.db.execute(top_query)
            top_data = result.fetchall()
            
            # 转换为排行数据
            ranking_list = []
            for index, row in enumerate(top_data, 1):
                ranking_item = {
                    "rank": index,
                    "template_id": row.template_id,
                    "template_name": row.template_name,
                    "usage_count": row.usage_count,
                    "success_rate": float(row.success_rate or 0),
                    "avg_response_quality": float(row.avg_response_quality) if row.avg_response_quality else None,
                    "total_cost": float(row.total_cost) if row.total_cost else None
                }
                ranking_list.append(ranking_item)
            
            Logger.info(f"获取热门模板排行成功: 共{len(ranking_list)}条记录")
            return ranking_list
            
        except Exception as e:
            Logger.error(f"获取热门模板排行失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取热门模板排行失败: {str(e)}"
            )
    
    async def get_user_usage_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取用户使用摘要
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 用户使用摘要
        """
        try:
            Logger.info(f"获取用户使用摘要: user_id={user_id}")
            
            # 设置时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 查询用户统计
            user_stats_query = select(
                func.count(PromptUsageLog.id).label('total_usage'),
                func.count(func.distinct(PromptUsageLog.template_id)).label('unique_templates'),
                func.count(func.case((PromptUsageLog.success == True, 1))).label('success_count'),
                func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.sum(PromptUsageLog.cost).label('total_cost'),
                func.sum(PromptUsageLog.token_count).label('total_tokens')
            ).filter(
                and_(
                    PromptUsageLog.user_id == user_id,
                    PromptUsageLog.created_at >= start_date,
                    PromptUsageLog.created_at <= end_date
                )
            )
            
            result = await self.db.execute(user_stats_query)
            stats = result.fetchone()
            
            if not stats or stats.total_usage == 0:
                return {
                    "user_id": user_id,
                    "period_days": days,
                    "total_usage": 0,
                    "unique_templates": 0,
                    "success_rate": 0.0,
                    "avg_execution_time": None,
                    "avg_response_quality": None,
                    "total_cost": None,
                    "total_tokens": None,
                    "daily_average_usage": 0.0
                }
            
            # 计算衍生指标
            success_rate = float(stats.success_count) / float(stats.total_usage) if stats.total_usage > 0 else 0.0
            daily_average_usage = float(stats.total_usage) / float(days)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_usage": stats.total_usage,
                "unique_templates": stats.unique_templates,
                "success_rate": success_rate,
                "avg_execution_time": float(stats.avg_execution_time) if stats.avg_execution_time else None,
                "avg_response_quality": float(stats.avg_response_quality) if stats.avg_response_quality else None,
                "total_cost": float(stats.total_cost) if stats.total_cost else None,
                "total_tokens": stats.total_tokens,
                "daily_average_usage": daily_average_usage
            }
            
        except Exception as e:
            Logger.error(f"获取用户使用摘要失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户使用摘要失败: {str(e)}"
            )
    
    async def get_knowledge_base_usage_summary(
        self,
        kb_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取知识库使用摘要
        
        Args:
            kb_id: 知识库ID
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 知识库使用摘要
        """
        try:
            Logger.info(f"获取知识库使用摘要: kb_id={kb_id}")
            
            # 设置时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 查询知识库统计
            kb_stats_query = select(
                func.count(PromptUsageLog.id).label('total_usage'),
                func.count(func.distinct(PromptUsageLog.template_id)).label('unique_templates'),
                func.count(func.distinct(PromptUsageLog.user_id)).label('unique_users'),
                func.count(func.case((PromptUsageLog.success == True, 1))).label('success_count'),
                func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.sum(PromptUsageLog.cost).label('total_cost'),
                func.sum(PromptUsageLog.token_count).label('total_tokens')
            ).filter(
                and_(
                    PromptUsageLog.kb_id == kb_id,
                    PromptUsageLog.created_at >= start_date,
                    PromptUsageLog.created_at <= end_date
                )
            )
            
            result = await self.db.execute(kb_stats_query)
            stats = result.fetchone()
            
            if not stats or stats.total_usage == 0:
                return {
                    "kb_id": kb_id,
                    "period_days": days,
                    "total_usage": 0,
                    "unique_templates": 0,
                    "unique_users": 0,
                    "success_rate": 0.0,
                    "avg_execution_time": None,
                    "avg_response_quality": None,
                    "total_cost": None,
                    "total_tokens": None,
                    "daily_average_usage": 0.0
                }
            
            # 计算衍生指标
            success_rate = float(stats.success_count) / float(stats.total_usage) if stats.total_usage > 0 else 0.0
            daily_average_usage = float(stats.total_usage) / float(days)
            
            return {
                "kb_id": kb_id,
                "period_days": days,
                "total_usage": stats.total_usage,
                "unique_templates": stats.unique_templates,
                "unique_users": stats.unique_users,
                "success_rate": success_rate,
                "avg_execution_time": float(stats.avg_execution_time) if stats.avg_execution_time else None,
                "avg_response_quality": float(stats.avg_response_quality) if stats.avg_response_quality else None,
                "total_cost": float(stats.total_cost) if stats.total_cost else None,
                "total_tokens": stats.total_tokens,
                "daily_average_usage": daily_average_usage
            }
            
        except Exception as e:
            Logger.error(f"获取知识库使用摘要失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取知识库使用摘要失败: {str(e)}"
            )    
 
   async def analyze_performance(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """分析性能指标
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            days: 分析天数
            
        Returns:
            Dict[str, Any]: 性能分析结果
        """
        try:
            Logger.info(f"开始性能分析: template_id={template_id}, user_id={user_id}")
            
            # 设置时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                PromptUsageLog.created_at >= start_date,
                PromptUsageLog.created_at <= end_date
            ]
            
            if template_id:
                conditions.append(PromptUsageLog.template_id == template_id)
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            if kb_id:
                conditions.append(PromptUsageLog.kb_id == kb_id)
            
            # 查询性能统计
            perf_query = select(
                func.count(PromptUsageLog.id).label('total_requests'),
                func.count(func.case((PromptUsageLog.success == True, 1))).label('success_count'),
                func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                func.percentile_cont(0.5).within_group(PromptUsageLog.execution_time).label('median_execution_time'),
                func.percentile_cont(0.95).within_group(PromptUsageLog.execution_time).label('p95_execution_time'),
                func.min(PromptUsageLog.execution_time).label('min_execution_time'),
                func.max(PromptUsageLog.execution_time).label('max_execution_time'),
                func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                func.avg(PromptUsageLog.token_count).label('avg_token_count'),
                func.sum(PromptUsageLog.cost).label('total_cost')
            ).filter(and_(*conditions))
            
            result = await self.db.execute(perf_query)
            perf_stats = result.fetchone()
            
            if not perf_stats or perf_stats.total_requests == 0:
                return {
                    "period_days": days,
                    "total_requests": 0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "performance_metrics": {},
                    "quality_metrics": {},
                    "cost_metrics": {},
                    "recommendations": []
                }
            
            # 计算基础指标
            success_rate = float(perf_stats.success_count) / float(perf_stats.total_requests)
            error_rate = 1.0 - success_rate
            
            # 性能指标
            performance_metrics = {
                "avg_execution_time": float(perf_stats.avg_execution_time) if perf_stats.avg_execution_time else None,
                "median_execution_time": float(perf_stats.median_execution_time) if perf_stats.median_execution_time else None,
                "p95_execution_time": float(perf_stats.p95_execution_time) if perf_stats.p95_execution_time else None,
                "min_execution_time": float(perf_stats.min_execution_time) if perf_stats.min_execution_time else None,
                "max_execution_time": float(perf_stats.max_execution_time) if perf_stats.max_execution_time else None
            }
            
            # 质量指标
            quality_metrics = {
                "avg_response_quality": float(perf_stats.avg_response_quality) if perf_stats.avg_response_quality else None,
                "avg_token_count": float(perf_stats.avg_token_count) if perf_stats.avg_token_count else None
            }
            
            # 成本指标
            cost_metrics = {
                "total_cost": float(perf_stats.total_cost) if perf_stats.total_cost else None,
                "avg_cost_per_request": float(perf_stats.total_cost) / float(perf_stats.total_requests) if perf_stats.total_cost else None,
                "daily_avg_cost": float(perf_stats.total_cost) / float(days) if perf_stats.total_cost else None
            }
            
            # 生成优化建议
            recommendations = await self._generate_optimization_suggestions(
                success_rate, performance_metrics, quality_metrics, cost_metrics
            )
            
            return {
                "period_days": days,
                "total_requests": perf_stats.total_requests,
                "success_rate": success_rate,
                "error_rate": error_rate,
                "performance_metrics": performance_metrics,
                "quality_metrics": quality_metrics,
                "cost_metrics": cost_metrics,
                "recommendations": recommendations
            }
            
        except Exception as e:
            Logger.error(f"性能分析失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"性能分析失败: {str(e)}"
            )
    
    async def get_optimization_suggestions(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """提供优化建议
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            days: 分析天数
            
        Returns:
            List[Dict[str, Any]]: 优化建议列表
        """
        try:
            Logger.info(f"生成优化建议: template_id={template_id}")
            
            # 获取性能分析结果
            perf_analysis = await self.analyze_performance(template_id, user_id, kb_id, days)
            
            suggestions = []
            
            # 基于成功率的建议
            if perf_analysis["success_rate"] < 0.9:
                suggestions.append({
                    "type": "error_rate",
                    "priority": "high",
                    "title": "错误率过高",
                    "description": f"当前成功率为 {perf_analysis['success_rate']:.2%}，建议检查模板配置和变量定义",
                    "action": "review_template_configuration"
                })
            
            # 基于执行时间的建议
            avg_time = perf_analysis["performance_metrics"].get("avg_execution_time")
            if avg_time and avg_time > 5.0:
                suggestions.append({
                    "type": "performance",
                    "priority": "medium",
                    "title": "执行时间过长",
                    "description": f"平均执行时间为 {avg_time:.2f}秒，建议优化模板内容长度",
                    "action": "optimize_template_content"
                })
            
            # 基于响应质量的建议
            avg_quality = perf_analysis["quality_metrics"].get("avg_response_quality")
            if avg_quality and avg_quality < 0.7:
                suggestions.append({
                    "type": "quality",
                    "priority": "high",
                    "title": "响应质量偏低",
                    "description": f"平均响应质量为 {avg_quality:.2f}，建议优化提示词内容",
                    "action": "improve_prompt_quality"
                })
            
            # 基于成本的建议
            avg_cost = perf_analysis["cost_metrics"].get("avg_cost_per_request")
            if avg_cost and avg_cost > 0.01:
                suggestions.append({
                    "type": "cost",
                    "priority": "medium",
                    "title": "单次请求成本较高",
                    "description": f"平均单次成本为 ${avg_cost:.4f}，建议优化token使用",
                    "action": "optimize_token_usage"
                })
            
            # 基于使用频率的建议
            if template_id:
                template_summary = await self.get_template_performance_summary(template_id, days)
                if template_summary["daily_average_usage"] < 1.0:
                    suggestions.append({
                        "type": "usage",
                        "priority": "low",
                        "title": "使用频率较低",
                        "description": f"日均使用 {template_summary['daily_average_usage']:.1f} 次，考虑是否需要推广使用",
                        "action": "promote_template_usage"
                    })
            
            return suggestions
            
        except Exception as e:
            Logger.error(f"生成优化建议失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"生成优化建议失败: {str(e)}"
            )
    
    async def detect_anomalous_usage(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """检测异常使用情况
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            days: 检测天数
            
        Returns:
            List[Dict[str, Any]]: 异常情况列表
        """
        try:
            Logger.info(f"检测异常使用: template_id={template_id}")
            
            # 设置时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                PromptUsageLog.created_at >= start_date,
                PromptUsageLog.created_at <= end_date
            ]
            
            if template_id:
                conditions.append(PromptUsageLog.template_id == template_id)
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            if kb_id:
                conditions.append(PromptUsageLog.kb_id == kb_id)
            
            anomalies = []
            
            # 检测执行时间异常
            time_anomaly_query = select(
                PromptUsageLog.id,
                PromptUsageLog.template_id,
                PromptUsageLog.execution_time,
                PromptUsageLog.created_at,
                PromptTemplate.name.label('template_name')
            ).select_from(
                PromptUsageLog.__table__.join(
                    PromptTemplate.__table__,
                    PromptUsageLog.template_id == PromptTemplate.id
                )
            ).filter(
                and_(
                    *conditions,
                    PromptUsageLog.execution_time > 10.0  # 超过10秒认为异常
                )
            ).order_by(desc(PromptUsageLog.execution_time)).limit(10)
            
            result = await self.db.execute(time_anomaly_query)
            time_anomalies = result.fetchall()
            
            for anomaly in time_anomalies:
                anomalies.append({
                    "type": "execution_time",
                    "severity": "high" if anomaly.execution_time > 30 else "medium",
                    "template_id": anomaly.template_id,
                    "template_name": anomaly.template_name,
                    "value": anomaly.execution_time,
                    "threshold": 10.0,
                    "timestamp": anomaly.created_at,
                    "description": f"执行时间异常: {anomaly.execution_time:.2f}秒"
                })
            
            # 检测错误率异常
            error_anomaly_query = select(
                PromptUsageLog.template_id,
                PromptTemplate.name.label('template_name'),
                func.count(PromptUsageLog.id).label('total_count'),
                func.count(func.case((PromptUsageLog.success == False, 1))).label('error_count')
            ).select_from(
                PromptUsageLog.__table__.join(
                    PromptTemplate.__table__,
                    PromptUsageLog.template_id == PromptTemplate.id
                )
            ).filter(
                and_(*conditions)
            ).group_by(
                PromptUsageLog.template_id,
                PromptTemplate.name
            ).having(
                func.count(func.case((PromptUsageLog.success == False, 1))) > 
                func.count(PromptUsageLog.id) * 0.2  # 错误率超过20%
            )
            
            result = await self.db.execute(error_anomaly_query)
            error_anomalies = result.fetchall()
            
            for anomaly in error_anomalies:
                error_rate = float(anomaly.error_count) / float(anomaly.total_count)
                anomalies.append({
                    "type": "error_rate",
                    "severity": "high" if error_rate > 0.5 else "medium",
                    "template_id": anomaly.template_id,
                    "template_name": anomaly.template_name,
                    "value": error_rate,
                    "threshold": 0.2,
                    "timestamp": end_date,
                    "description": f"错误率异常: {error_rate:.2%}"
                })
            
            # 检测使用量突增
            usage_spike_query = select(
                func.date(PromptUsageLog.created_at).label('date'),
                PromptUsageLog.template_id,
                PromptTemplate.name.label('template_name'),
                func.count(PromptUsageLog.id).label('daily_usage')
            ).select_from(
                PromptUsageLog.__table__.join(
                    PromptTemplate.__table__,
                    PromptUsageLog.template_id == PromptTemplate.id
                )
            ).filter(
                and_(*conditions)
            ).group_by(
                func.date(PromptUsageLog.created_at),
                PromptUsageLog.template_id,
                PromptTemplate.name
            ).having(
                func.count(PromptUsageLog.id) > 100  # 单日使用超过100次
            ).order_by(desc('daily_usage'))
            
            result = await self.db.execute(usage_spike_query)
            usage_spikes = result.fetchall()
            
            for spike in usage_spikes:
                anomalies.append({
                    "type": "usage_spike",
                    "severity": "medium",
                    "template_id": spike.template_id,
                    "template_name": spike.template_name,
                    "value": spike.daily_usage,
                    "threshold": 100,
                    "timestamp": spike.date,
                    "description": f"使用量突增: {spike.daily_usage}次/天"
                })
            
            Logger.info(f"检测到 {len(anomalies)} 个异常情况")
            return anomalies
            
        except Exception as e:
            Logger.error(f"异常检测失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"异常检测失败: {str(e)}"
            )
    
    async def _generate_optimization_suggestions(
        self,
        success_rate: float,
        performance_metrics: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        cost_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议的内部方法
        
        Args:
            success_rate: 成功率
            performance_metrics: 性能指标
            quality_metrics: 质量指标
            cost_metrics: 成本指标
            
        Returns:
            List[Dict[str, Any]]: 建议列表
        """
        suggestions = []
        
        # 成功率建议
        if success_rate < 0.95:
            priority = "high" if success_rate < 0.9 else "medium"
            suggestions.append({
                "category": "reliability",
                "priority": priority,
                "title": "提高成功率",
                "description": f"当前成功率 {success_rate:.2%}，建议检查模板变量定义和错误处理",
                "metrics": {"current_success_rate": success_rate, "target_success_rate": 0.95}
            })
        
        # 性能建议
        avg_time = performance_metrics.get("avg_execution_time")
        if avg_time and avg_time > 3.0:
            priority = "high" if avg_time > 10.0 else "medium"
            suggestions.append({
                "category": "performance",
                "priority": priority,
                "title": "优化执行时间",
                "description": f"平均执行时间 {avg_time:.2f}秒，建议简化模板内容或优化变量处理",
                "metrics": {"current_avg_time": avg_time, "target_avg_time": 3.0}
            })
        
        # 质量建议
        avg_quality = quality_metrics.get("avg_response_quality")
        if avg_quality and avg_quality < 0.8:
            priority = "high" if avg_quality < 0.6 else "medium"
            suggestions.append({
                "category": "quality",
                "priority": priority,
                "title": "提升响应质量",
                "description": f"平均响应质量 {avg_quality:.2f}，建议优化提示词内容和结构",
                "metrics": {"current_quality": avg_quality, "target_quality": 0.8}
            })
        
        # 成本建议
        avg_cost = cost_metrics.get("avg_cost_per_request")
        if avg_cost and avg_cost > 0.005:
            suggestions.append({
                "category": "cost",
                "priority": "medium",
                "title": "降低使用成本",
                "description": f"平均单次成本 ${avg_cost:.4f}，建议优化token使用效率",
                "metrics": {"current_cost": avg_cost, "target_cost": 0.005}
            })
        
        return suggestions