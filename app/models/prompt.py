from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from .database import Base
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.sql import select, and_
from app.models.user import User
from app.core.logger import Logger


class PromptTemplate(Base):
    """提示词模板模型
    
    用于存储AI提示词模板的基本信息、内容和配置
    支持变量替换、版本控制和权限管理
    """
    __tablename__ = "prompt_templates"
    __table_args__ = {'comment': '提示词模板表，存储提示词模板的基本信息和内容'}

    id = Column(Integer, primary_key=True, index=True, comment='提示词模板ID')
    name = Column(String(255), nullable=False, index=True, comment='模板名称')
    description = Column(Text, nullable=True, comment='模板描述')
    category_id = Column(Integer, ForeignKey("prompt_categories.id", ondelete="SET NULL"), nullable=True, comment='分类ID')
    content = Column(Text, nullable=False, comment='提示词内容，支持变量占位符')
    variables = Column(JSON, nullable=True, comment='变量定义，包含变量名、类型、默认值等')
    tags = Column(JSON, nullable=True, comment='标签列表，用于分类和搜索')
    is_system = Column(Boolean, default=False, comment='是否为系统内置模板')
    is_active = Column(Boolean, default=True, comment='是否激活状态')
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment='模板所有者用户ID')
    
    # 使用统计字段
    usage_count = Column(Integer, default=0, comment='使用次数统计')
    last_used_at = Column(DateTime, nullable=True, comment='最后使用时间')
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    owner = relationship("User", back_populates="prompt_templates", foreign_keys=[owner_id])
    category = relationship("PromptCategory", back_populates="templates")
    versions = relationship("PromptVersion", back_populates="template", cascade="all, delete-orphan")
    usage_logs = relationship("PromptUsageLog", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PromptTemplate {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于JSON序列化"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "content": self.content,
            "variables": self.variables or [],
            "tags": self.tags or [],
            "is_system": self.is_system,
            "is_active": self.is_active,
            "owner_id": self.owner_id,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def validate_variables(self) -> bool:
        """验证变量定义的格式是否正确"""
        if not self.variables:
            return True
            
        try:
            if not isinstance(self.variables, list):
                return False
                
            for var in self.variables:
                if not isinstance(var, dict):
                    return False
                    
                # 检查必需字段
                required_fields = ['name', 'type']
                for field in required_fields:
                    if field not in var:
                        return False
                        
                # 检查变量类型
                valid_types = ['string', 'integer', 'float', 'boolean', 'array', 'object']
                if var['type'] not in valid_types:
                    return False
                    
            return True
        except Exception as e:
            Logger.error(f"变量验证失败: {str(e)}")
            return False
    
    def extract_variables_from_content(self) -> List[str]:
        """从模板内容中提取变量名"""
        import re
        
        # 匹配 {{variable_name}} 格式的变量
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, self.content)
        return list(set(matches))  # 去重
    
    def validate_content_variables(self) -> bool:
        """验证内容中的变量是否都在变量定义中"""
        content_vars = self.extract_variables_from_content()
        if not content_vars:
            return True
            
        if not self.variables:
            return False
            
        defined_vars = [var['name'] for var in self.variables if isinstance(var, dict) and 'name' in var]
        
        # 检查内容中的变量是否都有定义
        for var in content_vars:
            if var not in defined_vars:
                return False
                
        return True


class PromptCategory(Base):
    """提示词分类模型
    
    用于组织和管理提示词模板的分类结构
    支持层级分类和分类统计
    """
    __tablename__ = "prompt_categories"
    __table_args__ = {'comment': '提示词分类表，用于组织提示词模板的层级分类'}

    id = Column(Integer, primary_key=True, index=True, comment='分类ID')
    name = Column(String(255), nullable=False, comment='分类名称')
    description = Column(Text, nullable=True, comment='分类描述')
    parent_id = Column(Integer, ForeignKey("prompt_categories.id", ondelete="CASCADE"), nullable=True, comment='父分类ID')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    is_active = Column(Boolean, default=True, comment='是否激活状态')
    
    # 统计字段
    template_count = Column(Integer, default=0, comment='该分类下的模板数量')
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    parent = relationship("PromptCategory", remote_side=[id], backref="children")
    templates = relationship("PromptTemplate", back_populates="category")
    
    def __repr__(self):
        return f"<PromptCategory {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于JSON序列化"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "template_count": self.template_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_full_path(self) -> str:
        """获取分类的完整路径"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    def get_all_children_ids(self, db: Session) -> List[int]:
        """获取所有子分类的ID（递归）"""
        children_ids = [self.id]
        
        # 查询直接子分类
        children = db.execute(
            select(PromptCategory).filter(PromptCategory.parent_id == self.id)
        ).scalars().all()
        
        # 递归获取子分类的子分类
        for child in children:
            children_ids.extend(child.get_all_children_ids(db))
            
        return children_ids


class PromptVersion(Base):
    """提示词版本模型
    
    用于管理提示词模板的版本控制
    支持版本创建、发布、回滚等功能
    """
    __tablename__ = "prompt_versions"
    __table_args__ = {'comment': '提示词版本表，用于管理提示词模板的版本控制'}

    id = Column(Integer, primary_key=True, index=True, comment='版本ID')
    template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False, comment='模板ID')
    version_number = Column(String(50), nullable=False, comment='版本号，如v1.0.0')
    content = Column(Text, nullable=False, comment='该版本的提示词内容')
    variables = Column(JSON, nullable=True, comment='该版本的变量定义')
    change_log = Column(Text, nullable=True, comment='版本变更说明')
    is_published = Column(Boolean, default=False, comment='是否已发布')
    is_current = Column(Boolean, default=False, comment='是否为当前使用版本')
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='版本创建者')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    published_at = Column(DateTime, nullable=True, comment='发布时间')
    
    # 关系定义
    template = relationship("PromptTemplate", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<PromptVersion {self.template_id}:{self.version_number}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于JSON序列化"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "version_number": self.version_number,
            "content": self.content,
            "variables": self.variables or [],
            "change_log": self.change_log,
            "is_published": self.is_published,
            "is_current": self.is_current,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


class PromptUsageLog(Base):
    """提示词使用日志模型
    
    用于记录提示词模板的使用情况和性能统计
    支持使用分析和效果评估
    """
    __tablename__ = "prompt_usage_logs"
    __table_args__ = {'comment': '提示词使用日志表，记录提示词模板的使用情况和性能统计'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False, comment='模板ID')
    version_id = Column(Integer, ForeignKey("prompt_versions.id", ondelete="SET NULL"), nullable=True, comment='使用的版本ID')
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='使用者用户ID')
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True, comment='关联的知识库ID')
    
    # 使用详情
    query = Column(Text, nullable=True, comment='用户查询内容')
    variables_used = Column(JSON, nullable=True, comment='实际使用的变量值')
    rendered_content = Column(Text, nullable=True, comment='渲染后的完整提示词内容')
    
    # 性能指标
    response_quality = Column(Float, nullable=True, comment='响应质量评分（0-1）')
    execution_time = Column(Float, nullable=True, comment='执行时间（秒）')
    token_count = Column(Integer, nullable=True, comment='生成的token数量')
    cost = Column(Float, nullable=True, comment='使用成本（美元）')
    
    # 结果信息
    success = Column(Boolean, default=True, comment='是否执行成功')
    error_message = Column(Text, nullable=True, comment='错误信息（如果失败）')
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, comment='使用时间')
    
    # 关系定义
    template = relationship("PromptTemplate", back_populates="usage_logs")
    version = relationship("PromptVersion")
    user = relationship("User")
    knowledge_base = relationship("KnowledgeBase")
    
    def __repr__(self):
        return f"<PromptUsageLog {self.template_id}:{self.created_at}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于JSON序列化"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "version_id": self.version_id,
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "query": self.query,
            "variables_used": self.variables_used or {},
            "response_quality": self.response_quality,
            "execution_time": self.execution_time,
            "token_count": self.token_count,
            "cost": self.cost,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }