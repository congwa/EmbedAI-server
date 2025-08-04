import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, delete
from sqlalchemy.orm import selectinload, joinedload

from app.models.rbac import (
    Permission, Role, UserGroup, UserSession, UserLoginLog, 
    UserSecuritySettings, role_permissions, user_roles, 
    user_group_members, group_roles
)
from app.models.user import User
from app.schemas.rbac import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    UserGroupCreate, UserGroupUpdate, UserGroupResponse,
    UserRoleAssignment, UserGroupMembership, BulkUserOperation,
    UserImportRequest, UserImportResult, EnhancedUserResponse,
    UserSessionResponse, UserLoginLogResponse, UserSecuritySettingsResponse
)
from app.core.logger import Logger
from app.core.security import get_password_hash, verify_password
from app.core.redis_manager import redis_manager

class RBACService:
    """RBAC服务
    
    提供基于角色的访问控制功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 权限管理 ====================
    
    async def create_permission(self, permission_data: PermissionCreate) -> PermissionResponse:
        """创建权限"""
        try:
            # 检查权限代码是否已存在
            existing = await self.db.execute(
                select(Permission).where(Permission.code == permission_data.code)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"权限代码 {permission_data.code} 已存在")
            
            permission = Permission(**permission_data.dict())
            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)
            
            return PermissionResponse(
                id=permission.id,
                name=permission.name,
                code=permission.code,
                description=permission.description,
                resource=permission.resource,
                action=permission.action,
                is_system=permission.is_system,
                is_active=permission.is_active,
                created_at=permission.created_at,
                updated_at=permission.updated_at
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建权限失败: {str(e)}")
            raise
    
    async def get_permissions(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        resource: Optional[str] = None
    ) -> List[PermissionResponse]:
        """获取权限列表"""
        try:
            query = select(Permission).order_by(Permission.resource, Permission.action)
            
            if is_active is not None:
                query = query.where(Permission.is_active == is_active)
            if resource:
                query = query.where(Permission.resource == resource)
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            permissions = result.scalars().all()
            
            return [
                PermissionResponse(
                    id=p.id,
                    name=p.name,
                    code=p.code,
                    description=p.description,
                    resource=p.resource,
                    action=p.action,
                    is_system=p.is_system,
                    is_active=p.is_active,
                    created_at=p.created_at,
                    updated_at=p.updated_at
                ) for p in permissions
            ]
            
        except Exception as e:
            Logger.error(f"获取权限列表失败: {str(e)}")
            raise
    
    async def update_permission(
        self, 
        permission_id: int, 
        permission_data: PermissionUpdate
    ) -> PermissionResponse:
        """更新权限"""
        try:
            permission = await self.db.get(Permission, permission_id)
            if not permission:
                raise ValueError("权限不存在")
            
            if permission.is_system:
                raise ValueError("系统权限不能修改")
            
            update_data = permission_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(permission, field, value)
            
            await self.db.commit()
            await self.db.refresh(permission)
            
            return PermissionResponse(
                id=permission.id,
                name=permission.name,
                code=permission.code,
                description=permission.description,
                resource=permission.resource,
                action=permission.action,
                is_system=permission.is_system,
                is_active=permission.is_active,
                created_at=permission.created_at,
                updated_at=permission.updated_at
            )
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"更新权限失败: {str(e)}")
            raise
    
    # ==================== 角色管理 ====================
    
    async def create_role(self, role_data: RoleCreate, created_by: int) -> RoleResponse:
        """创建角色"""
        try:
            # 检查角色代码是否已存在
            existing = await self.db.execute(
                select(Role).where(Role.code == role_data.code)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"角色代码 {role_data.code} 已存在")
            
            # 创建角色
            role_dict = role_data.dict(exclude={'permission_ids'})
            role = Role(**role_dict, created_by=created_by)
            self.db.add(role)
            await self.db.flush()
            
            # 分配权限
            if role_data.permission_ids:
                permissions = await self.db.execute(
                    select(Permission).where(Permission.id.in_(role_data.permission_ids))
                )
                role.permissions = permissions.scalars().all()
            
            await self.db.commit()
            await self.db.refresh(role, ['permissions'])
            
            return await self._build_role_response(role)
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建角色失败: {str(e)}")
            raise
    
    async def get_roles(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[RoleResponse]:
        """获取角色列表"""
        try:
            query = select(Role).options(selectinload(Role.permissions)).order_by(Role.priority.desc(), Role.name)
            
            if is_active is not None:
                query = query.where(Role.is_active == is_active)
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            roles = result.scalars().all()
            
            return [await self._build_role_response(role) for role in roles]
            
        except Exception as e:
            Logger.error(f"获取角色列表失败: {str(e)}")
            raise
    
    async def update_role(
        self, 
        role_id: int, 
        role_data: RoleUpdate
    ) -> RoleResponse:
        """更新角色"""
        try:
            role = await self.db.get(Role, role_id, options=[selectinload(Role.permissions)])
            if not role:
                raise ValueError("角色不存在")
            
            if role.is_system:
                raise ValueError("系统角色不能修改")
            
            # 更新基本信息
            update_data = role_data.dict(exclude_unset=True, exclude={'permission_ids'})
            for field, value in update_data.items():
                setattr(role, field, value)
            
            # 更新权限
            if role_data.permission_ids is not None:
                permissions = await self.db.execute(
                    select(Permission).where(Permission.id.in_(role_data.permission_ids))
                )
                role.permissions = permissions.scalars().all()
            
            await self.db.commit()
            await self.db.refresh(role, ['permissions'])
            
            return await self._build_role_response(role)
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"更新角色失败: {str(e)}")
            raise
    
    # ==================== 用户组管理 ====================
    
    async def create_user_group(
        self, 
        group_data: UserGroupCreate, 
        created_by: int
    ) -> UserGroupResponse:
        """创建用户组"""
        try:
            # 检查用户组代码是否已存在
            existing = await self.db.execute(
                select(UserGroup).where(UserGroup.code == group_data.code)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"用户组代码 {group_data.code} 已存在")
            
            # 创建用户组
            group_dict = group_data.dict(exclude={'role_ids', 'member_ids'})
            group = UserGroup(**group_dict, created_by=created_by)
            self.db.add(group)
            await self.db.flush()
            
            # 分配角色
            if group_data.role_ids:
                roles = await self.db.execute(
                    select(Role).where(Role.id.in_(group_data.role_ids))
                )
                group.roles = roles.scalars().all()
            
            # 添加成员
            if group_data.member_ids:
                members = await self.db.execute(
                    select(User).where(User.id.in_(group_data.member_ids))
                )
                group.members = members.scalars().all()
            
            await self.db.commit()
            await self.db.refresh(group, ['roles', 'members', 'parent'])
            
            return await self._build_user_group_response(group)
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"创建用户组失败: {str(e)}")
            raise
    
    async def get_user_groups(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        parent_id: Optional[int] = None
    ) -> List[UserGroupResponse]:
        """获取用户组列表"""
        try:
            query = select(UserGroup).options(
                selectinload(UserGroup.roles),
                selectinload(UserGroup.parent),
                selectinload(UserGroup.children)
            ).order_by(UserGroup.name)
            
            if is_active is not None:
                query = query.where(UserGroup.is_active == is_active)
            if parent_id is not None:
                query = query.where(UserGroup.parent_id == parent_id)
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            groups = result.scalars().all()
            
            return [await self._build_user_group_response(group) for group in groups]
            
        except Exception as e:
            Logger.error(f"获取用户组列表失败: {str(e)}")
            raise
    
    # ==================== 用户管理 ====================
    
    async def assign_user_roles(self, assignment: UserRoleAssignment) -> bool:
        """分配用户角色"""
        try:
            user = await self.db.get(User, assignment.user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 获取角色
            roles = await self.db.execute(
                select(Role).where(Role.id.in_(assignment.role_ids))
            )
            user.roles = roles.scalars().all()
            
            await self.db.commit()
            
            # 清除用户权限缓存
            await self._clear_user_permissions_cache(assignment.user_id)
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            Logger.error(f"分配用户角色失败: {str(e)}")
            raise
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限列表"""
        try:
            # 尝试从缓存获取
            cache_key = f"user_permissions:{user_id}"
            cached_permissions = await redis_manager.get(cache_key)
            if cached_permissions:
                return cached_permissions.split(',')
            
            # 从数据库获取用户直接角色权限
            direct_permissions = await self.db.execute(
                select(Permission.code).distinct().join(
                    role_permissions, Permission.id == role_permissions.c.permission_id
                ).join(
                    user_roles, role_permissions.c.role_id == user_roles.c.role_id
                ).where(user_roles.c.user_id == user_id)
            )
            
            # 从数据库获取用户组角色权限
            group_permissions = await self.db.execute(
                select(Permission.code).distinct().join(
                    role_permissions, Permission.id == role_permissions.c.permission_id
                ).join(
                    group_roles, role_permissions.c.role_id == group_roles.c.role_id
                ).join(
                    user_group_members, group_roles.c.group_id == user_group_members.c.group_id
                ).where(user_group_members.c.user_id == user_id)
            )
            
            # 合并权限
            all_permissions = set()
            all_permissions.update(p[0] for p in direct_permissions.fetchall())
            all_permissions.update(p[0] for p in group_permissions.fetchall())
            
            permissions_list = list(all_permissions)
            
            # 缓存权限（1小时）
            if permissions_list:
                await redis_manager.set(cache_key, ','.join(permissions_list), expire=3600)
            
            return permissions_list
            
        except Exception as e:
            Logger.error(f"获取用户权限失败: {str(e)}")
            return []
    
    async def check_user_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        try:
            permissions = await self.get_user_permissions(user_id)
            return permission_code in permissions
        except Exception:
            return False
    
    # ==================== 辅助方法 ====================
    
    async def _build_role_response(self, role: Role) -> RoleResponse:
        """构建角色响应对象"""
        # 获取用户数量
        user_count_result = await self.db.execute(
            select(func.count(user_roles.c.user_id)).where(user_roles.c.role_id == role.id)
        )
        user_count = user_count_result.scalar() or 0
        
        permissions = [
            PermissionResponse(
                id=p.id,
                name=p.name,
                code=p.code,
                description=p.description,
                resource=p.resource,
                action=p.action,
                is_system=p.is_system,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at
            ) for p in role.permissions
        ]
        
        return RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            priority=role.priority,
            created_at=role.created_at,
            updated_at=role.updated_at,
            created_by=role.created_by,
            permissions=permissions,
            user_count=user_count
        )
    
    async def _build_user_group_response(self, group: UserGroup) -> UserGroupResponse:
        """构建用户组响应对象"""
        # 获取成员数量
        member_count_result = await self.db.execute(
            select(func.count(user_group_members.c.user_id)).where(
                user_group_members.c.group_id == group.id
            )
        )
        member_count = member_count_result.scalar() or 0
        
        roles = [await self._build_role_response(role) for role in group.roles]
        
        parent = None
        if group.parent:
            parent = UserGroupResponse(
                id=group.parent.id,
                name=group.parent.name,
                code=group.parent.code,
                description=group.parent.description,
                parent_id=group.parent.parent_id,
                is_active=group.parent.is_active,
                created_at=group.parent.created_at,
                updated_at=group.parent.updated_at,
                created_by=group.parent.created_by,
                member_count=0,
                roles=[],
                children=[]
            )
        
        children = [
            UserGroupResponse(
                id=child.id,
                name=child.name,
                code=child.code,
                description=child.description,
                parent_id=child.parent_id,
                is_active=child.is_active,
                created_at=child.created_at,
                updated_at=child.updated_at,
                created_by=child.created_by,
                member_count=0,
                roles=[],
                children=[]
            ) for child in group.children
        ]
        
        return UserGroupResponse(
            id=group.id,
            name=group.name,
            code=group.code,
            description=group.description,
            parent_id=group.parent_id,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
            created_by=group.created_by,
            parent=parent,
            children=children,
            roles=roles,
            member_count=member_count
        )
    
    async def _clear_user_permissions_cache(self, user_id: int):
        """清除用户权限缓存"""
        try:
            cache_key = f"user_permissions:{user_id}"
            await redis_manager.delete(cache_key)
        except Exception as e:
            Logger.warning(f"清除用户权限缓存失败: {str(e)}")

    # ==================== 批量操作 ====================

    async def bulk_user_operation(self, operation: BulkUserOperation) -> Dict[str, Any]:
        """批量用户操作"""
        try:
            results = {
                "total": len(operation.user_ids),
                "success": 0,
                "failed": 0,
                "errors": []
            }

            for user_id in operation.user_ids:
                try:
                    if operation.operation == "activate":
                        await self._activate_user(user_id)
                    elif operation.operation == "deactivate":
                        await self._deactivate_user(user_id)
                    elif operation.operation == "delete":
                        await self._delete_user(user_id)
                    elif operation.operation == "assign_role":
                        role_ids = operation.data.get("role_ids", [])
                        await self.assign_user_roles(UserRoleAssignment(user_id=user_id, role_ids=role_ids))
                    elif operation.operation == "remove_role":
                        role_ids = operation.data.get("role_ids", [])
                        await self._remove_user_roles(user_id, role_ids)
                    elif operation.operation == "add_to_group":
                        group_ids = operation.data.get("group_ids", [])
                        await self._add_user_to_groups(user_id, group_ids)
                    elif operation.operation == "remove_from_group":
                        group_ids = operation.data.get("group_ids", [])
                        await self._remove_user_from_groups(user_id, group_ids)

                    results["success"] += 1

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "user_id": user_id,
                        "error": str(e)
                    })

            await self.db.commit()
            return results

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"批量用户操作失败: {str(e)}")
            raise

    async def import_users(self, import_request: UserImportRequest) -> UserImportResult:
        """批量导入用户"""
        try:
            result = UserImportResult(
                total_count=len(import_request.users),
                success_count=0,
                failed_count=0,
                errors=[],
                created_users=[]
            )

            for i, user_data in enumerate(import_request.users):
                try:
                    # 检查邮箱是否已存在
                    existing = await self.db.execute(
                        select(User).where(User.email == user_data.email)
                    )
                    if existing.scalar_one_or_none():
                        raise ValueError(f"邮箱 {user_data.email} 已存在")

                    # 创建用户
                    password = user_data.password or self._generate_random_password()
                    user = User(
                        email=user_data.email,
                        hashed_password=get_password_hash(password),
                        is_admin=user_data.is_admin,
                        is_active=True
                    )
                    self.db.add(user)
                    await self.db.flush()

                    # 分配角色
                    if user_data.role_codes:
                        roles = await self.db.execute(
                            select(Role).where(Role.code.in_(user_data.role_codes))
                        )
                        user.roles = roles.scalars().all()

                    # 添加到用户组
                    if user_data.group_codes:
                        groups = await self.db.execute(
                            select(UserGroup).where(UserGroup.code.in_(user_data.group_codes))
                        )
                        user.groups = groups.scalars().all()

                    result.created_users.append(user.id)
                    result.success_count += 1

                except Exception as e:
                    result.failed_count += 1
                    result.errors.append({
                        "row": i + 1,
                        "email": user_data.email,
                        "error": str(e)
                    })

            await self.db.commit()
            return result

        except Exception as e:
            await self.db.rollback()
            Logger.error(f"批量导入用户失败: {str(e)}")
            raise

    async def export_users_csv(self) -> str:
        """导出用户CSV"""
        try:
            # 获取用户数据
            users = await self.db.execute(
                select(User).options(
                    selectinload(User.roles),
                    selectinload(User.groups)
                ).order_by(User.email)
            )

            output = io.StringIO()
            writer = csv.writer(output)

            # 写入标题行
            writer.writerow([
                "ID", "邮箱", "是否管理员", "是否激活", "角色", "用户组", "创建时间"
            ])

            # 写入数据行
            for user in users.scalars().all():
                roles = ", ".join([role.name for role in user.roles])
                groups = ", ".join([group.name for group in user.groups])

                writer.writerow([
                    user.id,
                    user.email,
                    "是" if user.is_admin else "否",
                    "是" if user.is_active else "否",
                    roles,
                    groups,
                    user.created_at.strftime("%Y-%m-%d %H:%M:%S")
                ])

            return output.getvalue()

        except Exception as e:
            Logger.error(f"导出用户CSV失败: {str(e)}")
            raise

    # ==================== 私有辅助方法 ====================

    async def _activate_user(self, user_id: int):
        """激活用户"""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
        user.is_active = True

    async def _deactivate_user(self, user_id: int):
        """停用用户"""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
        user.is_active = False

    async def _delete_user(self, user_id: int):
        """删除用户"""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
        await self.db.delete(user)

    async def _remove_user_roles(self, user_id: int, role_ids: List[int]):
        """移除用户角色"""
        await self.db.execute(
            delete(user_roles).where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id.in_(role_ids)
                )
            )
        )
        await self._clear_user_permissions_cache(user_id)

    async def _add_user_to_groups(self, user_id: int, group_ids: List[int]):
        """添加用户到用户组"""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        groups = await self.db.execute(
            select(UserGroup).where(UserGroup.id.in_(group_ids))
        )
        existing_groups = set(group.id for group in user.groups)
        new_groups = [group for group in groups.scalars().all() if group.id not in existing_groups]
        user.groups.extend(new_groups)

        await self._clear_user_permissions_cache(user_id)

    async def _remove_user_from_groups(self, user_id: int, group_ids: List[int]):
        """从用户组移除用户"""
        await self.db.execute(
            delete(user_group_members).where(
                and_(
                    user_group_members.c.user_id == user_id,
                    user_group_members.c.group_id.in_(group_ids)
                )
            )
        )
        await self._clear_user_permissions_cache(user_id)

    def _generate_random_password(self) -> str:
        """生成随机密码"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(12))
