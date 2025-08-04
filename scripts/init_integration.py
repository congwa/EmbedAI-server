#!/usr/bin/env python3
"""
初始化集成管理系统脚本

该脚本创建默认的集成模板、API文档和端点信息
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import AsyncSessionLocal
from app.models.integration import (
    IntegrationTemplate, APIDocumentation, APIEndpoint
)
from app.core.logger import Logger

async def create_default_integration_templates():
    """创建默认集成模板"""
    
    default_templates = [
        {
            "name": "Slack集成",
            "description": "与Slack工作空间集成，发送通知和消息",
            "provider": "Slack",
            "integration_type": "webhook",
            "template_config": {
                "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                "channel": "#general",
                "username": "EmbedAI Bot",
                "icon_emoji": ":robot_face:"
            },
            "required_fields": ["webhook_url"],
            "optional_fields": ["channel", "username", "icon_emoji"],
            "documentation_url": "https://api.slack.com/messaging/webhooks",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/slack.svg",
            "rating": 4.8
        },
        {
            "name": "Discord集成",
            "description": "与Discord服务器集成，发送消息和通知",
            "provider": "Discord",
            "integration_type": "webhook",
            "template_config": {
                "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL",
                "username": "EmbedAI",
                "avatar_url": ""
            },
            "required_fields": ["webhook_url"],
            "optional_fields": ["username", "avatar_url"],
            "documentation_url": "https://discord.com/developers/docs/resources/webhook",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/discord.svg",
            "rating": 4.6
        },
        {
            "name": "Microsoft Teams集成",
            "description": "与Microsoft Teams集成，发送卡片和通知",
            "provider": "Microsoft",
            "integration_type": "webhook",
            "template_config": {
                "webhook_url": "https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK",
                "card_type": "MessageCard",
                "theme_color": "0076D7"
            },
            "required_fields": ["webhook_url"],
            "optional_fields": ["card_type", "theme_color"],
            "documentation_url": "https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/microsoftteams.svg",
            "rating": 4.4
        },
        {
            "name": "Zapier集成",
            "description": "通过Zapier连接数千个应用程序",
            "provider": "Zapier",
            "integration_type": "webhook",
            "template_config": {
                "webhook_url": "https://hooks.zapier.com/hooks/catch/YOUR/ZAPIER/HOOK",
                "trigger_event": "knowledge_base_created"
            },
            "required_fields": ["webhook_url"],
            "optional_fields": ["trigger_event"],
            "documentation_url": "https://zapier.com/help/create/code-webhooks/trigger-zaps-from-webhooks",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/zapier.svg",
            "rating": 4.7
        },
        {
            "name": "GitHub集成",
            "description": "与GitHub仓库集成，创建Issues和Pull Requests",
            "provider": "GitHub",
            "integration_type": "api_client",
            "template_config": {
                "api_url": "https://api.github.com",
                "repository": "owner/repo",
                "auth_type": "token"
            },
            "required_fields": ["repository", "access_token"],
            "optional_fields": ["api_url", "auth_type"],
            "documentation_url": "https://docs.github.com/en/rest",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/github.svg",
            "rating": 4.9
        },
        {
            "name": "Jira集成",
            "description": "与Atlassian Jira集成，创建和管理工单",
            "provider": "Atlassian",
            "integration_type": "api_client",
            "template_config": {
                "api_url": "https://your-domain.atlassian.net/rest/api/3",
                "project_key": "PROJ",
                "issue_type": "Task"
            },
            "required_fields": ["api_url", "username", "api_token", "project_key"],
            "optional_fields": ["issue_type"],
            "documentation_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/jira.svg",
            "rating": 4.3
        },
        {
            "name": "Google Sheets集成",
            "description": "与Google Sheets集成，读写电子表格数据",
            "provider": "Google",
            "integration_type": "oauth",
            "template_config": {
                "api_url": "https://sheets.googleapis.com/v4/spreadsheets",
                "scope": "https://www.googleapis.com/auth/spreadsheets",
                "spreadsheet_id": ""
            },
            "required_fields": ["client_id", "client_secret", "spreadsheet_id"],
            "optional_fields": ["scope"],
            "documentation_url": "https://developers.google.com/sheets/api",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/googlesheets.svg",
            "rating": 4.5
        },
        {
            "name": "Salesforce集成",
            "description": "与Salesforce CRM集成，同步客户和销售数据",
            "provider": "Salesforce",
            "integration_type": "oauth",
            "template_config": {
                "api_url": "https://your-instance.salesforce.com/services/data/v58.0",
                "auth_url": "https://login.salesforce.com/services/oauth2/authorize",
                "token_url": "https://login.salesforce.com/services/oauth2/token"
            },
            "required_fields": ["client_id", "client_secret", "instance_url"],
            "optional_fields": ["api_version"],
            "documentation_url": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/",
            "icon_url": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/salesforce.svg",
            "rating": 4.2
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for template_data in default_templates:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(IntegrationTemplate).where(
                        IntegrationTemplate.name == template_data["name"]
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    template = IntegrationTemplate(**template_data)
                    db.add(template)
                    Logger.info(f"创建集成模板: {template_data['name']}")
                else:
                    Logger.info(f"集成模板已存在: {template_data['name']}")
            
            await db.commit()
            Logger.info("默认集成模板创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认集成模板失败: {str(e)}")
            raise

async def create_default_api_documentation():
    """创建默认API文档"""
    
    default_docs = [
        {
            "title": "API概述",
            "content": """# EmbedAI API 概述

欢迎使用EmbedAI API！本API提供了完整的知识库管理、文档处理和智能对话功能。

## 基础信息

- **Base URL**: `https://api.embedai.com/v1`
- **认证方式**: API Key (Bearer Token)
- **数据格式**: JSON
- **字符编码**: UTF-8

## 快速开始

1. 获取API密钥
2. 设置请求头
3. 发送第一个请求

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     https://api.embedai.com/v1/knowledge-bases
```

## 响应格式

所有API响应都遵循统一的格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-08-04T12:00:00Z"
}
```
""",
            "content_type": "markdown",
            "category": "概述",
            "tags": ["overview", "getting-started"],
            "version": "v1",
            "order_index": 1,
            "is_published": True,
            "is_featured": True
        },
        {
            "title": "认证和授权",
            "content": """# 认证和授权

## API密钥认证

EmbedAI API使用API密钥进行认证。您需要在请求头中包含您的API密钥：

```
Authorization: Bearer YOUR_API_KEY
```

## 获取API密钥

1. 登录EmbedAI管理后台
2. 导航到"集成管理" > "API密钥"
3. 点击"创建新密钥"
4. 设置权限范围和过期时间
5. 复制生成的API密钥

## 权限范围

API密钥支持以下权限范围：

- `read`: 只读权限，可以查询数据
- `write`: 写入权限，可以创建和更新数据
- `admin`: 管理员权限，可以执行所有操作
- `webhook`: Webhook权限，用于接收事件通知

## 安全最佳实践

1. **保护您的API密钥**: 不要在客户端代码中暴露API密钥
2. **使用HTTPS**: 始终通过HTTPS发送请求
3. **定期轮换**: 定期更新您的API密钥
4. **最小权限原则**: 只授予必要的权限范围
5. **监控使用情况**: 定期检查API使用日志
""",
            "content_type": "markdown",
            "category": "认证",
            "tags": ["authentication", "security", "api-key"],
            "version": "v1",
            "order_index": 2,
            "is_published": True,
            "is_featured": True
        },
        {
            "title": "知识库管理",
            "content": """# 知识库管理 API

知识库是EmbedAI的核心概念，用于组织和管理相关文档。

## 创建知识库

```http
POST /v1/knowledge-bases
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "产品文档",
  "description": "产品相关的所有文档",
  "settings": {
    "embedding_model": "text-embedding-ada-002",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

## 获取知识库列表

```http
GET /v1/knowledge-bases?page=1&page_size=20
Authorization: Bearer YOUR_API_KEY
```

## 更新知识库

```http
PUT /v1/knowledge-bases/{kb_id}
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "更新后的名称",
  "description": "更新后的描述"
}
```

## 删除知识库

```http
DELETE /v1/knowledge-bases/{kb_id}
Authorization: Bearer YOUR_API_KEY
```

## 响应示例

```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "产品文档",
    "description": "产品相关的所有文档",
    "document_count": 15,
    "training_status": "completed",
    "created_at": "2024-08-04T10:00:00Z",
    "updated_at": "2024-08-04T12:00:00Z"
  }
}
```
""",
            "content_type": "markdown",
            "category": "API参考",
            "tags": ["knowledge-base", "crud", "api"],
            "version": "v1",
            "order_index": 10,
            "is_published": True
        },
        {
            "title": "文档管理",
            "content": """# 文档管理 API

文档是知识库的基本组成单元，支持多种格式的文件上传和处理。

## 上传文档

```http
POST /v1/knowledge-bases/{kb_id}/documents
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

