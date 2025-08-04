import secrets
import hashlib
import pyotp
import qrcode
import io
import base64
import ipaddress
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, delete
from sqlalchemy.orm import selectinload

from app.models.security import (
    TwoFactorAuth, UserSession, IPWhitelist, IPBlacklist, SecurityEvent,
    PasswordHistory, DeviceFingerprint, SecurityPolicy, TwoFactorMethod,
    SessionStatus, SecurityEventType
)
from app.models.user import User
from app.schemas.security import (
    TwoFactorSetupRequest, TwoFactorSetupResponse, TwoFactorVerifyRequest,
    TwoFactorStatusResponse, SessionResponse, SessionListResponse,
    IPWhitelistCreate, IPWhitelistResponse, IPBlacklistCreate, IPBlacklistResponse,
    SecurityEventCreate, SecurityEventResponse, DeviceFingerprintResponse,
    SecurityPolicyCreate, SecurityPolicyResponse, SecurityDashboardResponse,
    SecurityAuditRequest, SecurityAuditResponse, BulkIPOperation
)
from app.core.logger import Logger
from app.core.redis_manager import redis_manager
from app.core.security import get_password_hash, verify_password

class SecurityService:
    """安全服务
    
    提供双因子认证、会话管理、IP控制、安全审计等功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 双因子认证 ====================
    
    async def setup_two_factor(self, user_id: int, setup_request: TwoFactorSetupRequest) -> TwoFactorSetupResponse:
        """设置双因子认证"""
        try:
            # 检查是否已存在2FA设置
            existing = await self.db.execute(
                select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_id)
            )
            existing_2fa = existing.scalar_one_or_none()
            
            if existing_2fa and existing_2fa.is_enabled:
                raise ValueError("双因子认证已启用")
            
            # 生成密钥
            secret_key = pyotp.random_base32()
            
            # 生成备用验证码
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            
            # 获取用户信息
            user = await self.db.get(User, user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 生成二维码
            if setup_request.method == TwoFactorMethod.TOTP:
                totp = pyotp.TOTP(secret_key)
                provisioning_uri = totp.provisioning_uri(
                    name=user.email,
                    issuer_name="EmbedAI Server"
                )
                
                # 生成二维码图片
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(provisioning_uri)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                qr_code_url = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
            else:
                qr_code_url = ""
            
            # 保存或更新2FA设置
            if existing_2fa:
                existing_2fa.method = setup_request.method.value
                existing_2fa.secret_key = secret_key
                existing_2fa.backup_codes = backup_codes
                existing_2fa.phone_number = setup_request.phone_number
                existing_2fa.email = setup_request.email
                two_factor = existing_2fa
            else:
                two_factor = TwoFactorAuth(
                    user_id=user_id,
                    method=setup_request.method.value,
                    secret_key=secret_key,
                    backup_codes=backup_codes,
                    phone_number=setup_request.phone_number,
                    email=setup_request.email,
                    is_enabled=False
                )
                self.db.add(two_factor)
            
            await self.db.commit()
            
            return TwoFactorSetupResponse(
                secret_key=secret_key,
                qr_code_url=qr_code_url,
                backup_codes=backup_codes,
                method=setup_request.method
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"设置双因子认证失败: {str(e)}")
            raise
    
    async def verify_two_factor(self, user_id: int, verify_request: TwoFactorVerifyRequest) -> bool:
        """验证双因子认证"""
        try:
            two_factor = await self.db.execute(
                select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_id)
            )
            two_factor_auth = two_factor.scalar_one_or_none()
            
            if not two_factor_auth:
                raise ValueError("未设置双因子认证")
            
            # 验证备用验证码
            if verify_request.backup_code:
                if verify_request.backup_code in two_factor_auth.backup_codes:
                    # 移除已使用的备用验证码
                    two_factor_auth.backup_codes.remove(verify_request.backup_code)
                    two_factor_auth.last_used_at = datetime.now()
                    await self.db.commit()
                    return True
                else:
                    return False
            
            # 验证TOTP验证码
            if two_factor_auth.method == TwoFactorMethod.TOTP.value:
                totp = pyotp.TOTP(two_factor_auth.secret_key)
                if totp.verify(verify_request.code, valid_window=1):
                    two_factor_auth.last_used_at = datetime.now()
                    if not two_factor_auth.is_enabled:
                        two_factor_auth.is_enabled = True
                    await self.db.commit()
                    return True
            
            return False
            
        except Exception as e:
            Logger.error(f"验证双因子认证失败: {str(e)}")
            return False
    
    async def get_two_factor_status(self, user_id: int) -> TwoFactorStatusResponse:
        """获取双因子认证状态"""
        try:
            two_factor = await self.db.execute(
                select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_id)
            )
            two_factor_auth = two_factor.scalar_one_or_none()
            
            if not two_factor_auth:
                return TwoFactorStatusResponse(
                    is_enabled=False,
                    backup_codes_count=0
                )
            
            return TwoFactorStatusResponse(
                is_enabled=two_factor_auth.is_enabled,
                method=TwoFactorMethod(two_factor_auth.method) if two_factor_auth.method else None,
                phone_number=two_factor_auth.phone_number,
                email=two_factor_auth.email,
                backup_codes_count=len(two_factor_auth.backup_codes or []),
                last_used_at=two_factor_auth.last_used_at
            )
            
        except Exception as e:
            Logger.error(f"获取双因子认证状态失败: {str(e)}")
            raise
    
    async def disable_two_factor(self, user_id: int) -> bool:
        """禁用双因子认证"""
        try:
            two_factor = await self.db.execute(
                select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_id)
            )
            two_factor_auth = two_factor.scalar_one_or_none()
            
            if two_factor_auth:
                await self.db.delete(two_factor_auth)
                await self.db.commit()
                
                # 记录安全事件
                await self.log_security_event(
                    user_id=user_id,
                    event_type=SecurityEventType.TWO_FACTOR_DISABLED,
                    severity="warning",
                    details={"action": "two_factor_disabled"}
                )
                
                return True
            
            return False
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"禁用双因子认证失败: {str(e)}")
            raise
    
    # ==================== 会话管理 ====================
    
    async def create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        device_fingerprint: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """创建用户会话"""
        try:
            # 生成会话令牌
            session_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            # 检测是否为移动设备
            is_mobile = self._is_mobile_device(user_agent)
            
            # 检查设备是否受信任
            is_trusted = False
            if device_fingerprint:
                is_trusted = await self._is_trusted_device(user_id, device_fingerprint)
            
            # 创建会话
            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                location=location,
                is_mobile=is_mobile,
                is_trusted=is_trusted,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            # 缓存会话信息
            await redis_manager.set(f"session:{session_token}", str(session.id), expire=86400)
            
            return session
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建会话失败: {str(e)}")
            raise
    
    async def get_user_sessions(self, user_id: int, current_session_id: Optional[int] = None) -> SessionListResponse:
        """获取用户会话列表"""
        try:
            sessions_result = await self.db.execute(
                select(UserSession)
                .where(UserSession.user_id == user_id)
                .where(UserSession.status == SessionStatus.ACTIVE.value)
                .order_by(desc(UserSession.last_activity))
            )
            sessions = sessions_result.scalars().all()
            
            session_responses = []
            for session in sessions:
                session_responses.append(SessionResponse(
                    id=session.id,
                    session_token=session.session_token[:8] + "...",  # 部分显示
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    device_fingerprint=session.device_fingerprint,
                    location=session.location,
                    status=SessionStatus(session.status),
                    is_mobile=session.is_mobile,
                    is_trusted=session.is_trusted,
                    last_activity=session.last_activity,
                    expires_at=session.expires_at,
                    created_at=session.created_at
                ))
            
            return SessionListResponse(
                current_session_id=current_session_id or 0,
                sessions=session_responses,
                total_count=len(session_responses)
            )
            
        except Exception as e:
            Logger.error(f"获取用户会话列表失败: {str(e)}")
            raise
    
    async def terminate_sessions(
        self,
        user_id: int,
        session_ids: List[int],
        terminated_by: int,
        terminate_all: bool = False
    ) -> int:
        """终止用户会话"""
        try:
            terminated_count = 0
            
            if terminate_all:
                # 终止所有会话
                sessions_result = await self.db.execute(
                    select(UserSession)
                    .where(UserSession.user_id == user_id)
                    .where(UserSession.status == SessionStatus.ACTIVE.value)
                )
                sessions = sessions_result.scalars().all()
            else:
                # 终止指定会话
                sessions_result = await self.db.execute(
                    select(UserSession)
                    .where(UserSession.id.in_(session_ids))
                    .where(UserSession.user_id == user_id)
                    .where(UserSession.status == SessionStatus.ACTIVE.value)
                )
                sessions = sessions_result.scalars().all()
            
            for session in sessions:
                session.status = SessionStatus.TERMINATED.value
                session.terminated_at = datetime.now()
                session.terminated_by = terminated_by
                
                # 清除缓存
                await redis_manager.delete(f"session:{session.session_token}")
                terminated_count += 1
            
            await self.db.commit()
            
            # 记录安全事件
            await self.log_security_event(
                user_id=user_id,
                event_type=SecurityEventType.LOGOUT,
                severity="info",
                details={
                    "terminated_sessions": terminated_count,
                    "terminate_all": terminate_all,
                    "terminated_by": terminated_by
                }
            )
            
            return terminated_count
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"终止会话失败: {str(e)}")
            raise
    
    # ==================== IP控制 ====================
    
    async def add_ip_whitelist(
        self,
        whitelist_data: IPWhitelistCreate,
        created_by: int
    ) -> IPWhitelistResponse:
        """添加IP白名单"""
        try:
            # 验证IP地址格式
            self._validate_ip_address(whitelist_data.ip_address)
            
            # 检查是否已存在
            existing = await self.db.execute(
                select(IPWhitelist).where(IPWhitelist.ip_address == whitelist_data.ip_address)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"IP地址 {whitelist_data.ip_address} 已在白名单中")
            
            whitelist = IPWhitelist(
                **whitelist_data.model_dump(),
                created_by=created_by
            )
            
            self.db.add(whitelist)
            await self.db.commit()
            await self.db.refresh(whitelist)
            
            return IPWhitelistResponse(
                id=whitelist.id,
                ip_address=whitelist.ip_address,
                ip_range=whitelist.ip_range,
                description=whitelist.description,
                user_id=whitelist.user_id,
                is_active=whitelist.is_active,
                expires_at=whitelist.expires_at,
                created_at=whitelist.created_at,
                created_by=whitelist.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"添加IP白名单失败: {str(e)}")
            raise
    
    async def add_ip_blacklist(
        self,
        blacklist_data: IPBlacklistCreate,
        created_by: int
    ) -> IPBlacklistResponse:
        """添加IP黑名单"""
        try:
            # 验证IP地址格式
            self._validate_ip_address(blacklist_data.ip_address)
            
            # 检查是否已存在
            existing = await self.db.execute(
                select(IPBlacklist).where(IPBlacklist.ip_address == blacklist_data.ip_address)
            )
            existing_blacklist = existing.scalar_one_or_none()
            
            if existing_blacklist:
                # 更新现有记录
                existing_blacklist.reason = blacklist_data.reason
                existing_blacklist.block_type = blacklist_data.block_type
                existing_blacklist.is_active = True
                existing_blacklist.expires_at = blacklist_data.expires_at
                existing_blacklist.updated_at = datetime.now()
                blacklist = existing_blacklist
            else:
                # 创建新记录
                blacklist = IPBlacklist(
                    **blacklist_data.model_dump(),
                    created_by=created_by
                )
                self.db.add(blacklist)
            
            await self.db.commit()
            await self.db.refresh(blacklist)
            
            # 记录安全事件
            await self.log_security_event(
                event_type=SecurityEventType.IP_BLOCKED,
                severity="warning",
                ip_address=blacklist_data.ip_address,
                details={
                    "reason": blacklist_data.reason,
                    "block_type": blacklist_data.block_type
                }
            )
            
            return IPBlacklistResponse(
                id=blacklist.id,
                ip_address=blacklist.ip_address,
                ip_range=blacklist.ip_range,
                reason=blacklist.reason,
                block_type=blacklist.block_type,
                failed_attempts=blacklist.failed_attempts,
                is_active=blacklist.is_active,
                expires_at=blacklist.expires_at,
                created_at=blacklist.created_at,
                created_by=blacklist.created_by
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"添加IP黑名单失败: {str(e)}")
            raise
    
    async def check_ip_access(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """检查IP访问权限"""
        try:
            # 检查黑名单
            blacklist_result = await self.db.execute(
                select(IPBlacklist)
                .where(IPBlacklist.ip_address == ip_address)
                .where(IPBlacklist.is_active == True)
                .where(or_(
                    IPBlacklist.expires_at.is_(None),
                    IPBlacklist.expires_at > datetime.now()
                ))
            )
            blacklist_entry = blacklist_result.scalar_one_or_none()
            
            if blacklist_entry:
                return False, f"IP地址被封禁: {blacklist_entry.reason}"
            
            # 检查白名单（如果启用白名单模式）
            whitelist_count = await self.db.execute(
                select(func.count(IPWhitelist.id)).where(IPWhitelist.is_active == True)
            )
            if whitelist_count.scalar() > 0:
                whitelist_result = await self.db.execute(
                    select(IPWhitelist)
                    .where(IPWhitelist.ip_address == ip_address)
                    .where(IPWhitelist.is_active == True)
                    .where(or_(
                        IPWhitelist.expires_at.is_(None),
                        IPWhitelist.expires_at > datetime.now()
                    ))
                )
                whitelist_entry = whitelist_result.scalar_one_or_none()
                
                if not whitelist_entry:
                    return False, "IP地址不在白名单中"
            
            return True, None
            
        except Exception as e:
            Logger.error(f"检查IP访问权限失败: {str(e)}")
            return False, "系统错误"
    
    # ==================== 安全事件记录 ====================
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: str = "info",
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_score: int = 0
    ) -> SecurityEvent:
        """记录安全事件"""
        try:
            event = SecurityEvent(
                user_id=user_id,
                event_type=event_type.value,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                details=details,
                risk_score=risk_score
            )
            
            self.db.add(event)
            await self.db.commit()
            await self.db.refresh(event)
            
            return event
            
        except Exception as e:
            Logger.error(f"记录安全事件失败: {str(e)}")
            raise
    
    # ==================== 辅助方法 ====================
    
    def _is_mobile_device(self, user_agent: str) -> bool:
        """检测是否为移动设备"""
        mobile_keywords = ['Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone']
        return any(keyword in user_agent for keyword in mobile_keywords)
    
    async def _is_trusted_device(self, user_id: int, device_fingerprint: str) -> bool:
        """检查设备是否受信任"""
        try:
            fingerprint_result = await self.db.execute(
                select(DeviceFingerprint)
                .where(DeviceFingerprint.user_id == user_id)
                .where(DeviceFingerprint.fingerprint_hash == device_fingerprint)
                .where(DeviceFingerprint.is_trusted == True)
            )
            return fingerprint_result.scalar_one_or_none() is not None
        except Exception:
            return False
    
    def _validate_ip_address(self, ip_address: str):
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            raise ValueError(f"无效的IP地址格式: {ip_address}")

    # ==================== 安全仪表板 ====================

    async def get_security_dashboard(self) -> SecurityDashboardResponse:
        """获取安全仪表板数据"""
        try:
            # 活跃会话数
            active_sessions_result = await self.db.execute(
                select(func.count(UserSession.id))
                .where(UserSession.status == SessionStatus.ACTIVE.value)
            )
            active_sessions = active_sessions_result.scalar() or 0

            # 24小时内失败登录次数
            yesterday = datetime.now() - timedelta(hours=24)
            failed_logins_result = await self.db.execute(
                select(func.count(SecurityEvent.id))
                .where(SecurityEvent.event_type == SecurityEventType.LOGIN_FAILED.value)
                .where(SecurityEvent.created_at >= yesterday)
            )
            failed_logins_24h = failed_logins_result.scalar() or 0

            # 被封禁IP数量
            blocked_ips_result = await self.db.execute(
                select(func.count(IPBlacklist.id))
                .where(IPBlacklist.is_active == True)
            )
            blocked_ips = blocked_ips_result.scalar() or 0

            # 24小时内安全事件数
            security_events_result = await self.db.execute(
                select(func.count(SecurityEvent.id))
                .where(SecurityEvent.created_at >= yesterday)
            )
            security_events_24h = security_events_result.scalar() or 0

            # 启用2FA的用户数
            two_factor_users_result = await self.db.execute(
                select(func.count(TwoFactorAuth.id))
                .where(TwoFactorAuth.is_enabled == True)
            )
            two_factor_enabled_users = two_factor_users_result.scalar() or 0

            # 可疑活动数量
            suspicious_activities_result = await self.db.execute(
                select(func.count(SecurityEvent.id))
                .where(SecurityEvent.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY.value)
                .where(SecurityEvent.is_resolved == False)
            )
            suspicious_activities = suspicious_activities_result.scalar() or 0

            # 最近安全事件
            recent_events_result = await self.db.execute(
                select(SecurityEvent)
                .order_by(desc(SecurityEvent.created_at))
                .limit(10)
            )
            recent_events = [
                SecurityEventResponse(
                    id=event.id,
                    user_id=event.user_id,
                    event_type=event.event_type,
                    severity=event.severity,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    session_id=event.session_id,
                    details=event.details,
                    risk_score=event.risk_score,
                    is_resolved=event.is_resolved,
                    resolved_at=event.resolved_at,
                    resolved_by=event.resolved_by,
                    created_at=event.created_at
                ) for event in recent_events_result.scalars().all()
            ]

            # 高风险IP列表
            top_risk_ips_result = await self.db.execute(
                select(SecurityEvent.ip_address, func.count(SecurityEvent.id).label('event_count'))
                .where(SecurityEvent.ip_address.isnot(None))
                .where(SecurityEvent.created_at >= yesterday)
                .group_by(SecurityEvent.ip_address)
                .order_by(desc('event_count'))
                .limit(5)
            )
            top_risk_ips = [
                {"ip_address": ip, "event_count": count}
                for ip, count in top_risk_ips_result.fetchall()
            ]

            return SecurityDashboardResponse(
                active_sessions=active_sessions,
                failed_logins_24h=failed_logins_24h,
                blocked_ips=blocked_ips,
                security_events_24h=security_events_24h,
                two_factor_enabled_users=two_factor_enabled_users,
                suspicious_activities=suspicious_activities,
                recent_events=recent_events,
                top_risk_ips=top_risk_ips
            )

        except Exception as e:
            Logger.error(f"获取安全仪表板数据失败: {str(e)}")
            raise

    # ==================== 安全审计 ====================

    async def generate_security_audit(self, audit_request: SecurityAuditRequest) -> SecurityAuditResponse:
        """生成安全审计报告"""
        try:
            # 构建查询条件
            query = select(SecurityEvent)

            if audit_request.start_date:
                query = query.where(SecurityEvent.created_at >= audit_request.start_date)
            if audit_request.end_date:
                query = query.where(SecurityEvent.created_at <= audit_request.end_date)
            if audit_request.event_types:
                event_type_values = [et.value for et in audit_request.event_types]
                query = query.where(SecurityEvent.event_type.in_(event_type_values))
            if audit_request.user_ids:
                query = query.where(SecurityEvent.user_id.in_(audit_request.user_ids))
            if audit_request.ip_addresses:
                query = query.where(SecurityEvent.ip_address.in_(audit_request.ip_addresses))
            if audit_request.severity_levels:
                query = query.where(SecurityEvent.severity.in_(audit_request.severity_levels))

            # 获取事件总数
            total_events_result = await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
            total_events = total_events_result.scalar() or 0

            # 按类型统计事件
            events_by_type_result = await self.db.execute(
                select(SecurityEvent.event_type, func.count(SecurityEvent.id))
                .select_from(query.subquery())
                .group_by(SecurityEvent.event_type)
            )
            events_by_type = dict(events_by_type_result.fetchall())

            # 按严重程度统计事件
            events_by_severity_result = await self.db.execute(
                select(SecurityEvent.severity, func.count(SecurityEvent.id))
                .select_from(query.subquery())
                .group_by(SecurityEvent.severity)
            )
            events_by_severity = dict(events_by_severity_result.fetchall())

            # 活跃用户排行
            top_users_result = await self.db.execute(
                select(SecurityEvent.user_id, func.count(SecurityEvent.id).label('event_count'))
                .select_from(query.subquery())
                .where(SecurityEvent.user_id.isnot(None))
                .group_by(SecurityEvent.user_id)
                .order_by(desc('event_count'))
                .limit(10)
            )
            top_users = [
                {"user_id": user_id, "event_count": count}
                for user_id, count in top_users_result.fetchall()
            ]

            # 活跃IP排行
            top_ips_result = await self.db.execute(
                select(SecurityEvent.ip_address, func.count(SecurityEvent.id).label('event_count'))
                .select_from(query.subquery())
                .where(SecurityEvent.ip_address.isnot(None))
                .group_by(SecurityEvent.ip_address)
                .order_by(desc('event_count'))
                .limit(10)
            )
            top_ips = [
                {"ip_address": ip, "event_count": count}
                for ip, count in top_ips_result.fetchall()
            ]

            # 时间线数据（按小时统计）
            timeline_result = await self.db.execute(
                select(
                    func.date_trunc('hour', SecurityEvent.created_at).label('hour'),
                    func.count(SecurityEvent.id).label('event_count')
                )
                .select_from(query.subquery())
                .group_by('hour')
                .order_by('hour')
            )
            timeline_data = [
                {"time": hour.isoformat(), "count": count}
                for hour, count in timeline_result.fetchall()
            ]

            # 风险分析
            high_risk_events = await self.db.execute(
                select(func.count(SecurityEvent.id))
                .select_from(query.subquery())
                .where(SecurityEvent.risk_score >= 70)
            )
            high_risk_count = high_risk_events.scalar() or 0

            risk_analysis = {
                "high_risk_events": high_risk_count,
                "risk_percentage": (high_risk_count / total_events * 100) if total_events > 0 else 0,
                "most_common_event": max(events_by_type.items(), key=lambda x: x[1])[0] if events_by_type else None
            }

            return SecurityAuditResponse(
                total_events=total_events,
                events_by_type=events_by_type,
                events_by_severity=events_by_severity,
                top_users=top_users,
                top_ips=top_ips,
                timeline_data=timeline_data,
                risk_analysis=risk_analysis
            )

        except Exception as e:
            Logger.error(f"生成安全审计报告失败: {str(e)}")
            raise

    # ==================== 批量操作 ====================

    async def bulk_ip_operation(self, operation: BulkIPOperation, created_by: int) -> Dict[str, Any]:
        """批量IP操作"""
        try:
            results = {
                "total": len(operation.ip_addresses),
                "success": 0,
                "failed": 0,
                "errors": []
            }

            for ip_address in operation.ip_addresses:
                try:
                    if operation.operation == "whitelist":
                        await self.add_ip_whitelist(
                            IPWhitelistCreate(
                                ip_address=ip_address,
                                description=operation.reason,
                                expires_at=operation.expires_at
                            ),
                            created_by=created_by
                        )
                    elif operation.operation == "blacklist":
                        await self.add_ip_blacklist(
                            IPBlacklistCreate(
                                ip_address=ip_address,
                                reason=operation.reason,
                                expires_at=operation.expires_at
                            ),
                            created_by=created_by
                        )
                    elif operation.operation == "remove_whitelist":
                        await self.db.execute(
                            delete(IPWhitelist).where(IPWhitelist.ip_address == ip_address)
                        )
                    elif operation.operation == "remove_blacklist":
                        await self.db.execute(
                            delete(IPBlacklist).where(IPBlacklist.ip_address == ip_address)
                        )

                    results["success"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "ip_address": ip_address,
                        "error": str(e)
                    })

            await self.db.commit()
            return results

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"批量IP操作失败: {str(e)}")
            raise

    # ==================== 密码安全 ====================

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        try:
            user = await self.db.get(User, user_id)
            if not user:
                raise ValueError("用户不存在")

            # 验证当前密码
            if not verify_password(current_password, user.hashed_password):
                raise ValueError("当前密码错误")

            # 检查密码历史
            password_history_result = await self.db.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user_id)
                .order_by(desc(PasswordHistory.created_at))
                .limit(5)  # 检查最近5个密码
            )

            new_password_hash = get_password_hash(new_password)
            for history in password_history_result.scalars().all():
                if verify_password(new_password, history.password_hash):
                    raise ValueError("不能使用最近使用过的密码")

            # 保存旧密码到历史记录
            password_history = PasswordHistory(
                user_id=user_id,
                password_hash=user.hashed_password
            )
            self.db.add(password_history)

            # 更新密码
            user.hashed_password = new_password_hash

            await self.db.commit()

            # 记录安全事件
            await self.log_security_event(
                user_id=user_id,
                event_type=SecurityEventType.PASSWORD_CHANGED,
                severity="info",
                details={"action": "password_changed"}
            )

            return True

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"修改密码失败: {str(e)}")
            raise
