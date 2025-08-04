import secrets
import hashlib
import hmac
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, delete, update
from sqlalchemy.orm import selectinload

from app.models.database import AsyncSessionLocal
from app.models.integration import (
    APIKey, Webhook, WebhookDelivery, Integration, APIEndpoint,
    APIUsageLog, IntegrationTemplate, APIDocumentation,
    WebhookStatus, WebhookEvent, IntegrationType, APIKeyScope
)
from app.models.user import User
from app.schemas.integration import (
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    WebhookCreate, WebhookUpdate, WebhookResponse,
    WebhookDeliveryResponse, WebhookTestRequest,
    IntegrationCreate, IntegrationUpdate, IntegrationResponse,
    APIEndpointResponse, APIUsageStatsResponse,
    IntegrationTemplateResponse, APIDocumentationCreate,
    APIDocumentationUpdate, APIDocumentationResponse,
    IntegrationDashboardResponse, WebhookEventPayload
)
from app.core.logger import Logger
from app.core.redis_manager import redis_manager

class IntegrationService:
    """集成管理服务
    
    提供API密钥管理、Webhook管理、第三方集成等功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== API密钥管理 ====================
    
    async def create_api_key(
        self,
        key_data: APIKeyCreate,
        created_by: int
    ) -> APIKeyCreateResponse:
        """创建API密钥"""
        try:
            # 生成API密钥
            key_value = self._generate_api_key()
            key_hash = self._hash_api_key(key_value)
            key_prefix = key_value[:8]
            
            api_key = APIKey(
                name=key_data.name,
                description=key_data.description,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=[scope.value for scope in key_data.scopes],
                rate_limit=key_data.rate_limit,
                expires_at=key_data.expires_at,
                created_by=created_by
            )
            
            self.db.add(api_key)
            await self.db.commit()
            await self.db.refresh(api_key)
            
            return APIKeyCreateResponse(
                id=api_key.id,
                name=api_key.name,
                api_key=key_value,
                key_prefix=api_key.key_prefix,
                scopes=api_key.scopes,
                expires_at=api_key.expires_at
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建API密钥失败: {str(e)}")
            raise
    
    async def get_api_keys(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[APIKeyResponse]:
        """获取API密钥列表"""
        try:
            query = select(APIKey)
            
            if is_active is not None:
                query = query.where(APIKey.is_active == is_active)
            
            query = query.offset(skip).limit(limit).order_by(desc(APIKey.created_at))
            
            result = await self.db.execute(query)
            api_keys = result.scalars().all()
            
            return [
                APIKeyResponse(
                    id=key.id,
                    name=key.name,
                    description=key.description,
                    key_prefix=key.key_prefix,
                    scopes=key.scopes,
                    rate_limit=key.rate_limit,
                    is_active=key.is_active,
                    last_used_at=key.last_used_at,
                    usage_count=key.usage_count,
                    expires_at=key.expires_at,
                    created_at=key.created_at,
                    created_by=key.created_by
                ) for key in api_keys
            ]
            
        except Exception as e:
            Logger.error(f"获取API密钥列表失败: {str(e)}")
            raise
    
    async def revoke_api_key(self, key_id: int) -> bool:
        """撤销API密钥"""
        try:
            api_key = await self.db.get(APIKey, key_id)
            if not api_key:
                raise ValueError("API密钥不存在")
            
            api_key.is_active = False
            await self.db.commit()
            
            # 清除缓存
            await redis_manager.delete(f"api_key:{api_key.key_prefix}")
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"撤销API密钥失败: {str(e)}")
            raise
    
    def _generate_api_key(self) -> str:
        """生成API密钥"""
        return f"eak_{secrets.token_urlsafe(32)}"
    
    def _hash_api_key(self, key: str) -> str:
        """哈希API密钥"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    # ==================== Webhook管理 ====================
    
    async def create_webhook(
        self,
        webhook_data: WebhookCreate,
        created_by: int
    ) -> WebhookResponse:
        """创建Webhook"""
        try:
            webhook = Webhook(
                name=webhook_data.name,
                description=webhook_data.description,
                url=str(webhook_data.url),
                secret=webhook_data.secret or self._generate_webhook_secret(),
                events=[event.value for event in webhook_data.events],
                headers=webhook_data.headers,
                timeout=webhook_data.timeout,
                retry_count=webhook_data.retry_count,
                created_by=created_by
            )
            
            self.db.add(webhook)
            await self.db.commit()
            await self.db.refresh(webhook)
            
            return WebhookResponse(
                id=webhook.id,
                name=webhook.name,
                description=webhook.description,
                url=webhook.url,
                events=webhook.events,
                headers=webhook.headers,
                timeout=webhook.timeout,
                retry_count=webhook.retry_count,
                status=WebhookStatus(webhook.status),
                is_active=webhook.is_active,
                success_count=webhook.success_count,
                failure_count=webhook.failure_count,
                last_triggered_at=webhook.last_triggered_at,
                last_success_at=webhook.last_success_at,
                last_failure_at=webhook.last_failure_at,
                created_at=webhook.created_at,
                created_by=webhook.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建Webhook失败: {str(e)}")
            raise
    
    async def update_webhook(
        self,
        webhook_id: int,
        webhook_data: WebhookUpdate
    ) -> WebhookResponse:
        """更新Webhook"""
        try:
            webhook = await self.db.get(Webhook, webhook_id)
            if not webhook:
                raise ValueError("Webhook不存在")
            
            update_data = webhook_data.model_dump(exclude_unset=True)
            
            if 'url' in update_data:
                update_data['url'] = str(update_data['url'])
            if 'events' in update_data:
                update_data['events'] = [event.value for event in update_data['events']]
            
            for field, value in update_data.items():
                setattr(webhook, field, value)
            
            webhook.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(webhook)
            
            return WebhookResponse(
                id=webhook.id,
                name=webhook.name,
                description=webhook.description,
                url=webhook.url,
                events=webhook.events,
                headers=webhook.headers,
                timeout=webhook.timeout,
                retry_count=webhook.retry_count,
                status=WebhookStatus(webhook.status),
                is_active=webhook.is_active,
                success_count=webhook.success_count,
                failure_count=webhook.failure_count,
                last_triggered_at=webhook.last_triggered_at,
                last_success_at=webhook.last_success_at,
                last_failure_at=webhook.last_failure_at,
                created_at=webhook.created_at,
                created_by=webhook.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"更新Webhook失败: {str(e)}")
            raise
    
    async def trigger_webhook(
        self,
        event_type: WebhookEvent,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """触发Webhook"""
        try:
            # 查找监听该事件的Webhook
            webhooks_result = await self.db.execute(
                select(Webhook)
                .where(Webhook.is_active == True)
                .where(Webhook.events.contains([event_type.value]))
            )
            webhooks = webhooks_result.scalars().all()
            
            # 构建事件载荷
            event_payload = WebhookEventPayload(
                event_type=event_type.value,
                timestamp=datetime.now(),
                data=payload,
                metadata=metadata
            )
            
            # 异步发送Webhook
            for webhook in webhooks:
                asyncio.create_task(
                    self._deliver_webhook(webhook, event_payload.model_dump())
                )
            
        except Exception as e:
            Logger.error(f"触发Webhook失败: {str(e)}")
    
    async def _deliver_webhook(self, webhook: Webhook, payload: Dict[str, Any]):
        """投递Webhook"""
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=payload['event_type'],
            payload=payload
        )
        
        try:
            # 准备请求头
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'EmbedAI-Webhook/1.0'
            }
            
            if webhook.headers:
                headers.update(webhook.headers)
            
            # 添加签名
            if webhook.secret:
                signature = self._generate_webhook_signature(
                    json.dumps(payload, separators=(',', ':')),
                    webhook.secret
                )
                headers['X-EmbedAI-Signature'] = signature
            
            delivery.request_headers = headers
            
            # 发送请求
            start_time = datetime.now()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=webhook.timeout)) as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers
                ) as response:
                    end_time = datetime.now()
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    delivery.response_status = response.status
                    delivery.response_headers = dict(response.headers)
                    delivery.response_body = await response.text()
                    delivery.duration_ms = duration_ms
                    delivery.is_success = 200 <= response.status < 300
            
            # 更新Webhook统计
            webhook.last_triggered_at = datetime.now()
            if delivery.is_success:
                webhook.success_count += 1
                webhook.last_success_at = datetime.now()
                webhook.status = WebhookStatus.ACTIVE.value
            else:
                webhook.failure_count += 1
                webhook.last_failure_at = datetime.now()
                if webhook.failure_count >= 10:  # 连续失败10次后暂停
                    webhook.status = WebhookStatus.FAILED.value
            
        except Exception as e:
            delivery.is_success = False
            delivery.error_message = str(e)
            webhook.failure_count += 1
            webhook.last_failure_at = datetime.now()
            webhook.last_triggered_at = datetime.now()
            
            if webhook.failure_count >= 10:
                webhook.status = WebhookStatus.FAILED.value
        
        finally:
            # 保存投递记录
            async with AsyncSessionLocal() as db:
                try:
                    db.add(delivery)
                    await db.merge(webhook)
                    await db.commit()
                except Exception as e:
                    Logger.error(f"保存Webhook投递记录失败: {str(e)}")
    
    def _generate_webhook_secret(self) -> str:
        """生成Webhook密钥"""
        return secrets.token_urlsafe(32)
    
    def _generate_webhook_signature(self, payload: str, secret: str) -> str:
        """生成Webhook签名"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def test_webhook(
        self,
        webhook_id: int,
        test_request: WebhookTestRequest
    ) -> WebhookDeliveryResponse:
        """测试Webhook"""
        try:
            webhook = await self.db.get(Webhook, webhook_id)
            if not webhook:
                raise ValueError("Webhook不存在")
            
            # 构建测试载荷
            test_payload = test_request.test_payload or {
                "test": True,
                "message": "This is a test webhook delivery"
            }
            
            event_payload = WebhookEventPayload(
                event_type=test_request.event_type.value,
                timestamp=datetime.now(),
                data=test_payload,
                metadata={"test": True}
            )
            
            # 发送测试Webhook
            await self._deliver_webhook(webhook, event_payload.model_dump())
            
            # 获取最新的投递记录
            delivery_result = await self.db.execute(
                select(WebhookDelivery)
                .where(WebhookDelivery.webhook_id == webhook_id)
                .order_by(desc(WebhookDelivery.delivered_at))
                .limit(1)
            )
            delivery = delivery_result.scalar_one()
            
            return WebhookDeliveryResponse(
                id=delivery.id,
                webhook_id=delivery.webhook_id,
                event_type=delivery.event_type,
                payload=delivery.payload,
                request_headers=delivery.request_headers,
                response_status=delivery.response_status,
                response_headers=delivery.response_headers,
                response_body=delivery.response_body,
                duration_ms=delivery.duration_ms,
                is_success=delivery.is_success,
                error_message=delivery.error_message,
                retry_count=delivery.retry_count,
                delivered_at=delivery.delivered_at
            )
            
        except Exception as e:
            Logger.error(f"测试Webhook失败: {str(e)}")
            raise

    # ==================== 第三方集成管理 ====================

    async def create_integration(
        self,
        integration_data: IntegrationCreate,
        created_by: int
    ) -> IntegrationResponse:
        """创建第三方集成"""
        try:
            integration = Integration(
                name=integration_data.name,
                description=integration_data.description,
                integration_type=integration_data.integration_type.value,
                provider=integration_data.provider,
                config=integration_data.config,
                credentials=integration_data.credentials,
                created_by=created_by
            )

            self.db.add(integration)
            await self.db.commit()
            await self.db.refresh(integration)

            # 验证集成配置
            await self._verify_integration(integration)

            return IntegrationResponse(
                id=integration.id,
                name=integration.name,
                description=integration.description,
                integration_type=integration.integration_type,
                provider=integration.provider,
                config=integration.config,
                is_active=integration.is_active,
                is_verified=integration.is_verified,
                last_sync_at=integration.last_sync_at,
                sync_status=integration.sync_status,
                error_message=integration.error_message,
                created_at=integration.created_at,
                created_by=integration.created_by
            )

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建第三方集成失败: {str(e)}")
            raise

    async def _verify_integration(self, integration: Integration):
        """验证集成配置"""
        try:
            if integration.integration_type == IntegrationType.WEBHOOK.value:
                # 验证Webhook URL
                async with aiohttp.ClientSession() as session:
                    async with session.get(integration.config.get('url', '')) as response:
                        integration.is_verified = response.status == 200
            elif integration.integration_type == IntegrationType.API_CLIENT.value:
                # 验证API客户端配置
                integration.is_verified = True  # 简化验证
            else:
                integration.is_verified = True

            integration.sync_status = "verified" if integration.is_verified else "failed"
            await self.db.commit()

        except Exception as e:
            integration.is_verified = False
            integration.sync_status = "failed"
            integration.error_message = str(e)
            await self.db.commit()

    # ==================== API文档管理 ====================

    async def create_api_documentation(
        self,
        doc_data: APIDocumentationCreate,
        created_by: int
    ) -> APIDocumentationResponse:
        """创建API文档"""
        try:
            documentation = APIDocumentation(
                **doc_data.model_dump(),
                created_by=created_by
            )

            self.db.add(documentation)
            await self.db.commit()
            await self.db.refresh(documentation)

            return APIDocumentationResponse(
                id=documentation.id,
                title=documentation.title,
                content=documentation.content,
                content_type=documentation.content_type,
                category=documentation.category,
                tags=documentation.tags,
                version=documentation.version,
                order_index=documentation.order_index,
                is_published=documentation.is_published,
                is_featured=documentation.is_featured,
                view_count=documentation.view_count,
                last_viewed_at=documentation.last_viewed_at,
                created_at=documentation.created_at,
                updated_at=documentation.updated_at,
                created_by=documentation.created_by
            )

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建API文档失败: {str(e)}")
            raise

    async def get_api_documentation(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        version: Optional[str] = None,
        is_published: Optional[bool] = None
    ) -> List[APIDocumentationResponse]:
        """获取API文档列表"""
        try:
            query = select(APIDocumentation)

            if category:
                query = query.where(APIDocumentation.category == category)
            if version:
                query = query.where(APIDocumentation.version == version)
            if is_published is not None:
                query = query.where(APIDocumentation.is_published == is_published)

            query = query.offset(skip).limit(limit).order_by(
                APIDocumentation.order_index,
                APIDocumentation.created_at
            )

            result = await self.db.execute(query)
            docs = result.scalars().all()

            return [
                APIDocumentationResponse(
                    id=doc.id,
                    title=doc.title,
                    content=doc.content,
                    content_type=doc.content_type,
                    category=doc.category,
                    tags=doc.tags,
                    version=doc.version,
                    order_index=doc.order_index,
                    is_published=doc.is_published,
                    is_featured=doc.is_featured,
                    view_count=doc.view_count,
                    last_viewed_at=doc.last_viewed_at,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    created_by=doc.created_by
                ) for doc in docs
            ]

        except Exception as e:
            Logger.error(f"获取API文档列表失败: {str(e)}")
            raise

    # ==================== API使用统计 ====================

    async def log_api_usage(
        self,
        api_key_id: Optional[int],
        endpoint_id: Optional[int],
        method: str,
        path: str,
        status_code: int,
        response_time_ms: Optional[int] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """记录API使用日志"""
        try:
            usage_log = APIUsageLog(
                api_key_id=api_key_id,
                endpoint_id=endpoint_id,
                method=method,
                path=path,
                status_code=status_code,
                response_time_ms=response_time_ms,
                request_size=request_size,
                response_size=response_size,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error_message
            )

            self.db.add(usage_log)

            # 更新API密钥使用统计
            if api_key_id:
                api_key = await self.db.get(APIKey, api_key_id)
                if api_key:
                    api_key.usage_count += 1
                    api_key.last_used_at = datetime.now()

            await self.db.commit()

        except Exception as e:
            Logger.error(f"记录API使用日志失败: {str(e)}")

    async def get_api_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> APIUsageStatsResponse:
        """获取API使用统计"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()

            # 总请求数
            total_requests_result = await self.db.execute(
                select(func.count(APIUsageLog.id))
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
            )
            total_requests = total_requests_result.scalar() or 0

            # 成功请求数
            successful_requests_result = await self.db.execute(
                select(func.count(APIUsageLog.id))
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
                .where(APIUsageLog.status_code >= 200)
                .where(APIUsageLog.status_code < 400)
            )
            successful_requests = successful_requests_result.scalar() or 0

            # 失败请求数
            failed_requests = total_requests - successful_requests

            # 平均响应时间
            avg_response_time_result = await self.db.execute(
                select(func.avg(APIUsageLog.response_time_ms))
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
                .where(APIUsageLog.response_time_ms.isnot(None))
            )
            average_response_time = avg_response_time_result.scalar() or 0.0

            # 按端点统计请求
            requests_by_endpoint_result = await self.db.execute(
                select(APIUsageLog.path, func.count(APIUsageLog.id))
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
                .group_by(APIUsageLog.path)
                .order_by(desc(func.count(APIUsageLog.id)))
                .limit(10)
            )
            requests_by_endpoint = dict(requests_by_endpoint_result.fetchall())

            # 按状态码统计请求
            requests_by_status_result = await self.db.execute(
                select(APIUsageLog.status_code, func.count(APIUsageLog.id))
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
                .group_by(APIUsageLog.status_code)
            )
            requests_by_status = {
                str(status): count for status, count in requests_by_status_result.fetchall()
            }

            # 按小时统计请求
            requests_by_hour_result = await self.db.execute(
                select(
                    func.date_trunc('hour', APIUsageLog.created_at).label('hour'),
                    func.count(APIUsageLog.id).label('count')
                )
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
                .group_by('hour')
                .order_by('hour')
            )
            requests_by_hour = [
                {"hour": hour.isoformat(), "count": count}
                for hour, count in requests_by_hour_result.fetchall()
            ]

            # 热门API密钥
            top_api_keys_result = await self.db.execute(
                select(APIKey.name, func.count(APIUsageLog.id).label('usage_count'))
                .join(APIUsageLog, APIKey.id == APIUsageLog.api_key_id)
                .where(APIUsageLog.created_at >= start_date)
                .where(APIUsageLog.created_at <= end_date)
                .group_by(APIKey.id, APIKey.name)
                .order_by(desc('usage_count'))
                .limit(5)
            )
            top_api_keys = [
                {"name": name, "usage_count": count}
                for name, count in top_api_keys_result.fetchall()
            ]

            return APIUsageStatsResponse(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                average_response_time=float(average_response_time),
                requests_by_endpoint=requests_by_endpoint,
                requests_by_status=requests_by_status,
                requests_by_hour=requests_by_hour,
                top_api_keys=top_api_keys
            )

        except Exception as e:
            Logger.error(f"获取API使用统计失败: {str(e)}")
            raise

    # ==================== 集成仪表板 ====================

    async def get_integration_dashboard(self) -> IntegrationDashboardResponse:
        """获取集成管理仪表板数据"""
        try:
            # 总集成数
            total_integrations_result = await self.db.execute(select(func.count(Integration.id)))
            total_integrations = total_integrations_result.scalar() or 0

            # 活跃集成数
            active_integrations_result = await self.db.execute(
                select(func.count(Integration.id)).where(Integration.is_active == True)
            )
            active_integrations = active_integrations_result.scalar() or 0

            # 总Webhook数
            total_webhooks_result = await self.db.execute(select(func.count(Webhook.id)))
            total_webhooks = total_webhooks_result.scalar() or 0

            # 活跃Webhook数
            active_webhooks_result = await self.db.execute(
                select(func.count(Webhook.id)).where(Webhook.is_active == True)
            )
            active_webhooks = active_webhooks_result.scalar() or 0

            # 总API密钥数
            total_api_keys_result = await self.db.execute(select(func.count(APIKey.id)))
            total_api_keys = total_api_keys_result.scalar() or 0

            # 活跃API密钥数
            active_api_keys_result = await self.db.execute(
                select(func.count(APIKey.id)).where(APIKey.is_active == True)
            )
            active_api_keys = active_api_keys_result.scalar() or 0

            # 24小时API请求数
            yesterday = datetime.now() - timedelta(hours=24)
            api_requests_24h_result = await self.db.execute(
                select(func.count(APIUsageLog.id)).where(APIUsageLog.created_at >= yesterday)
            )
            api_requests_24h = api_requests_24h_result.scalar() or 0

            # 24小时Webhook投递数
            webhook_deliveries_24h_result = await self.db.execute(
                select(func.count(WebhookDelivery.id)).where(WebhookDelivery.delivered_at >= yesterday)
            )
            webhook_deliveries_24h = webhook_deliveries_24h_result.scalar() or 0

            # 最近API使用
            recent_api_usage_result = await self.db.execute(
                select(APIUsageLog)
                .order_by(desc(APIUsageLog.created_at))
                .limit(10)
            )
            recent_api_usage = [
                {
                    "method": log.method,
                    "path": log.path,
                    "status_code": log.status_code,
                    "response_time_ms": log.response_time_ms,
                    "created_at": log.created_at.isoformat()
                } for log in recent_api_usage_result.scalars().all()
            ]

            # 最近Webhook投递
            recent_webhook_deliveries_result = await self.db.execute(
                select(WebhookDelivery)
                .order_by(desc(WebhookDelivery.delivered_at))
                .limit(10)
            )
            recent_webhook_deliveries = [
                WebhookDeliveryResponse(
                    id=delivery.id,
                    webhook_id=delivery.webhook_id,
                    event_type=delivery.event_type,
                    payload=delivery.payload,
                    request_headers=delivery.request_headers,
                    response_status=delivery.response_status,
                    response_headers=delivery.response_headers,
                    response_body=delivery.response_body,
                    duration_ms=delivery.duration_ms,
                    is_success=delivery.is_success,
                    error_message=delivery.error_message,
                    retry_count=delivery.retry_count,
                    delivered_at=delivery.delivered_at
                ) for delivery in recent_webhook_deliveries_result.scalars().all()
            ]

            # 按类型统计集成
            integration_by_type_result = await self.db.execute(
                select(Integration.integration_type, func.count(Integration.id))
                .group_by(Integration.integration_type)
            )
            integration_by_type = dict(integration_by_type_result.fetchall())

            # Webhook成功率
            webhook_success_result = await self.db.execute(
                select(func.count(WebhookDelivery.id)).where(WebhookDelivery.is_success == True)
            )
            webhook_success_count = webhook_success_result.scalar() or 0

            webhook_total_result = await self.db.execute(select(func.count(WebhookDelivery.id)))
            webhook_total_count = webhook_total_result.scalar() or 0

            webhook_success_rate = (webhook_success_count / webhook_total_count * 100) if webhook_total_count > 0 else 0.0

            return IntegrationDashboardResponse(
                total_integrations=total_integrations,
                active_integrations=active_integrations,
                total_webhooks=total_webhooks,
                active_webhooks=active_webhooks,
                total_api_keys=total_api_keys,
                active_api_keys=active_api_keys,
                api_requests_24h=api_requests_24h,
                webhook_deliveries_24h=webhook_deliveries_24h,
                recent_api_usage=recent_api_usage,
                recent_webhook_deliveries=recent_webhook_deliveries,
                integration_by_type=integration_by_type,
                webhook_success_rate=webhook_success_rate
            )

        except Exception as e:
            Logger.error(f"获取集成管理仪表板数据失败: {str(e)}")
            raise
