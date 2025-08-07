from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime
import re
import json

from app.models.prompt import PromptTemplate, PromptCategory, PromptVersion, PromptUsageLog
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.schemas.prompt import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse,
    PromptTemplateRenderRequest, PromptTemplateRenderResponse,
    PromptTemplateValidateRequest, PromptTemplateValidateResponse,
    PromptVariableDefinition, PromptCategoryCreate, PromptCategoryUpdate,
    PromptVersionCreate
)
from app.core.logger import Logger
from app.core.exceptions import ValidationError


class PromptService:
    """提示词服务类
    
    处理提示词模板相关的业务逻辑，包括模板的创建、查询、更新、删除、渲染和验证等操作
    """
    
    def __init__(self, db: AsyncSession):
        """初始化提示词服务
        
        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db
    
    async def create_template(self, template_data: PromptTemplateCreate, user_id: int) -> PromptTemplate:
        """创建提示词模板
        
        Args:
            template_data: 模板创建数据
            user_id: 创建者用户ID
            
        Returns:
            PromptTemplate: 创建的模板对象
            
        Raises:
            HTTPException: 当验证失败或创建失败时
        """
        try:
            Logger.info(f"用户 {user_id} 开始创建提示词模板: {template_data.name}")
            
            # 检查模板名称是否已存在（同一用户下）
            existing_template = await self.db.execute(
                select(PromptTemplate).filter(
                    and_(
                        PromptTemplate.name == template_data.name,
                        PromptTemplate.owner_id == user_id,
                        PromptTemplate.is_active == True
                    )
                )
            )
            if existing_template.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模板名称 '{template_data.name}' 已存在"
                )
            
            # 验证分类是否存在
            if template_data.category_id:
                category = await self.db.execute(
                    select(PromptCategory).filter(PromptCategory.id == template_data.category_id)
                )
                if not category.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"分类ID {template_data.category_id} 不存在"
                    )
            
            # 验证模板内容和变量
            validation_result = await self._validate_template_content(
                template_data.content, 
                template_data.variables or []
            )
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模板验证失败: {'; '.join(validation_result.errors)}"
                )
            
            # 创建模板
            db_template = PromptTemplate(
                name=template_data.name,
                description=template_data.description,
                category_id=template_data.category_id,
                content=template_data.content,
                variables=[var.model_dump() for var in (template_data.variables or [])],
                tags=template_data.tags or [],
                is_system=template_data.is_system,
                owner_id=user_id
            )
            
            self.db.add(db_template)
            await self.db.commit()
            await self.db.refresh(db_template)
            
            # 创建初始版本
            await self._create_initial_version(db_template, user_id)
            
            # 更新分类统计
            if template_data.category_id:
                await self._update_category_count(template_data.category_id)
            
            Logger.info(f"提示词模板创建成功: ID={db_template.id}, 名称={db_template.name}")
            return db_template
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"创建提示词模板失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建模板失败: {str(e)}"
            )
    
    async def get_template(self, template_id: int, user_id: int) -> PromptTemplate:
        """获取提示词模板详情
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
            
        Returns:
            PromptTemplate: 模板对象
            
        Raises:
            HTTPException: 当模板不存在或无权限时
        """
        try:
            # 查询模板（包含关联信息）
            result = await self.db.execute(
                select(PromptTemplate)
                .options(
                    selectinload(PromptTemplate.category),
                    selectinload(PromptTemplate.owner)
                )
                .filter(
                    and_(
                        PromptTemplate.id == template_id,
                        PromptTemplate.is_active == True
                    )
                )
            )
            template = result.scalar_one_or_none()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="模板不存在"
                )
            
            # 检查权限（所有者或系统模板可以查看）
            if not template.is_system and template.owner_id != user_id:
                # 这里可以扩展更复杂的权限检查逻辑
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有权限访问此模板"
                )
            
            return template
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取提示词模板失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取模板失败: {str(e)}"
            )
    
    async def list_templates(
        self, 
        user_id: int,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        is_system: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[PromptTemplate], int]:
        """列出提示词模板
        
        Args:
            user_id: 用户ID
            category_id: 分类ID筛选
            tags: 标签筛选
            search: 搜索关键词
            is_system: 是否系统模板
            page: 页码
            page_size: 每页大小
            
        Returns:
            Tuple[List[PromptTemplate], int]: 模板列表和总数
        """
        try:
            # 构建查询条件
            conditions = [PromptTemplate.is_active == True]
            
            # 权限过滤：用户只能看到自己的模板和系统模板
            conditions.append(
                or_(
                    PromptTemplate.owner_id == user_id,
                    PromptTemplate.is_system == True
                )
            )
            
            # 分类筛选
            if category_id is not None:
                conditions.append(PromptTemplate.category_id == category_id)
            
            # 系统模板筛选
            if is_system is not None:
                conditions.append(PromptTemplate.is_system == is_system)
            
            # 搜索筛选
            if search:
                search_condition = or_(
                    PromptTemplate.name.ilike(f"%{search}%"),
                    PromptTemplate.description.ilike(f"%{search}%")
                )
                conditions.append(search_condition)
            
            # 标签筛选
            if tags:
                for tag in tags:
                    conditions.append(PromptTemplate.tags.contains([tag]))
            
            # 查询总数
            count_result = await self.db.execute(
                select(func.count(PromptTemplate.id)).filter(and_(*conditions))
            )
            total = count_result.scalar()
            
            # 查询数据
            offset = (page - 1) * page_size
            result = await self.db.execute(
                select(PromptTemplate)
                .options(
                    selectinload(PromptTemplate.category),
                    selectinload(PromptTemplate.owner)
                )
                .filter(and_(*conditions))
                .order_by(desc(PromptTemplate.updated_at))
                .offset(offset)
                .limit(page_size)
            )
            templates = result.scalars().all()
            
            return templates, total
            
        except Exception as e:
            Logger.error(f"列出提示词模板失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取模板列表失败: {str(e)}"
            )
    
    async def update_template(
        self, 
        template_id: int, 
        template_data: PromptTemplateUpdate, 
        user_id: int
    ) -> PromptTemplate:
        """更新提示词模板
        
        Args:
            template_id: 模板ID
            template_data: 更新数据
            user_id: 用户ID
            
        Returns:
            PromptTemplate: 更新后的模板对象
        """
        try:
            # 获取现有模板
            template = await self.get_template(template_id, user_id)
            
            # 检查权限（只有所有者可以更新）
            if template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有模板所有者可以更新模板"
                )
            
            # 检查名称是否重复
            if template_data.name and template_data.name != template.name:
                existing = await self.db.execute(
                    select(PromptTemplate).filter(
                        and_(
                            PromptTemplate.name == template_data.name,
                            PromptTemplate.owner_id == user_id,
                            PromptTemplate.id != template_id,
                            PromptTemplate.is_active == True
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"模板名称 '{template_data.name}' 已存在"
                    )
            
            # 验证分类
            if template_data.category_id is not None:
                if template_data.category_id != template.category_id:
                    category = await self.db.execute(
                        select(PromptCategory).filter(PromptCategory.id == template_data.category_id)
                    )
                    if not category.scalar_one_or_none():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"分类ID {template_data.category_id} 不存在"
                        )
            
            # 验证内容和变量（如果有更新）
            content_to_validate = template_data.content or template.content
            variables_to_validate = template_data.variables or [
                PromptVariableDefinition(**var) for var in (template.variables or [])
            ]
            
            validation_result = await self._validate_template_content(
                content_to_validate, variables_to_validate
            )
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模板验证失败: {'; '.join(validation_result.errors)}"
                )
            
            # 记录是否需要创建新版本
            content_changed = (
                template_data.content and template_data.content != template.content
            ) or (
                template_data.variables is not None and 
                template_data.variables != [PromptVariableDefinition(**var) for var in (template.variables or [])]
            )
            
            # 更新模板
            old_category_id = template.category_id
            update_data = template_data.model_dump(exclude_unset=True)
            
            # 处理变量数据
            if 'variables' in update_data and update_data['variables'] is not None:
                update_data['variables'] = [var.model_dump() for var in update_data['variables']]
            
            for field, value in update_data.items():
                setattr(template, field, value)
            
            template.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(template)
            
            # 如果内容发生变化，创建新版本
            if content_changed:
                await self._create_version_from_template(template, user_id, "模板更新")
            
            # 更新分类统计
            if old_category_id != template.category_id:
                if old_category_id:
                    await self._update_category_count(old_category_id)
                if template.category_id:
                    await self._update_category_count(template.category_id)
            
            Logger.info(f"提示词模板更新成功: ID={template.id}")
            return template
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"更新提示词模板失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新模板失败: {str(e)}"
            )
    
    async def delete_template(self, template_id: int, user_id: int) -> None:
        """删除提示词模板（软删除）
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        """
        try:
            # 获取模板
            template = await self.get_template(template_id, user_id)
            
            # 检查权限
            if template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有模板所有者可以删除模板"
                )
            
            # 软删除
            template.is_active = False
            template.updated_at = datetime.now()
            
            await self.db.commit()
            
            # 更新分类统计
            if template.category_id:
                await self._update_category_count(template.category_id)
            
            Logger.info(f"提示词模板删除成功: ID={template_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"删除提示词模板失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除模板失败: {str(e)}"
            ) 
   
    async def render_template(
        self, 
        template_id: int, 
        variables: Dict[str, Any], 
        user_id: int
    ) -> PromptTemplateRenderResponse:
        """渲染提示词模板
        
        Args:
            template_id: 模板ID
            variables: 变量值映射
            user_id: 用户ID
            
        Returns:
            PromptTemplateRenderResponse: 渲染结果
        """
        try:
            # 获取模板
            template = await self.get_template(template_id, user_id)
            
            # 解析变量定义
            variable_definitions = [
                PromptVariableDefinition(**var) for var in (template.variables or [])
            ]
            
            # 检查必需变量
            missing_variables = []
            variables_used = {}
            
            for var_def in variable_definitions:
                if var_def.required and var_def.name not in variables:
                    if var_def.default is not None:
                        variables_used[var_def.name] = var_def.default
                    else:
                        missing_variables.append(var_def.name)
                else:
                    variables_used[var_def.name] = variables.get(var_def.name, var_def.default)
            
            if missing_variables:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"缺少必需变量: {', '.join(missing_variables)}"
                )
            
            # 渲染模板
            rendered_content = template.content
            for var_name, var_value in variables_used.items():
                if var_value is not None:
                    # 处理不同类型的变量值
                    if isinstance(var_value, (dict, list)):
                        var_str = json.dumps(var_value, ensure_ascii=False)
                    else:
                        var_str = str(var_value)
                    
                    rendered_content = rendered_content.replace(f"{{{{{var_name}}}}}", var_str)
            
            # 记录使用日志
            await self._log_template_usage(
                template_id=template_id,
                user_id=user_id,
                variables_used=variables_used,
                rendered_content=rendered_content,
                success=True
            )
            
            # 更新使用统计
            template.usage_count += 1
            template.last_used_at = datetime.now()
            await self.db.commit()
            
            return PromptTemplateRenderResponse(
                rendered_content=rendered_content,
                variables_used=variables_used,
                missing_variables=[]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"渲染提示词模板失败: {str(e)}")
            # 记录失败日志
            await self._log_template_usage(
                template_id=template_id,
                user_id=user_id,
                variables_used=variables,
                success=False,
                error_message=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"渲染模板失败: {str(e)}"
            )
    
    async def validate_template(
        self, 
        content: str, 
        variables: List[PromptVariableDefinition]
    ) -> PromptTemplateValidateResponse:
        """验证提示词模板
        
        Args:
            content: 模板内容
            variables: 变量定义列表
            
        Returns:
            PromptTemplateValidateResponse: 验证结果
        """
        return await self._validate_template_content(content, variables)
    
    # 私有辅助方法
    
    async def _validate_template_content(
        self, 
        content: str, 
        variables: List[PromptVariableDefinition]
    ) -> PromptTemplateValidateResponse:
        """验证模板内容和变量定义
        
        Args:
            content: 模板内容
            variables: 变量定义列表
            
        Returns:
            PromptTemplateValidateResponse: 验证结果
        """
        errors = []
        warnings = []
        
        # 从内容中提取变量
        extracted_variables = self._extract_variables_from_content(content)
        
        # 获取定义的变量名
        defined_variables = [var.name for var in variables]
        
        # 检查未定义的变量
        undefined_variables = [var for var in extracted_variables if var not in defined_variables]
        if undefined_variables:
            errors.append(f"以下变量在内容中使用但未定义: {', '.join(undefined_variables)}")
        
        # 检查未使用的变量
        unused_variables = [var for var in defined_variables if var not in extracted_variables]
        if unused_variables:
            warnings.append(f"以下变量已定义但未在内容中使用: {', '.join(unused_variables)}")
        
        # 检查变量名格式
        for var in variables:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var.name):
                errors.append(f"变量名 '{var.name}' 格式不正确，只能包含字母、数字和下划线，且不能以数字开头")
        
        # 检查内容长度
        if len(content) > 50000:  # 50KB限制
            warnings.append("模板内容过长，可能影响性能")
        
        # 检查变量数量
        if len(variables) > 50:
            warnings.append("变量数量过多，建议简化模板结构")
        
        is_valid = len(errors) == 0
        
        return PromptTemplateValidateResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            extracted_variables=extracted_variables,
            undefined_variables=undefined_variables,
            unused_variables=unused_variables
        )
    
    def _extract_variables_from_content(self, content: str) -> List[str]:
        """从模板内容中提取变量名
        
        Args:
            content: 模板内容
            
        Returns:
            List[str]: 变量名列表
        """
        # 匹配 {{variable_name}} 格式的变量
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, content)
        return list(set(matches))  # 去重
    
    async def _create_initial_version(self, template: PromptTemplate, user_id: int) -> None:
        """为新模板创建初始版本
        
        Args:
            template: 模板对象
            user_id: 用户ID
        """
        version = PromptVersion(
            template_id=template.id,
            version_number="v1.0.0",
            content=template.content,
            variables=template.variables,
            change_log="初始版本",
            is_published=True,
            is_current=True,
            created_by=user_id
        )
        
        self.db.add(version)
        await self.db.commit()
    
    async def _create_version_from_template(
        self, 
        template: PromptTemplate, 
        user_id: int, 
        change_log: str
    ) -> None:
        """从模板创建新版本
        
        Args:
            template: 模板对象
            user_id: 用户ID
            change_log: 变更说明
        """
        # 获取最新版本号
        latest_version = await self.db.execute(
            select(PromptVersion)
            .filter(PromptVersion.template_id == template.id)
            .order_by(desc(PromptVersion.created_at))
            .limit(1)
        )
        latest = latest_version.scalar_one_or_none()
        
        # 生成新版本号
        if latest:
            # 简单的版本号递增逻辑
            version_parts = latest.version_number.replace('v', '').split('.')
            if len(version_parts) == 3:
                major, minor, patch = map(int, version_parts)
                new_version = f"v{major}.{minor}.{patch + 1}"
            else:
                new_version = "v1.0.1"
        else:
            new_version = "v1.0.0"
        
        # 将之前的版本设为非当前版本
        if latest:
            latest.is_current = False
        
        # 创建新版本
        version = PromptVersion(
            template_id=template.id,
            version_number=new_version,
            content=template.content,
            variables=template.variables,
            change_log=change_log,
            is_published=True,
            is_current=True,
            created_by=user_id
        )
        
        self.db.add(version)
        await self.db.commit()
    
    async def _update_category_count(self, category_id: int) -> None:
        """更新分类的模板数量统计
        
        Args:
            category_id: 分类ID
        """
        try:
            # 统计该分类下的活跃模板数量
            count_result = await self.db.execute(
                select(func.count(PromptTemplate.id)).filter(
                    and_(
                        PromptTemplate.category_id == category_id,
                        PromptTemplate.is_active == True
                    )
                )
            )
            count = count_result.scalar()
            
            # 更新分类统计
            category_result = await self.db.execute(
                select(PromptCategory).filter(PromptCategory.id == category_id)
            )
            category = category_result.scalar_one_or_none()
            
            if category:
                category.template_count = count
                await self.db.commit()
                
        except Exception as e:
            Logger.error(f"更新分类统计失败: {str(e)}")
    
    async def _log_template_usage(
        self,
        template_id: int,
        user_id: int,
        variables_used: Dict[str, Any],
        rendered_content: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        kb_id: Optional[int] = None,
        query: Optional[str] = None,
        execution_time: Optional[float] = None,
        response_quality: Optional[float] = None,
        token_count: Optional[int] = None,
        cost: Optional[float] = None
    ) -> None:
        """记录模板使用日志
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
            variables_used: 使用的变量
            rendered_content: 渲染后的内容
            success: 是否成功
            error_message: 错误信息
            kb_id: 知识库ID
            query: 查询内容
            execution_time: 执行时间
            response_quality: 响应质量
            token_count: token数量
            cost: 成本
        """
        try:
            usage_log = PromptUsageLog(
                template_id=template_id,
                user_id=user_id,
                kb_id=kb_id,
                query=query,
                variables_used=variables_used,
                rendered_content=rendered_content,
                response_quality=response_quality,
                execution_time=execution_time,
                token_count=token_count,
                cost=cost,
                success=success,
                error_message=error_message
            )
            
            self.db.add(usage_log)
            await self.db.commit()
            
        except Exception as e:
            Logger.error(f"记录模板使用日志失败: {str(e)}")

class PromptCategoryService:
    """提示词分类服务类
    
    处理提示词分类相关的业务逻辑，包括分类的创建、查询、更新、删除等操作
    """
    
    def __init__(self, db: AsyncSession):
        """初始化分类服务
        
        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db
    
    async def create_category(self, category_data: 'PromptCategoryCreate') -> PromptCategory:
        """创建提示词分类
        
        Args:
            category_data: 分类创建数据
            
        Returns:
            PromptCategory: 创建的分类对象
            
        Raises:
            HTTPException: 当验证失败或创建失败时
        """
        try:
            Logger.info(f"开始创建提示词分类: {category_data.name}")
            
            # 检查分类名称是否已存在（同一父分类下）
            existing_category = await self.db.execute(
                select(PromptCategory).filter(
                    and_(
                        PromptCategory.name == category_data.name,
                        PromptCategory.parent_id == category_data.parent_id,
                        PromptCategory.is_active == True
                    )
                )
            )
            if existing_category.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"分类名称 '{category_data.name}' 在此层级下已存在"
                )
            
            # 验证父分类是否存在
            if category_data.parent_id:
                parent_category = await self.db.execute(
                    select(PromptCategory).filter(
                        and_(
                            PromptCategory.id == category_data.parent_id,
                            PromptCategory.is_active == True
                        )
                    )
                )
                if not parent_category.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"父分类ID {category_data.parent_id} 不存在"
                    )
            
            # 创建分类
            db_category = PromptCategory(
                name=category_data.name,
                description=category_data.description,
                parent_id=category_data.parent_id,
                sort_order=category_data.sort_order
            )
            
            self.db.add(db_category)
            await self.db.commit()
            await self.db.refresh(db_category)
            
            Logger.info(f"提示词分类创建成功: ID={db_category.id}, 名称={db_category.name}")
            return db_category
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"创建提示词分类失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建分类失败: {str(e)}"
            )
    
    async def get_category(self, category_id: int) -> PromptCategory:
        """获取分类详情
        
        Args:
            category_id: 分类ID
            
        Returns:
            PromptCategory: 分类对象
            
        Raises:
            HTTPException: 当分类不存在时
        """
        try:
            result = await self.db.execute(
                select(PromptCategory)
                .options(selectinload(PromptCategory.parent))
                .filter(
                    and_(
                        PromptCategory.id == category_id,
                        PromptCategory.is_active == True
                    )
                )
            )
            category = result.scalar_one_or_none()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分类不存在"
                )
            
            return category
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取提示词分类失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取分类失败: {str(e)}"
            )
    
    async def list_categories(
        self, 
        parent_id: Optional[int] = None,
        include_children: bool = False
    ) -> List[PromptCategory]:
        """列出分类
        
        Args:
            parent_id: 父分类ID，None表示获取根分类
            include_children: 是否包含子分类
            
        Returns:
            List[PromptCategory]: 分类列表
        """
        try:
            # 构建查询条件
            conditions = [PromptCategory.is_active == True]
            
            if parent_id is None:
                conditions.append(PromptCategory.parent_id.is_(None))
            else:
                conditions.append(PromptCategory.parent_id == parent_id)
            
            # 查询分类
            result = await self.db.execute(
                select(PromptCategory)
                .filter(and_(*conditions))
                .order_by(PromptCategory.sort_order, PromptCategory.name)
            )
            categories = result.scalars().all()
            
            # 如果需要包含子分类，递归获取
            if include_children:
                for category in categories:
                    category.children = await self.list_categories(
                        parent_id=category.id, 
                        include_children=True
                    )
            
            return categories
            
        except Exception as e:
            Logger.error(f"列出提示词分类失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取分类列表失败: {str(e)}"
            )
    
    async def get_category_tree(self) -> List[PromptCategory]:
        """获取完整的分类树
        
        Returns:
            List[PromptCategory]: 根分类列表（包含所有子分类）
        """
        return await self.list_categories(parent_id=None, include_children=True)
    
    async def update_category(
        self, 
        category_id: int, 
        category_data: 'PromptCategoryUpdate'
    ) -> PromptCategory:
        """更新分类
        
        Args:
            category_id: 分类ID
            category_data: 更新数据
            
        Returns:
            PromptCategory: 更新后的分类对象
        """
        try:
            # 获取现有分类
            category = await self.get_category(category_id)
            
            # 检查名称是否重复
            if category_data.name and category_data.name != category.name:
                existing = await self.db.execute(
                    select(PromptCategory).filter(
                        and_(
                            PromptCategory.name == category_data.name,
                            PromptCategory.parent_id == (category_data.parent_id or category.parent_id),
                            PromptCategory.id != category_id,
                            PromptCategory.is_active == True
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"分类名称 '{category_data.name}' 在此层级下已存在"
                    )
            
            # 验证父分类
            if category_data.parent_id is not None and category_data.parent_id != category.parent_id:
                # 检查是否会形成循环引用
                if await self._would_create_cycle(category_id, category_data.parent_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="不能将分类移动到其子分类下，这会形成循环引用"
                    )
                
                # 验证新父分类是否存在
                if category_data.parent_id:
                    parent = await self.db.execute(
                        select(PromptCategory).filter(
                            and_(
                                PromptCategory.id == category_data.parent_id,
                                PromptCategory.is_active == True
                            )
                        )
                    )
                    if not parent.scalar_one_or_none():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"父分类ID {category_data.parent_id} 不存在"
                        )
            
            # 更新分类
            update_data = category_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(category, field, value)
            
            category.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(category)
            
            Logger.info(f"提示词分类更新成功: ID={category.id}")
            return category
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"更新提示词分类失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新分类失败: {str(e)}"
            )
    
    async def delete_category(self, category_id: int) -> None:
        """删除分类（软删除）
        
        Args:
            category_id: 分类ID
        """
        try:
            # 获取分类
            category = await self.get_category(category_id)
            
            # 检查是否有子分类
            children = await self.db.execute(
                select(PromptCategory).filter(
                    and_(
                        PromptCategory.parent_id == category_id,
                        PromptCategory.is_active == True
                    )
                )
            )
            if children.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能删除包含子分类的分类，请先删除或移动子分类"
                )
            
            # 检查是否有关联的模板
            templates = await self.db.execute(
                select(PromptTemplate).filter(
                    and_(
                        PromptTemplate.category_id == category_id,
                        PromptTemplate.is_active == True
                    )
                )
            )
            if templates.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能删除包含模板的分类，请先删除或移动模板"
                )
            
            # 软删除
            category.is_active = False
            category.updated_at = datetime.now()
            
            await self.db.commit()
            
            Logger.info(f"提示词分类删除成功: ID={category_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"删除提示词分类失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除分类失败: {str(e)}"
            )
    
    async def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门标签
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 标签列表，包含标签名和使用次数
        """
        try:
            # 查询所有活跃模板的标签
            result = await self.db.execute(
                select(PromptTemplate.tags).filter(
                    and_(
                        PromptTemplate.is_active == True,
                        PromptTemplate.tags.is_not(None)
                    )
                )
            )
            
            # 统计标签使用次数
            tag_counts = {}
            for tags_row in result.scalars():
                if tags_row:
                    for tag in tags_row:
                        if tag and tag.strip():
                            tag = tag.strip()
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # 按使用次数排序
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            
            # 返回前N个标签
            return [
                {"tag": tag, "count": count} 
                for tag, count in sorted_tags[:limit]
            ]
            
        except Exception as e:
            Logger.error(f"获取热门标签失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取标签失败: {str(e)}"
            )
    
    async def search_tags(self, query: str, limit: int = 10) -> List[str]:
        """搜索标签（用于自动补全）
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            List[str]: 匹配的标签列表
        """
        try:
            if not query or len(query.strip()) < 1:
                return []
            
            query = query.strip().lower()
            
            # 查询所有活跃模板的标签
            result = await self.db.execute(
                select(PromptTemplate.tags).filter(
                    and_(
                        PromptTemplate.is_active == True,
                        PromptTemplate.tags.is_not(None)
                    )
                )
            )
            
            # 收集匹配的标签
            matching_tags = set()
            for tags_row in result.scalars():
                if tags_row:
                    for tag in tags_row:
                        if tag and tag.strip() and query in tag.lower():
                            matching_tags.add(tag.strip())
            
            # 返回匹配的标签（按字母顺序排序）
            return sorted(list(matching_tags))[:limit]
            
        except Exception as e:
            Logger.error(f"搜索标签失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"搜索标签失败: {str(e)}"
            )
    
    # 私有辅助方法
    
    async def _would_create_cycle(self, category_id: int, new_parent_id: int) -> bool:
        """检查移动分类是否会创建循环引用
        
        Args:
            category_id: 要移动的分类ID
            new_parent_id: 新的父分类ID
            
        Returns:
            bool: 是否会创建循环引用
        """
        if not new_parent_id:
            return False
        
        # 获取新父分类的所有祖先分类
        current_id = new_parent_id
        ancestors = set()
        
        while current_id:
            if current_id == category_id:
                return True  # 发现循环
            
            if current_id in ancestors:
                break  # 避免无限循环
            
            ancestors.add(current_id)
            
            # 获取父分类
            result = await self.db.execute(
                select(PromptCategory.parent_id).filter(PromptCategory.id == current_id)
            )
            parent_row = result.first()
            current_id = parent_row[0] if parent_row else None
        
        return False
class PromptVersionService:
    """提示词版本管理服务类
    
    处理提示词模板版本相关的业务逻辑，包括版本的创建、发布、回滚、比较等操作
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
        version_data: 'PromptVersionCreate', 
        user_id: int
    ) -> PromptVersion:
        """创建新版本
        
        Args:
            template_id: 模板ID
            version_data: 版本创建数据
            user_id: 创建者用户ID
            
        Returns:
            PromptVersion: 创建的版本对象
        """
        try:
            Logger.info(f"用户 {user_id} 开始为模板 {template_id} 创建新版本")
            
            # 验证模板是否存在且用户有权限
            template_result = await self.db.execute(
                select(PromptTemplate).filter(
                    and_(
                        PromptTemplate.id == template_id,
                        PromptTemplate.is_active == True,
                        PromptTemplate.owner_id == user_id
                    )
                )
            )
            template = template_result.scalar_one_or_none()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="模板不存在或无权限"
                )
            
            # 验证版本内容和变量
            from app.services.prompt import PromptService
            prompt_service = PromptService(self.db)
            validation_result = await prompt_service._validate_template_content(
                version_data.content, 
                version_data.variables or []
            )
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"版本验证失败: {'; '.join(validation_result.errors)}"
                )
            
            # 生成版本号
            version_number = await self._generate_version_number(template_id)
            
            # 将当前版本设为非当前版本
            await self.db.execute(
                PromptVersion.__table__.update()
                .where(
                    and_(
                        PromptVersion.template_id == template_id,
                        PromptVersion.is_current == True
                    )
                )
                .values(is_current=False)
            )
            
            # 创建新版本
            db_version = PromptVersion(
                template_id=template_id,
                version_number=version_number,
                content=version_data.content,
                variables=[var.model_dump() for var in (version_data.variables or [])],
                change_log=version_data.change_log,
                is_published=False,  # 新版本默认未发布
                is_current=True,     # 设为当前版本
                created_by=user_id
            )
            
            self.db.add(db_version)
            await self.db.commit()
            await self.db.refresh(db_version)
            
            # 同步更新模板内容
            template.content = version_data.content
            template.variables = [var.model_dump() for var in (version_data.variables or [])]
            template.updated_at = datetime.now()
            await self.db.commit()
            
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
            # 获取版本信息
            result = await self.db.execute(
                select(PromptVersion)
                .options(selectinload(PromptVersion.template))
                .filter(PromptVersion.id == version_id)
            )
            version = result.scalar_one_or_none()
            
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
            
            if version.is_published:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="版本已经发布"
                )
            
            # 发布版本
            version.is_published = True
            version.published_at = datetime.now()
            
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
    
    async def get_version_history(self, template_id: int, user_id: int) -> List[PromptVersion]:
        """获取版本历史
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
            
        Returns:
            List[PromptVersion]: 版本列表
        """
        try:
            # 验证模板权限
            template_result = await self.db.execute(
                select(PromptTemplate).filter(
                    and_(
                        PromptTemplate.id == template_id,
                        PromptTemplate.is_active == True,
                        or_(
                            PromptTemplate.owner_id == user_id,
                            PromptTemplate.is_system == True
                        )
                    )
                )
            )
            template = template_result.scalar_one_or_none()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="模板不存在或无权限"
                )
            
            # 获取版本历史
            result = await self.db.execute(
                select(PromptVersion)
                .options(selectinload(PromptVersion.creator))
                .filter(PromptVersion.template_id == template_id)
                .order_by(desc(PromptVersion.created_at))
            )
            versions = result.scalars().all()
            
            return versions
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取版本历史失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取版本历史失败: {str(e)}"
            )
    
    async def get_version(self, version_id: int, user_id: int) -> PromptVersion:
        """获取版本详情
        
        Args:
            version_id: 版本ID
            user_id: 用户ID
            
        Returns:
            PromptVersion: 版本对象
        """
        try:
            result = await self.db.execute(
                select(PromptVersion)
                .options(
                    selectinload(PromptVersion.template),
                    selectinload(PromptVersion.creator)
                )
                .filter(PromptVersion.id == version_id)
            )
            version = result.scalar_one_or_none()
            
            if not version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="版本不存在"
                )
            
            # 检查权限
            if not version.template.is_system and version.template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="没有权限访问此版本"
                )
            
            return version
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"获取版本详情失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取版本详情失败: {str(e)}"
            )
    
    # 私有辅助方法
    
    async def _generate_version_number(self, template_id: int) -> str:
        """生成版本号
        
        Args:
            template_id: 模板ID
            
        Returns:
            str: 新的版本号
        """
        # 获取最新版本
        result = await self.db.execute(
            select(PromptVersion.version_number)
            .filter(PromptVersion.template_id == template_id)
            .order_by(desc(PromptVersion.created_at))
            .limit(1)
        )
        latest_version = result.scalar_one_or_none()
        
        if not latest_version:
            return "v1.0.0"
        
        # 解析版本号并递增
        try:
            version_str = latest_version.replace('v', '')
            parts = version_str.split('.')
            
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                # 简单递增patch版本
                return f"v{major}.{minor}.{patch + 1}"
            else:
                # 如果版本号格式不标准，生成新的
                return "v1.0.1"
                
        except (ValueError, AttributeError):
            # 如果解析失败，生成新的版本号
            return "v1.0.1"    

    async def compare_versions(
        self, 
        version1_id: int, 
        version2_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """比较版本差异
        
        Args:
            version1_id: 版本1的ID
            version2_id: 版本2的ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 版本比较结果
        """
        try:
            # 获取两个版本
            version1 = await self.get_version(version1_id, user_id)
            version2 = await self.get_version(version2_id, user_id)
            
            # 检查是否属于同一模板
            if version1.template_id != version2.template_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能比较同一模板的不同版本"
                )
            
            # 比较内容差异
            content_changed = version1.content != version2.content
            variables_changed = version1.variables != version2.variables
            
            differences = {
                "content_changed": content_changed,
                "variables_changed": variables_changed,
                "added_lines": [],
                "removed_lines": [],
                "modified_lines": []
            }
            
            # 如果内容发生变化，进行详细的行级比较
            if content_changed:
                differences.update(
                    self._compare_text_content(version1.content, version2.content)
                )
            
            # 比较变量差异
            if variables_changed:
                differences["variable_differences"] = self._compare_variables(
                    version1.variables or [], 
                    version2.variables or []
                )
            
            return {
                "version1": version1,
                "version2": version2,
                "differences": differences
            }
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"比较版本失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"比较版本失败: {str(e)}"
            )
    
    async def rollback_version(
        self, 
        template_id: int, 
        target_version_id: int, 
        user_id: int,
        change_log: Optional[str] = None
    ) -> PromptTemplate:
        """回滚到指定版本
        
        Args:
            template_id: 模板ID
            target_version_id: 目标版本ID
            user_id: 用户ID
            change_log: 回滚说明
            
        Returns:
            PromptTemplate: 更新后的模板对象
        """
        try:
            Logger.info(f"用户 {user_id} 开始回滚模板 {template_id} 到版本 {target_version_id}")
            
            # 获取目标版本
            target_version = await self.get_version(target_version_id, user_id)
            
            # 验证版本属于指定模板
            if target_version.template_id != template_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="版本不属于指定模板"
                )
            
            # 检查权限
            if target_version.template.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有模板所有者可以回滚版本"
                )
            
            # 检查目标版本是否已发布
            if not target_version.is_published:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能回滚到已发布的版本"
                )
            
            # 创建回滚版本（基于目标版本的内容）
            rollback_version_number = await self._generate_version_number(template_id)
            rollback_change_log = change_log or f"回滚到版本 {target_version.version_number}"
            
            # 将当前版本设为非当前版本
            await self.db.execute(
                PromptVersion.__table__.update()
                .where(
                    and_(
                        PromptVersion.template_id == template_id,
                        PromptVersion.is_current == True
                    )
                )
                .values(is_current=False)
            )
            
            # 创建回滚版本
            rollback_version = PromptVersion(
                template_id=template_id,
                version_number=rollback_version_number,
                content=target_version.content,
                variables=target_version.variables,
                change_log=rollback_change_log,
                is_published=True,  # 回滚版本自动发布
                is_current=True,
                created_by=user_id
            )
            
            self.db.add(rollback_version)
            
            # 更新模板内容
            template = target_version.template
            template.content = target_version.content
            template.variables = target_version.variables
            template.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(template)
            
            Logger.info(f"版本回滚成功: 模板ID={template_id}, 新版本={rollback_version_number}")
            return template
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"回滚版本失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"回滚版本失败: {str(e)}"
            )
    
    # 私有辅助方法
    
    def _compare_text_content(self, content1: str, content2: str) -> Dict[str, Any]:
        """比较文本内容的差异
        
        Args:
            content1: 内容1
            content2: 内容2
            
        Returns:
            Dict[str, Any]: 差异信息
        """
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # 简单的行级比较
        added_lines = []
        removed_lines = []
        modified_lines = []
        
        max_lines = max(len(lines1), len(lines2))
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else None
            line2 = lines2[i] if i < len(lines2) else None
            
            if line1 is None and line2 is not None:
                added_lines.append({"line_number": i + 1, "content": line2})
            elif line1 is not None and line2 is None:
                removed_lines.append({"line_number": i + 1, "content": line1})
            elif line1 != line2:
                modified_lines.append({
                    "line_number": i + 1,
                    "old": line1,
                    "new": line2
                })
        
        return {
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "modified_lines": modified_lines
        }
    
    def _compare_variables(self, vars1: List[Dict], vars2: List[Dict]) -> Dict[str, Any]:
        """比较变量定义的差异
        
        Args:
            vars1: 变量定义1
            vars2: 变量定义2
            
        Returns:
            Dict[str, Any]: 变量差异信息
        """
        # 将变量列表转换为字典，便于比较
        vars1_dict = {var.get('name'): var for var in vars1 if var.get('name')}
        vars2_dict = {var.get('name'): var for var in vars2 if var.get('name')}
        
        added_vars = []
        removed_vars = []
        modified_vars = []
        
        # 检查新增和修改的变量
        for name, var2 in vars2_dict.items():
            if name not in vars1_dict:
                added_vars.append(var2)
            elif vars1_dict[name] != var2:
                modified_vars.append({
                    "name": name,
                    "old": vars1_dict[name],
                    "new": var2
                })
        
        # 检查删除的变量
        for name, var1 in vars1_dict.items():
            if name not in vars2_dict:
                removed_vars.append(var1)
        
        return {
            "added_variables": added_vars,
            "removed_variables": removed_vars,
            "modified_variables": modified_vars
        }
