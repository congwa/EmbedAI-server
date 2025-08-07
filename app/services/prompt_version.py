from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime
import difflib

from app.models.prompt import PromptTemplate, PromptVersion
from app.models.user import User
from app.schemas.prompt import (
    PromptVersionCreate, PromptVersionResponse, PromptVersionList,
    PromptVersionCompareRequest, PromptVersionCompareResponse,
    PromptVersionRollbackRequest, PromptVariableDefinition
)
from app.core.logger import Logger


class PromptVersionService:
    """提示词版本管理服务类
    
    处理提示词模板版本控制相关的业务逻辑
    包括版本创建、发布、回滚、比较等功能
    """
    
    def __init__(self, db: AsyncSession):
        """初始化版本服务
        
        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db
    
    async def create_version(
        self,
        template_id: int,
        version_data: PromptVersionCreate,
        user_id: int
    ) -> PromptVersion:
        """创建新版本
        
        Args:
            template_id: 模板ID
            version_data: 版本创建数据
            user_id: 用户ID
            
        Returns:
            PromptVersion: 创建的版本对象
            
        Raises:
            HTTPException: 当创建失败时
        """
        try:
            Logger.info(f"用户 {user_id} 为模板 {template_id} 创建新版本")
            
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
            
            # 检查权限（只有所有者可以创建版本）
            if template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有模板所有者可以创建版本"
                )
            
            # 生成新版本号
            version_number = await self._generate_version_number(template_id)
            
            # 将之前的当前版本设为非当前版本
            await self.db.execute(
                select(PromptVersion).filter(
                    and_(
                        PromptVersion.template_id == template_id,
                        PromptVersion.is_current == True
                    )
                ).update({"is_current": False})
            )
            
            # 创建新版本
            db_version = PromptVersion(
                template_id=template_id,
                version_number=version_number,
                content=version_data.content,
                variables=[var.model_dump() for var in (version_data.variables or [])],
                change_log=version_data.change_log,
                is_published=False,
                is_current=True,
                created_by=user_id
            )
            
            self.db.add(db_version)
            await self.db.commit()
            await self.db.refresh(db_version)
            
            Logger.info(f"版本创建成功: ID={db_version.id}, 版本号={version_number}")
            return db_version
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"创建版本失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建版本失败: {str(e)}"
            )
    
    async def publish_version(self, version_id: int, user_id: int) -> PromptVersion:
        """发布版本
        
        Args:
            version_id: 版本ID
            user_id: 用户ID
            
        Returns:
            PromptVersion: 发布的版本对象
        """
        try:
            Logger.info(f"用户 {user_id} 发布版本: {version_id}")
            
            # 获取版本
            version_result = await self.db.execute(
                select(PromptVersion)
                .options(selectinload(PromptVersion.template))
                .filter(PromptVersion.id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="版本不存在"
                )
            
            # 检查权限
            if version.template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有模板所有者可以发布版本"
                )
            
            # 发布版本
            version.is_published = True
            version.published_at = datetime.now()
            
            # 更新模板内容为当前版本
            if version.is_current:
                version.template.content = version.content
                version.template.variables = version.variables
                version.template.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(version)
            
            Logger.info(f"版本发布成功: ID={version_id}")
            return version
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"发布版本失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"发布版本失败: {str(e)}"
            )
    
    async def rollback_version(
        self,
        template_id: int,
        rollback_request: PromptVersionRollbackRequest,
        user_id: int
    ) -> PromptTemplate:
        """回滚到指定版本
        
        Args:
            template_id: 模板ID
            rollback_request: 回滚请求
            user_id: 用户ID
            
        Returns:
            PromptTemplate: 回滚后的模板对象
        """
        try:
            Logger.info(f"用户 {user_id} 回滚模板 {template_id} 到版本 {rollback_request.version_id}")
            
            # 获取模板
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
                    detail="模板不存在"
                )
            
            # 检查权限
            if template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有模板所有者可以回滚版本"
                )
            
            # 获取目标版本
            target_version_result = await self.db.execute(
                select(PromptVersion).filter(
                    and_(
                        PromptVersion.id == rollback_request.version_id,
                        PromptVersion.template_id == template_id
                    )
                )
            )
            target_version = target_version_result.scalar_one_or_none()
            
            if not target_version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="目标版本不存在"
                )
            
            # 创建回滚版本
            new_version_number = await self._generate_version_number(template_id)
            
            # 将当前版本设为非当前版本
            await self.db.execute(
                select(PromptVersion).filter(
                    and_(
                        PromptVersion.template_id == template_id,
                        PromptVersion.is_current == True
                    )
                ).update({"is_current": False})
            )
            
            # 创建新的回滚版本
            rollback_version = PromptVersion(
                template_id=template_id,
                version_number=new_version_number,
                content=target_version.content,
                variables=target_version.variables,
                change_log=rollback_request.change_log or f"回滚到版本 {target_version.version_number}",
                is_published=True,
                is_current=True,
                created_by=user_id,
                published_at=datetime.now()
            )
            
            self.db.add(rollback_version)
            
            # 更新模板内容
            template.content = target_version.content
            template.variables = target_version.variables
            template.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(template)
            
            Logger.info(f"版本回滚成功: 模板 {template_id} 回滚到版本 {target_version.version_number}")
            return template
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"版本回滚失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"版本回滚失败: {str(e)}"
            )
    
    async def compare_versions(
        self,
        compare_request: PromptVersionCompareRequest
    ) -> PromptVersionCompareResponse:
        """比较版本差异
        
        Args:
            compare_request: 比较请求
            
        Returns:
            PromptVersionCompareResponse: 比较结果
        """
        try:
            Logger.info(f"比较版本: {compare_request.version1_id} vs {compare_request.version2_id}")
            
            # 获取两个版本
            version1_result = await self.db.execute(
                select(PromptVersion)
                .options(selectinload(PromptVersion.creator))
                .filter(PromptVersion.id == compare_request.version1_id)
            )
            version1 = version1_result.scalar_one_or_none()
            
            version2_result = await self.db.execute(
                select(PromptVersion)
                .options(selectinload(PromptVersion.creator))
                .filter(PromptVersion.id == compare_request.version2_id)
            )
            version2 = version2_result.scalar_one_or_none()
            
            if not version1 or not version2:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="版本不存在"
                )
            
            # 检查是否属于同一模板
            if version1.template_id != version2.template_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能比较同一模板的不同版本"
                )
            
            # 比较内容差异
            differences = await self._compare_content(version1, version2)
            
            # 构建响应
            response = PromptVersionCompareResponse(
                version1=PromptVersionResponse(
                    id=version1.id,
                    template_id=version1.template_id,
                    version_number=version1.version_number,
                    content=version1.content,
                    variables=version1.variables or [],
                    change_log=version1.change_log,
                    is_published=version1.is_published,
                    is_current=version1.is_current,
                    created_by=version1.created_by,
                    created_at=version1.created_at,
                    published_at=version1.published_at,
                    creator_email=version1.creator.email if version1.creator else None
                ),
                version2=PromptVersionResponse(
                    id=version2.id,
                    template_id=version2.template_id,
                    version_number=version2.version_number,
                    content=version2.content,
                    variables=version2.variables or [],
                    change_log=version2.change_log,
                    is_published=version2.is_published,
                    is_current=version2.is_current,
                    created_by=version2.created_by,
                    created_at=version2.created_at,
                    published_at=version2.published_at,
                    creator_email=version2.creator.email if version2.creator else None
                ),
                differences=differences
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"版本比较失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"版本比较失败: {str(e)}"
            )
    
    async def get_version_history(
        self,
        template_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PromptVersion], int]:
        """获取版本历史
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            Tuple[List[PromptVersion], int]: 版本列表和总数
        """
        try:
            Logger.info(f"用户 {user_id} 获取模板 {template_id} 的版本历史")
            
            # 验证模板存在和权限
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
                    detail="模板不存在"
                )
            
            # 检查权限（所有者或系统模板可以查看）
            if not template.is_system and template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有权限查看此模板的版本历史"
                )
            
            # 查询总数
            count_result = await self.db.execute(
                select(func.count(PromptVersion.id)).filter(
                    PromptVersion.template_id == template_id
                )
            )
            total = count_result.scalar()
            
            # 查询版本列表
            offset = (page - 1) * page_size
            result = await self.db.execute(
                select(PromptVersion)
                .options(selectinload(PromptVersion.creator))
                .filter(PromptVersion.template_id == template_id)
                .order_by(desc(PromptVersion.created_at))
                .offset(offset)
                .limit(page_size)
            )
            versions = result.scalars().all()
            
            return versions, total
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取版本历史失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取版本历史失败: {str(e)}"
            )
    
    async def _generate_version_number(self, template_id: int) -> str:
        """生成新版本号
        
        Args:
            template_id: 模板ID
            
        Returns:
            str: 新版本号
        """
        try:
            # 获取最新版本号
            latest_result = await self.db.execute(
                select(PromptVersion.version_number)
                .filter(PromptVersion.template_id == template_id)
                .order_by(desc(PromptVersion.created_at))
                .limit(1)
            )
            latest_version = latest_result.scalar_one_or_none()
            
            if not latest_version:
                return "v1.0.0"
            
            # 解析版本号并递增
            try:
                version_parts = latest_version.replace('v', '').split('.')
                if len(version_parts) == 3:
                    major, minor, patch = map(int, version_parts)
                    return f"v{major}.{minor}.{patch + 1}"
                else:
                    return "v1.0.1"
            except ValueError:
                return "v1.0.1"
                
        except Exception as e:
            Logger.error(f"生成版本号失败: {str(e)}")
            return "v1.0.0"
    
    async def _compare_content(self, version1: PromptVersion, version2: PromptVersion) -> Dict[str, Any]:
        """比较两个版本的内容差异
        
        Args:
            version1: 版本1
            version2: 版本2
            
        Returns:
            Dict[str, Any]: 差异信息
        """
        try:
            differences = {
                "content_changed": version1.content != version2.content,
                "variables_changed": version1.variables != version2.variables,
                "added_lines": [],
                "removed_lines": [],
                "modified_lines": []
            }
            
            # 比较内容差异
            if differences["content_changed"]:
                content1_lines = version1.content.splitlines()
                content2_lines = version2.content.splitlines()
                
                diff = list(difflib.unified_diff(
                    content1_lines,
                    content2_lines,
                    fromfile=f"版本 {version1.version_number}",
                    tofile=f"版本 {version2.version_number}",
                    lineterm=""
                ))
                
                for line in diff:
                    if line.startswith('+') and not line.startswith('+++'):
                        differences["added_lines"].append(line[1:])
                    elif line.startswith('-') and not line.startswith('---'):
                        differences["removed_lines"].append(line[1:])
            
            # 比较变量差异
            if differences["variables_changed"]:
                vars1 = {var.get('name'): var for var in (version1.variables or [])}
                vars2 = {var.get('name'): var for var in (version2.variables or [])}
                
                differences["added_variables"] = [
                    name for name in vars2.keys() if name not in vars1
                ]
                differences["removed_variables"] = [
                    name for name in vars1.keys() if name not in vars2
                ]
                differences["modified_variables"] = [
                    name for name in vars1.keys() 
                    if name in vars2 and vars1[name] != vars2[name]
                ]
            
            return differences
            
        except Exception as e:
            Logger.error(f"比较内容差异失败: {str(e)}")
            return {
                "content_changed": False,
                "variables_changed": False,
                "added_lines": [],
                "removed_lines": [],
                "modified_lines": []
            }