file: [文件内容]
title: "文档标题"
doc_type: "pdf"
```

## 支持的文件格式

- PDF (.pdf)
- Word文档 (.docx, .doc)
- 文本文件 (.txt)
- Markdown (.md)
- HTML (.html)
- PowerPoint (.pptx, .ppt)

## 获取文档列表

```http
GET /v1/knowledge-bases/{kb_id}/documents?page=1&page_size=20
Authorization: Bearer YOUR_API_KEY
```

## 获取文档详情

```http
GET /v1/documents/{doc_id}
Authorization: Bearer YOUR_API_KEY
```

## 删除文档

```http
DELETE /v1/documents/{doc_id}
Authorization: Bearer YOUR_API_KEY
```

## 文档处理状态

- `pending`: 等待处理
- `processing`: 正在处理
- `completed`: 处理完成
- `failed`: 处理失败

## 响应示例

```json
{
  "success": true,
  "data": {
    "id": 456,
    "title": "产品使用手册",
    "doc_type": "pdf",
    "file_size": 2048576,
    "processing_status": "completed",
    "knowledge_base_id": 123,
    "created_at": "2024-08-04T11:00:00Z"
  }
}
```
""",
            "content_type": "markdown",
            "category": "API参考",
            "tags": ["document", "upload", "api"],
            "version": "v1",
            "order_index": 11,
            "is_published": True
        },
        {
            "title": "Webhook事件",
            "content": """# Webhook 事件

EmbedAI支持通过Webhook实时通知您的应用程序关于重要事件。

## 支持的事件类型

### 用户事件
- `user.created`: 用户创建
- `user.updated`: 用户更新
- `user.deleted`: 用户删除

### 知识库事件
- `knowledge_base.created`: 知识库创建
- `knowledge_base.updated`: 知识库更新
- `knowledge_base.deleted`: 知识库删除

### 文档事件
- `document.uploaded`: 文档上传
- `document.processed`: 文档处理完成
- `document.failed`: 文档处理失败

### 对话事件
- `chat.started`: 对话开始
- `chat.ended`: 对话结束

### 系统事件
- `system.alert`: 系统告警

## 配置Webhook

```http
POST /v1/admin/integration/webhooks
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "我的Webhook",
  "url": "https://your-app.com/webhook",
  "events": ["knowledge_base.created", "document.processed"],
  "secret": "your-webhook-secret"
}
```

## 事件载荷格式

```json
{
  "event_type": "knowledge_base.created",
  "timestamp": "2024-08-04T12:00:00Z",
  "data": {
    "id": 123,
    "name": "新知识库",
    "created_by": 1
  },
  "metadata": {
    "source": "api",
    "version": "v1"
  }
}
```

## 验证Webhook签名

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```
""",
            "content_type": "markdown",
            "category": "Webhook",
            "tags": ["webhook", "events", "integration"],
            "version": "v1",
            "order_index": 20,
            "is_published": True
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for doc_data in default_docs:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(APIDocumentation).where(APIDocumentation.title == doc_data["title"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    documentation = APIDocumentation(**doc_data)
                    db.add(documentation)
                    Logger.info(f"创建API文档: {doc_data['title']}")
                else:
                    Logger.info(f"API文档已存在: {doc_data['title']}")
            
            await db.commit()
            Logger.info("默认API文档创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建默认API文档失败: {str(e)}")
            raise

async def create_api_endpoints():
    """创建API端点信息"""
    
    api_endpoints = [
        {
            "path": "/v1/knowledge-bases",
            "method": "GET",
            "summary": "获取知识库列表",
            "description": "分页获取用户的知识库列表",
            "tags": ["knowledge-base"],
            "parameters": {
                "query": [
                    {"name": "page", "type": "integer", "description": "页码"},
                    {"name": "page_size", "type": "integer", "description": "每页数量"}
                ]
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/KnowledgeBase"}
                    }
                }
            },
            "auth_required": True,
            "scopes_required": ["read"],
            "version": "v1"
        },
        {
            "path": "/v1/knowledge-bases",
            "method": "POST",
            "summary": "创建知识库",
            "description": "创建新的知识库",
            "tags": ["knowledge-base"],
            "request_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "settings": {"type": "object"}
                },
                "required": ["name"]
            },
            "auth_required": True,
            "scopes_required": ["write"],
            "version": "v1"
        },
        {
            "path": "/v1/knowledge-bases/{kb_id}/documents",
            "method": "POST",
            "summary": "上传文档",
            "description": "向知识库上传文档",
            "tags": ["document"],
            "parameters": {
                "path": [
                    {"name": "kb_id", "type": "integer", "description": "知识库ID"}
                ]
            },
            "request_schema": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "title": {"type": "string"},
                    "doc_type": {"type": "string"}
                },
                "required": ["file"]
            },
            "auth_required": True,
            "scopes_required": ["write"],
            "version": "v1"
        },
        {
            "path": "/v1/admin/integration/webhooks",
            "method": "POST",
            "summary": "创建Webhook",
            "description": "创建新的Webhook配置",
            "tags": ["webhook"],
            "request_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "events": {"type": "array", "items": {"type": "string"}},
                    "secret": {"type": "string"}
                },
                "required": ["name", "url", "events"]
            },
            "auth_required": True,
            "scopes_required": ["admin"],
            "version": "v1"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for endpoint_data in api_endpoints:
                # 检查是否已存在
                from sqlalchemy import select
                result = await db.execute(
                    select(APIEndpoint).where(
                        APIEndpoint.path == endpoint_data["path"],
                        APIEndpoint.method == endpoint_data["method"]
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    endpoint = APIEndpoint(**endpoint_data)
                    db.add(endpoint)
                    Logger.info(f"创建API端点: {endpoint_data['method']} {endpoint_data['path']}")
                else:
                    Logger.info(f"API端点已存在: {endpoint_data['method']} {endpoint_data['path']}")
            
            await db.commit()
            Logger.info("API端点信息创建完成")
            
        except Exception as e:
            await db.rollback()
            Logger.error(f"创建API端点信息失败: {str(e)}")
            raise

async def main():
    """主函数"""
    try:
        Logger.info("开始初始化集成管理系统...")
        
        # 创建默认集成模板
        await create_default_integration_templates()
        
        # 创建默认API文档
        await create_default_api_documentation()
        
        # 创建API端点信息
        await create_api_endpoints()
        
        Logger.info("集成管理系统初始化完成!")
        Logger.info("集成管理功能包括:")
        Logger.info("- API密钥管理")
        Logger.info("- Webhook管理和事件通知")
        Logger.info("- 第三方集成 (8个预定义模板)")
        Logger.info("- API文档管理 (5个默认文档)")
        Logger.info("- API端点监控")
        Logger.info("- 使用统计和分析")
        Logger.info("- 集成模板库")
        
    except Exception as e:
        Logger.error(f"集成管理系统初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