class PromptAnalyticsService:
    """提示词统计分析服务类
    
    处理提示词使用统计和性能分析相关的业务逻辑
    """
    
    def __init__(self, db: AsyncSession):
        """初始化统计分析服务
        
        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db
    
    async def log_usage(
        self,
        template_id: int,
        user_id: int,
        variables_used: Dict[str, Any],
        rendered_content: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        kb_id: Optional[int] = None,
        query: Optional[str] = None,
        execution_time: Optional[float] = None,
        response_quality: Optional[float] = None,
        token_count: Optional[int] = None,
        cost: Optional[float] = None
    ) -> PromptUsageLog:
        """记录提示词使用情况
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
            variables_used: 使用的变量
            rendered_content: 渲染后的内容
            success: 是否成功
            error_message: 错误信息
            kb_id: 知识库ID
            query: 查询内容
            execution_time: 执行时间
            response_quality: 响应质量
            token_count: token数量
            cost: 成本
            
        Returns:
            PromptUsageLog: 使用日志对象
        """
        try:
            # 获取当前版本ID
            version_result = await self.db.execute(
                select(PromptVersion.id).filter(
                    and_(
                        PromptVersion.template_id == template_id,
                        PromptVersion.is_current == True
                    )
                )
            )
            version_id = version_result.scalar_one_or_none()
            
            # 创建使用日志
            usage_log = PromptUsageLog(
                template_id=template_id,
                version_id=version_id,
                user_id=user_id,
                kb_id=kb_id,
                query=query,
                variables_used=variables_used,
                rendered_content=rendered_content,
                response_quality=response_quality,
                execution_time=execution_time,
                token_count=token_count,
                cost=cost,
                success=success,
                error_message=error_message
            )
            
            self.db.add(usage_log)
            await self.db.commit()
            await self.db.refresh(usage_log)
            
            return usage_log
            
        except Exception as e:
            Logger.error(f"记录提示词使用日志失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"记录使用日志失败: {str(e)}"
            )
    
    async def get_usage_stats(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        kb_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取使用统计数据
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            kb_id: 知识库ID筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 统计数据
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
            
            # 基础统计查询
            base_query = select(PromptUsageLog)
            if conditions:
                base_query = base_query.filter(and_(*conditions))
            
            # 总使用次数
            total_usage_result = await self.db.execute(
                select(func.count(PromptUsageLog.id)).select_from(base_query.subquery())
            )
            total_usage = total_usage_result.scalar() or 0
            
            # 成功次数
            success_conditions = conditions + [PromptUsageLog.success == True]
            success_result = await self.db.execute(
                select(func.count(PromptUsageLog.id)).filter(and_(*success_conditions))
            )
            success_count = success_result.scalar() or 0
            
            # 成功率
            success_rate = success_count / total_usage if total_usage > 0 else 0
            
            # 平均执行时间
            avg_time_result = await self.db.execute(
                select(func.avg(PromptUsageLog.execution_time)).filter(
                    and_(
                        *success_conditions,
                        PromptUsageLog.execution_time.is_not(None)
                    )
                )
            )
            avg_execution_time = avg_time_result.scalar()
            
            # 平均响应质量
            avg_quality_result = await self.db.execute(
                select(func.avg(PromptUsageLog.response_quality)).filter(
                    and_(
                        *success_conditions,
                        PromptUsageLog.response_quality.is_not(None)
                    )
                )
            )
            avg_response_quality = avg_quality_result.scalar()
            
            # 总成本
            total_cost_result = await self.db.execute(
                select(func.sum(PromptUsageLog.cost)).filter(
                    and_(
                        *success_conditions,
                        PromptUsageLog.cost.is_not(None)
                    )
                )
            )
            total_cost = total_cost_result.scalar() or 0
            
            # 总token数
            total_tokens_result = await self.db.execute(
                select(func.sum(PromptUsageLog.token_count)).filter(
                    and_(
                        *success_conditions,
                        PromptUsageLog.token_count.is_not(None)
                    )
                )
            )
            total_tokens = total_tokens_result.scalar() or 0
            
            return {
                "total_usage": total_usage,
                "success_count": success_count,
                "success_rate": round(success_rate, 4),
                "avg_execution_time": round(avg_execution_time, 4) if avg_execution_time else None,
                "avg_response_quality": round(avg_response_quality, 4) if avg_response_quality else None,
                "total_cost": round(total_cost, 6),
                "total_tokens": total_tokens,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            Logger.error(f"获取使用统计失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取统计数据失败: {str(e)}"
            )
    
    async def get_usage_trend(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取使用趋势数据
        
        Args:
            template_id: 模板ID筛选
            user_id: 用户ID筛选
            days: 统计天数
            
        Returns:
            List[Dict[str, Any]]: 趋势数据
        """
        try:
            from datetime import timedelta
            
            # 计算日期范围
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
            
            # 按日期分组统计
            from sqlalchemy import cast, Date
            
            result = await self.db.execute(
                select(
                    cast(PromptUsageLog.created_at, Date).label('date'),
                    func.count(PromptUsageLog.id).label('usage_count'),
                    func.sum(
                        func.case(
                            (PromptUsageLog.success == True, 1),
                            else_=0
                        )
                    ).label('success_count'),
                    func.avg(PromptUsageLog.execution_time).label('avg_execution_time'),
                    func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                    func.sum(PromptUsageLog.cost).label('total_cost')
                )
                .filter(and_(*conditions))
                .group_by(cast(PromptUsageLog.created_at, Date))
                .order_by(cast(PromptUsageLog.created_at, Date))
            )
            
            trend_data = []
            for row in result:
                usage_count = row.usage_count or 0
                success_count = row.success_count or 0
                success_rate = success_count / usage_count if usage_count > 0 else 0
                
                trend_data.append({
                    "date": row.date.isoformat(),
                    "usage_count": usage_count,
                    "success_count": success_count,
                    "success_rate": round(success_rate, 4),
                    "avg_execution_time": round(row.avg_execution_time, 4) if row.avg_execution_time else None,
                    "avg_response_quality": round(row.avg_response_quality, 4) if row.avg_response_quality else None,
                    "total_cost": round(row.total_cost, 6) if row.total_cost else 0
                })
            
            return trend_data
            
        except Exception as e:
            Logger.error(f"获取使用趋势失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取趋势数据失败: {str(e)}"
            )
    
    async def get_template_ranking(
        self,
        user_id: Optional[int] = None,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取模板使用排行榜
        
        Args:
            user_id: 用户ID筛选
            days: 统计天数
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 排行榜数据
        """
        try:
            from datetime import timedelta
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                PromptUsageLog.created_at >= start_date,
                PromptUsageLog.created_at <= end_date
            ]
            
            if user_id:
                conditions.append(PromptUsageLog.user_id == user_id)
            
            # 按模板分组统计
            result = await self.db.execute(
                select(
                    PromptUsageLog.template_id,
                    PromptTemplate.name.label('template_name'),
                    func.count(PromptUsageLog.id).label('usage_count'),
                    func.sum(
                        func.case(
                            (PromptUsageLog.success == True, 1),
                            else_=0
                        )
                    ).label('success_count'),
                    func.avg(PromptUsageLog.response_quality).label('avg_response_quality'),
                    func.sum(PromptUsageLog.cost).label('total_cost')
                )
                .join(PromptTemplate, PromptUsageLog.template_id == PromptTemplate.id)
                .filter(and_(*conditions))
                .group_by(PromptUsageLog.template_id, PromptTemplate.name)
                .order_by(desc(func.count(PromptUsageLog.id)))
                .limit(limit)
            )
            
            ranking_data = []
            for i, row in enumerate(result, 1):
                usage_count = row.usage_count or 0
                success_count = row.success_count or 0
                success_rate = success_count / usage_count if usage_count > 0 else 0
                
                ranking_data.append({
                    "rank": i,
                    "template_id": row.template_id,
                    "template_name": row.template_name,
                    "usage_count": usage_count,
                    "success_rate": round(success_rate, 4),
                    "avg_response_quality": round(row.avg_response_quality, 4) if row.avg_response_quality else None,
                    "total_cost": round(row.total_cost, 6) if row.total_cost else 0
                })
            
            return ranking_data
            
        except Exception as e:
            Logger.error(f"获取模板排行榜失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取排行榜失败: {str(e)}"
            )
    
    async def get_error_analysis(
        self,
        template_id: Optional[int] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取错误分析数据
        
        Args:
            template_id: 模板ID筛选
            days: 统计天数
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 错误分析数据
        """
        try:
            from datetime import timedelta
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                PromptUsageLog.created_at >= start_date,
                PromptUsageLog.created_at <= end_date,
                PromptUsageLog.success == False,
                PromptUsageLog.error_message.is_not(None)
            ]
            
            if template_id:
                conditions.append(PromptUsageLog.template_id == template_id)
            
            # 按错误信息分组统计
            result = await self.db.execute(
                select(
                    PromptUsageLog.error_message,
                    func.count(PromptUsageLog.id).label('error_count'),
                    func.max(PromptUsageLog.created_at).label('last_occurrence')
                )
                .filter(and_(*conditions))
                .group_by(PromptUsageLog.error_message)
                .order_by(desc(func.count(PromptUsageLog.id)))
                .limit(limit)
            )
            
            error_data = []
            for row in result:
                error_data.append({
                    "error_message": row.error_message,
                    "error_count": row.error_count,
                    "last_occurrence": row.last_occurrence.isoformat() if row.last_occurrence else None
                })
            
            return error_data
            
        except Exception as e:
            Logger.error(f"获取错误分析失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取错误分析失败: {str(e)}"
            )    
            
    async def update_category(
        self, 
        category_id: int, 
        category_data: PromptCategoryUpdate
    ) -> PromptCategory:
        """更新提示词分类
        
        Args:
            category_id: 分类ID
            category_data: 更新数据
            
        Returns:
            PromptCategory: 更新后的分类对象
        """
        try:
            # 获取现有分类
            category = await self.get_category(category_id)
            
            # 检查名称是否重复
            if category_data.name and category_data.name != category.name:
                existing = await self.db.execute(
                    select(PromptCategory).filter(
                        and_(
                            PromptCategory.name == category_data.name,
                            PromptCategory.parent_id == category.parent_id,
                            PromptCategory.id != category_id,
                            PromptCategory.is_active == True
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"分类名称 '{category_data.name}' 已存在"
                    )
            
            # 验证父分类
            if category_data.parent_id is not None and category_data.parent_id != category.parent_id:
                if category_data.parent_id == category_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="分类不能设置自己为父分类"
                    )
                
                if category_data.parent_id:
                    parent_category = await self.db.execute(
                        select(PromptCategory).filter(
                            and_(
                                PromptCategory.id == category_data.parent_id,
                                PromptCategory.is_active == True
                            )
                        )
                    )
                    if not parent_category.scalar_one_or_none():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"父分类ID {category_data.parent_id} 不存在"
                        )
            
            # 更新分类
            update_data = category_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(category, field, value)
            
            category.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(category)
            
            Logger.info(f"提示词分类更新成功: ID={category.id}")
            return category
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"更新提示词分类失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新分类失败: {str(e)}"
            )
    
    async def delete_category(self, category_id: int) -> None:
        """删除提示词分类（软删除）
        
        Args:
            category_id: 分类ID
        """
        try:
            # 获取分类
            category = await self.get_category(category_id)
            
            # 检查是否有子分类
            children_result = await self.db.execute(
                select(PromptCategory).filter(
                    and_(
                        PromptCategory.parent_id == category_id,
                        PromptCategory.is_active == True
                    )
                )
            )
            children = children_result.scalars().all()
            
            if children:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能删除包含子分类的分类，请先删除或移动子分类"
                )
            
            # 检查是否有关联的模板
            templates_result = await self.db.execute(
                select(PromptTemplate).filter(
                    and_(
                        PromptTemplate.category_id == category_id,
                        PromptTemplate.is_active == True
                    )
                )
            )
            templates = templates_result.scalars().all()
            
            if templates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能删除包含模板的分类，请先删除或移动模板"
                )
            
            # 软删除
            category.is_active = False
            category.updated_at = datetime.now()
            
            await self.db.commit()
            
            Logger.info(f"提示词分类删除成功: ID={category_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            Logger.error(f"删除提示词分类失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除分类失败: {str(e)}"
            )