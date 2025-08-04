#!/usr/bin/env python3
"""
初始化内容管理系统脚本

该脚本创建默认的内容审核规则、标签、分类等
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import AsyncSessionLocal
from app.models.content import (
    ContentModerationRule, ContentTag, ContentCategory, SearchIndex
)
from app.models.knowledge_base import KnowledgeBase
# from app.models.document import Document  # 暂时不使用
from app.core.logger import Logger

async def create_default_moderation_rules():
    """创建默认内容审核规则"""
    
    default_rules = [
        {
            "name": "敏感词过滤",
            "description": "检测和过滤敏感词汇",
            "rule_type": "keyword_filter",
            "conditions": {
                "keywords": ["spam", "abuse", "inappropriate"],
                "case_sensitive": False,
                "match_type": "contains"
            },
            "actions": {
                "action": "flag",
                "severity": "medium",
                "auto_apply": True
            },
            "priority": 100,
            "is_active": True,
            "auto_apply": True
        },
        {
            "name": "内容长度检查",
            "description": "检查内容长度是否符合要求",
            "rule_type": "length_check",
            "conditions": {
                "min_length": 10,
                "max_length": 10000,
                "check_title": True,
                "check_content": True
            },
            "actions": {
                "action": "reject",
                "reason": "内容长度不符合要求",
                "auto_apply": False
            },
            "priority": 90,
            "is_active": True,
            "auto_apply": False
        },
        {
            "name": "重复内容检测",
            "description": "检测重复或相似内容",
            "rule_type": "duplicate_check",
            "conditions": {
                "similarity_threshold": 0.8,
                "check_title": True,
                "check_content": True,
                "time_window": 86400  # 24小时
            },
            "actions": {
                "action": "flag",
                "severity": "low",
                "auto_apply": True
            },
            "priority": 80,
            "is_active": True,
            "auto_apply": True
        },
        {
            "name": "链接安全检查",
            "description": "检查内容中的外部链接安全性",
            "rule_type": "link_safety",
            "conditions": {
                "check_malicious_domains": True,
                "check_phishing": True,
                "allowed_domains": ["example.com", "trusted-site.com"],
                "blocked_domains": ["malicious-site.com"]
            },
            "actions": {
                "action": "remove",
                "reason": "包含不安全链接",
                "auto_apply": True
            },
            "priority": 95,
            "is_active": True,
            "auto_apply": True
        },
        {
            "name": "图片内容审核",
            "description": "审核图片内容是否合规",
            "rule_type": "image_moderation",
            "conditions": {
                "check_adult_content": True,
                "check_violence": True,
                "confidence_threshold": 0.7
            },
            "actions": {
                "action": "flag",
                "severity": "high",
                "auto_apply": False
            },
            "priority": 85,
            "is_active": True,
            "auto_apply": False
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for rule_data in default_rules:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(ContentModerationRule).where(ContentModerationRule.name == rule_data["name"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    rule = ContentModerationRule(**rule_data)
                    db.add(rule)
                    Logger.info(f"创建内容审核规则: {rule_data['name']}")
                else:
                    Logger.info(f"内容审核规则已存在: {rule_data['name']}")
            
            await db.commit()
            Logger.info("默认内容审核规则创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认内容审核规则失败: {str(e)}")
            raise

async def create_default_tags():
    """创建默认内容标签"""
    
    default_tags = [
        {"name": "技术", "description": "技术相关内容", "color": "#007bff", "category": "主题"},
        {"name": "教程", "description": "教程和指南", "color": "#28a745", "category": "类型"},
        {"name": "文档", "description": "文档资料", "color": "#6c757d", "category": "类型"},
        {"name": "API", "description": "API相关", "color": "#17a2b8", "category": "技术"},
        {"name": "数据库", "description": "数据库相关", "color": "#ffc107", "category": "技术"},
        {"name": "前端", "description": "前端开发", "color": "#e83e8c", "category": "技术"},
        {"name": "后端", "description": "后端开发", "color": "#6f42c1", "category": "技术"},
        {"name": "AI", "description": "人工智能", "color": "#fd7e14", "category": "技术"},
        {"name": "机器学习", "description": "机器学习相关", "color": "#20c997", "category": "技术"},
        {"name": "重要", "description": "重要内容", "color": "#dc3545", "category": "优先级"},
        {"name": "草稿", "description": "草稿状态", "color": "#6c757d", "category": "状态"},
        {"name": "已发布", "description": "已发布内容", "color": "#28a745", "category": "状态"}
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for tag_data in default_tags:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(ContentTag).where(ContentTag.name == tag_data["name"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    tag = ContentTag(**tag_data, is_system=True)
                    db.add(tag)
                    Logger.info(f"创建内容标签: {tag_data['name']}")
                else:
                    Logger.info(f"内容标签已存在: {tag_data['name']}")
            
            await db.commit()
            Logger.info("默认内容标签创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认内容标签失败: {str(e)}")
            raise

async def create_default_categories():
    """创建默认内容分类"""
    
    default_categories = [
        {
            "name": "技术文档",
            "slug": "tech-docs",
            "description": "技术相关文档和资料",
            "icon": "📚",
            "color": "#007bff",
            "sort_order": 1
        },
        {
            "name": "API文档",
            "slug": "api-docs",
            "description": "API接口文档",
            "icon": "🔌",
            "color": "#17a2b8",
            "sort_order": 2
        },
        {
            "name": "用户指南",
            "slug": "user-guides",
            "description": "用户使用指南和教程",
            "icon": "📖",
            "color": "#28a745",
            "sort_order": 3
        },
        {
            "name": "开发指南",
            "slug": "dev-guides",
            "description": "开发者指南和最佳实践",
            "icon": "💻",
            "color": "#6f42c1",
            "sort_order": 4
        },
        {
            "name": "常见问题",
            "slug": "faq",
            "description": "常见问题解答",
            "icon": "❓",
            "color": "#ffc107",
            "sort_order": 5
        },
        {
            "name": "发布说明",
            "slug": "release-notes",
            "description": "版本发布说明和更新日志",
            "icon": "📝",
            "color": "#fd7e14",
            "sort_order": 6
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for category_data in default_categories:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(ContentCategory).where(ContentCategory.slug == category_data["slug"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    category = ContentCategory(**category_data)
                    db.add(category)
                    Logger.info(f"创建内容分类: {category_data['name']}")
                else:
                    Logger.info(f"内容分类已存在: {category_data['name']}")
            
            await db.commit()
            Logger.info("默认内容分类创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认内容分类失败: {str(e)}")
            raise

async def initialize_search_indexes():
    """初始化搜索索引"""
    
    async with AsyncSessionLocal() as db:
        try:
            # 为现有知识库创建搜索索引
            from sqlalchemy import select
            kb_result = await db.execute(select(KnowledgeBase))
            knowledge_bases = kb_result.scalars().all()
            
            for kb in knowledge_bases:
                # 检查是否已有索引
                index_result = await db.execute(
                    select(SearchIndex)
                    .where(SearchIndex.content_type == "knowledge_base")
                    .where(SearchIndex.content_id == kb.id)
                )
                existing_index = index_result.scalar_one_or_none()
                
                if not existing_index:
                    search_index = SearchIndex(
                        content_type="knowledge_base",
                        content_id=kb.id,
                        title=kb.name,
                        content=f"Knowledge base: {kb.name}",
                        keywords=f"{kb.name} knowledge base",
                        meta_data={
                            "training_status": kb.training_status.value if kb.training_status else None,
                            "created_at": kb.created_at.isoformat() if kb.created_at else None
                        },
                        boost_score=1.0
                    )
                    db.add(search_index)
                    Logger.info(f"创建知识库搜索索引: {kb.name}")
            
            # 文档索引将在后续版本中实现
            Logger.info("文档搜索索引功能将在后续版本中实现")
            
            await db.commit()
            Logger.info("搜索索引初始化完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"初始化搜索索引失败: {str(e)}")
            raise

async def main():
    """主函数"""
    try:
        Logger.info("开始初始化内容管理系统...")
        
        # 创建默认内容审核规则
        await create_default_moderation_rules()
        
        # 创建默认内容标签
        await create_default_tags()
        
        # 创建默认内容分类
        await create_default_categories()
        
        # 初始化搜索索引
        await initialize_search_indexes()
        
        Logger.info("内容管理系统初始化完成!")
        Logger.info("内容管理功能包括:")
        Logger.info("- 内容审核规则 (5个预定义规则)")
        Logger.info("- 内容标签系统 (12个默认标签)")
        Logger.info("- 内容分类管理 (6个默认分类)")
        Logger.info("- 批量操作功能")
        Logger.info("- 高级搜索功能")
        Logger.info("- 数据导出功能")
        Logger.info("- 内容统计分析")
        
    except Exception as e:
        Logger.error(f"内容管理系统初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
