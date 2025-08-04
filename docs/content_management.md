# Content & Data Management

## Overview

The Content & Data Management module provides comprehensive tools for managing, moderating, organizing, and analyzing content within the system. It offers advanced features including automated content moderation, bulk operations, sophisticated search capabilities, data export functionality, and detailed analytics.

## Core Features

### 1. Content Moderation System
- **Automated Rules Engine**: 5 pre-configured moderation rules for content quality control
- **Manual Moderation**: Human review and approval workflows
- **Multi-criteria Filtering**: Keyword filtering, length validation, duplicate detection
- **Security Checks**: Link safety validation and image content analysis
- **Audit Trail**: Complete moderation history with detailed logs

### 2. Content Organization
- **Tag System**: 12 default tags with color-coded categories
- **Category Management**: 6-level hierarchical categorization system
- **Metadata Management**: Rich metadata support for all content types
- **Content Classification**: Automatic and manual content classification

### 3. Bulk Operations
- **Mass Actions**: Delete, archive, publish, approve, reject operations
- **Progress Tracking**: Real-time progress monitoring for bulk tasks
- **Error Handling**: Detailed error reporting and recovery mechanisms
- **Background Processing**: Asynchronous execution for large datasets

### 4. Advanced Search
- **Full-text Search**: Comprehensive content indexing and search
- **Faceted Search**: Multi-dimensional filtering capabilities
- **Relevance Scoring**: Intelligent ranking and scoring algorithms
- **Search Analytics**: Query performance and usage statistics

### 5. Data Export & Analytics
- **Multiple Formats**: CSV, JSON, XML export capabilities
- **Filtered Exports**: Custom data selection and filtering
- **Scheduled Exports**: Automated recurring export tasks
- **Analytics Dashboard**: Content performance and usage insights

## Content Moderation Rules

### Pre-configured Rules (5 rules)

#### 1. Keyword Filtering (Priority: 100)
```json
{
  "name": "敏感词过滤",
  "rule_type": "keyword_filter",
  "conditions": {
    "keywords": ["spam", "abuse", "inappropriate"],
    "case_sensitive": false,
    "match_type": "contains"
  },
  "actions": {
    "action": "flag",
    "severity": "medium",
    "auto_apply": true
  }
}
```

#### 2. Content Length Validation (Priority: 90)
```json
{
  "name": "内容长度检查",
  "rule_type": "length_check",
  "conditions": {
    "min_length": 10,
    "max_length": 10000,
    "check_title": true,
    "check_content": true
  },
  "actions": {
    "action": "reject",
    "reason": "内容长度不符合要求",
    "auto_apply": false
  }
}
```

#### 3. Duplicate Content Detection (Priority: 80)
```json
{
  "name": "重复内容检测",
  "rule_type": "duplicate_check",
  "conditions": {
    "similarity_threshold": 0.8,
    "check_title": true,
    "check_content": true,
    "time_window": 86400
  },
  "actions": {
    "action": "flag",
    "severity": "low",
    "auto_apply": true
  }
}
```

#### 4. Link Safety Check (Priority: 95)
```json
{
  "name": "链接安全检查",
  "rule_type": "link_safety",
  "conditions": {
    "check_malicious_domains": true,
    "check_phishing": true,
    "allowed_domains": ["example.com", "trusted-site.com"],
    "blocked_domains": ["malicious-site.com"]
  },
  "actions": {
    "action": "remove",
    "reason": "包含不安全链接",
    "auto_apply": true
  }
}
```

#### 5. Image Content Moderation (Priority: 85)
```json
{
  "name": "图片内容审核",
  "rule_type": "image_moderation",
  "conditions": {
    "check_adult_content": true,
    "check_violence": true,
    "confidence_threshold": 0.7
  },
  "actions": {
    "action": "flag",
    "severity": "high",
    "auto_apply": false
  }
}
```

## Content Tags System

### Default Tags (12 tags)

#### By Category

**主题 (Topics)**
- 技术 (#007bff) - Technical content
- 重要 (#dc3545) - Important content

**类型 (Types)**
- 教程 (#28a745) - Tutorials and guides
- 文档 (#6c757d) - Documentation

**技术 (Technology)**
- API (#17a2b8) - API related
- 数据库 (#ffc107) - Database related
- 前端 (#e83e8c) - Frontend development
- 后端 (#6f42c1) - Backend development
- AI (#fd7e14) - Artificial Intelligence
- 机器学习 (#20c997) - Machine Learning

**状态 (Status)**
- 草稿 (#6c757d) - Draft status
- 已发布 (#28a745) - Published content

## Content Categories

### Hierarchical Structure (6 categories)

1. **技术文档** (tech-docs) 📚
   - Technical documentation and resources
   - Color: #007bff

2. **API文档** (api-docs) 🔌
   - API interface documentation
   - Color: #17a2b8

3. **用户指南** (user-guides) 📖
   - User guides and tutorials
   - Color: #28a745

4. **开发指南** (dev-guides) 💻
   - Developer guides and best practices
   - Color: #6f42c1

5. **常见问题** (faq) ❓
   - Frequently asked questions
   - Color: #ffc107

6. **发布说明** (release-notes) 📝
   - Release notes and changelogs
   - Color: #fd7e14

## API Endpoints

### Content Dashboard

#### Get Content Dashboard
```http
GET /api/v1/admin/content/dashboard
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_content": 150,
    "published_content": 120,
    "pending_moderation": 15,
    "total_categories": 6,
    "total_tags": 12,
    "active_bulk_operations": 2,
    "recent_moderation_logs": [...],
    "content_by_status": {
      "kb_published": 45,
      "kb_draft": 10,
      "doc_processed": 75,
      "doc_pending": 20
    },
    "content_by_type": {
      "knowledge_bases": 55,
      "documents": 95
    },
    "top_categories": [...],
    "top_tags": [...]
  }
}
```

### Content Moderation

#### Create Moderation Rule
```http
POST /api/v1/admin/content/moderation/rules
```

**Request Body:**
```json
{
  "name": "Custom Rule",
  "description": "Custom moderation rule",
  "rule_type": "custom_filter",
  "conditions": {
    "keywords": ["test", "example"],
    "case_sensitive": false
  },
  "actions": {
    "action": "flag",
    "severity": "low"
  },
  "priority": 50,
  "auto_apply": true
}
```

#### Moderate Content
```http
POST /api/v1/admin/content/moderation/moderate
```

**Request Body:**
```json
{
  "content_type": "knowledge_base",
  "content_id": 123,
  "action": "approve",
  "reason": "Content meets quality standards",
  "details": {
    "reviewer_notes": "Well-structured and informative"
  }
}
```

#### Get Moderation Logs
```http
GET /api/v1/admin/content/moderation/logs?content_type=knowledge_base&action=approve
```

### Bulk Operations

#### Create Bulk Operation
```http
POST /api/v1/admin/content/bulk-operations
```

**Request Body:**
```json
{
  "name": "Archive Old Content",
  "operation_type": "archive",
  "target_type": "knowledge_base",
  "target_ids": [1, 2, 3, 4, 5],
  "parameters": {
    "reason": "Content outdated",
    "notify_owners": true
  }
}
```

#### Get Bulk Operation Status
```http
GET /api/v1/admin/content/bulk-operations/{operation_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Archive Old Content",
    "operation_type": "archive",
    "status": "running",
    "progress": 60,
    "total_items": 5,
    "processed_items": 3,
    "success_items": 3,
    "failed_items": 0,
    "started_at": "2024-08-04T12:00:00Z",
    "estimated_completion": "2024-08-04T12:05:00Z"
  }
}
```

### Tag Management

#### Create Tag
```http
POST /api/v1/admin/content/tags
```

**Request Body:**
```json
{
  "name": "新技术",
  "description": "新兴技术相关内容",
  "color": "#ff6b6b",
  "category": "技术"
}
```

#### Get Tags
```http
GET /api/v1/admin/content/tags?category=技术&is_active=true
```

#### Batch Tag Operation
```http
POST /api/v1/admin/content/tags/batch-operation
```

**Request Body:**
```json
{
  "content_ids": [1, 2, 3],
  "tag_ids": [10, 11],
  "operation": "add"
}
```

### Category Management

#### Create Category
```http
POST /api/v1/admin/content/categories
```

**Request Body:**
```json
{
  "name": "移动开发",
  "slug": "mobile-dev",
  "description": "移动应用开发相关内容",
  "parent_id": 4,
  "icon": "📱",
  "color": "#9c27b0",
  "sort_order": 10
}
```

#### Get Categories Tree
```http
GET /api/v1/admin/content/categories
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "技术文档",
      "slug": "tech-docs",
      "level": 0,
      "children": [
        {
          "id": 7,
          "name": "移动开发",
          "slug": "mobile-dev",
          "level": 1,
          "children": []
        }
      ]
    }
  ]
}
```

### Advanced Search

#### Search Content
```http
POST /api/v1/admin/content/search
```

**Request Body:**
```json
{
  "query": "API documentation",
  "content_types": ["knowledge_base", "document"],
  "categories": [1, 2],
  "tags": [10, 11],
  "status": ["published"],
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-08-04T23:59:59Z",
  "sort_by": "relevance",
  "sort_order": "desc",
  "page": 1,
  "page_size": 20
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "API documentation",
    "total_count": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "results": [
      {
        "content_type": "knowledge_base",
        "content_id": 123,
        "title": "REST API Documentation",
        "snippet": "Complete guide to our REST API...",
        "score": 0.95,
        "metadata": {
          "training_status": "completed",
          "created_at": "2024-07-15T10:30:00Z"
        },
        "url": "/knowledge_base/123"
      }
    ],
    "search_time": 0.045
  }
}
```

### Data Export

#### Create Export Task
```http
POST /api/v1/admin/content/exports
```

**Request Body:**
```json
{
  "name": "Knowledge Base Export",
  "export_type": "full",
  "data_type": "knowledge_bases",
  "filters": {
    "status": ["published"],
    "created_from": "2024-01-01T00:00:00Z",
    "created_to": "2024-08-04T23:59:59Z"
  },
  "format": "csv",
  "include_headers": true,
  "date_format": "ISO"
}
```

#### Get Export Tasks
```http
GET /api/v1/admin/content/exports?status=completed&data_type=knowledge_bases
```

#### Download Export File
```http
GET /api/v1/admin/content/exports/{task_id}/download
```

## Database Schema

### Content Management Tables (8 tables)

1. **content_moderation_rules** - Moderation rule definitions
2. **content_moderation_logs** - Moderation action history
3. **bulk_operations** - Bulk operation tracking
4. **content_tags** - Tag management
5. **content_categories** - Category hierarchy
6. **search_indexes** - Full-text search indexes
7. **content_statistics** - Content analytics data
8. **data_export_tasks** - Export task management

## Usage Examples

### Content Moderation Workflow
```python
from app.services.content import ContentService

# Create moderation rule
rule_data = ContentModerationRuleCreate(
    name="Quality Check",
    rule_type="quality_filter",
    conditions={"min_words": 50},
    actions={"action": "flag"}
)
rule = await content_service.create_moderation_rule(rule_data, admin_id)

# Moderate content
moderation_request = ContentModerationRequest(
    content_type="knowledge_base",
    content_id=123,
    action=ModerationAction.APPROVE,
    reason="High quality content"
)
log = await content_service.moderate_content(moderation_request, moderator_id)
```

### Bulk Operations
```python
# Create bulk operation
operation_data = BulkOperationCreate(
    name="Archive Old Content",
    operation_type=BulkOperationType.ARCHIVE,
    target_type="knowledge_base",
    target_ids=[1, 2, 3, 4, 5]
)
operation = await content_service.create_bulk_operation(operation_data, admin_id)
```

### Advanced Search
```python
# Perform advanced search
search_request = SearchRequest(
    query="machine learning",
    content_types=["knowledge_base"],
    sort_by="relevance",
    page=1,
    page_size=20
)
results = await content_service.advanced_search(search_request)
```

### Data Export
```python
# Create export task
export_request = DataExportRequest(
    name="Monthly Report",
    export_type="filtered",
    data_type="knowledge_bases",
    format="csv"
)
task = await content_service.create_export_task(export_request, admin_id)
```

## Best Practices

### Content Moderation
1. **Rule Prioritization**: Set appropriate priorities for moderation rules
2. **Automated vs Manual**: Balance automation with human oversight
3. **Regular Review**: Periodically review and update moderation rules
4. **Performance Monitoring**: Track moderation effectiveness and accuracy

### Content Organization
1. **Consistent Tagging**: Establish and maintain consistent tagging conventions
2. **Category Hierarchy**: Design logical and intuitive category structures
3. **Metadata Standards**: Define clear metadata standards for all content types
4. **Regular Cleanup**: Periodically review and clean up unused tags/categories

### Search Optimization
1. **Index Maintenance**: Regularly update and optimize search indexes
2. **Relevance Tuning**: Fine-tune search relevance algorithms
3. **Performance Monitoring**: Monitor search performance and response times
4. **User Feedback**: Collect and analyze user search behavior

### Data Management
1. **Export Scheduling**: Set up regular automated exports for backup
2. **Data Retention**: Implement appropriate data retention policies
3. **Performance Optimization**: Optimize bulk operations for large datasets
4. **Error Handling**: Implement robust error handling and recovery mechanisms

## Integration Points

### With Security Module
- Content access control and permissions
- Audit logging for content operations
- User authentication for moderation actions

### With User Management
- User role-based content moderation
- Content ownership and collaboration
- Activity tracking and analytics

### With Knowledge Base
- Content indexing and search integration
- Automated content classification
- Quality scoring and recommendations

## Troubleshooting

### Common Issues

1. **Slow Search Performance**
   - Check search index status
   - Optimize query complexity
   - Consider index rebuilding

2. **Bulk Operation Failures**
   - Review error logs and details
   - Check system resource availability
   - Verify target content accessibility

3. **Moderation Rule Conflicts**
   - Review rule priorities and conditions
   - Check for overlapping rule logic
   - Test rules with sample content

4. **Export Task Timeouts**
   - Reduce export scope or add filters
   - Check system performance and resources
   - Consider breaking into smaller exports

### Debugging Commands

```python
# Check content statistics
dashboard = await content_service.get_content_dashboard()

# Review moderation logs
logs = await content_service.get_moderation_logs(content_type="knowledge_base")

# Monitor bulk operations
operations = await content_service.get_bulk_operations(status="running")

# Analyze search performance
search_stats = await content_service.get_search_statistics()
```
