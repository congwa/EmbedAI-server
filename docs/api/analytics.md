# 分析报告 API

## 概述

分析报告API提供系统的各种统计数据和分析报告，包括用户活动、系统性能、知识库使用情况等。

## 基础路径

```
/api/v1/admin/analytics
```

## API端点列表

### 1. 获取仪表板数据

**端点**: `GET /dashboard`

**描述**: 获取管理员仪表板所需的所有关键指标和统计信息

**权限要求**: 管理员权限

**请求头**:
```http
Authorization: Bearer <your_jwt_token>
```

**请求参数**: 无

**请求示例**:
```http
GET /api/v1/admin/analytics/dashboard
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_users": 150,
      "active_users": 89,
      "total_knowledge_bases": 25,
      "total_documents": 1250,
      "total_queries": 5680,
      "system_uptime": 99.8
    },
    "recent_activities": [
      {
        "user_id": 1,
        "user_email": "admin@example.com",
        "activity_type": "document_upload",
        "activity_details": {
          "document_name": "API文档.pdf",
          "knowledge_base": "技术文档库"
        },
        "timestamp": "2024-08-05T10:25:00Z"
      }
    ],
    "top_knowledge_bases": [
      {
        "id": 1,
        "name": "技术文档库",
        "domain": "技术支持",
        "document_count": 45,
        "query_count": 1250,
        "last_updated": "2024-08-05T09:30:00Z"
      }
    ],
    "performance_trends": {
      "dates": ["2024-07-29", "2024-07-30", "2024-07-31", "2024-08-01", "2024-08-02", "2024-08-03", "2024-08-04"],
      "response_times": [120, 115, 130, 125, 118, 122, 119],
      "query_counts": [450, 520, 480, 600, 580, 650, 720],
      "error_rates": [0.5, 0.3, 0.8, 0.4, 0.2, 0.6, 0.3]
    },
    "cost_summary": {
      "current_month": {
        "total_cost": 1250.50,
        "llm_cost": 980.30,
        "storage_cost": 150.20,
        "api_cost": 120.00
      },
      "previous_month": {
        "total_cost": 1180.20,
        "growth_rate": 5.96
      }
    }
  },
  "message": "获取仪表板数据成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 2. 获取系统概览

**端点**: `GET /overview`

**描述**: 获取系统的整体概览统计数据

**权限要求**: 管理员权限

**查询参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| period | string | 否 | "7d" | 统计周期：1d, 7d, 30d, 90d |

**请求示例**:
```http
GET /api/v1/admin/analytics/overview?period=30d
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "total_users": 150,
    "new_users": 12,
    "active_users": 89,
    "total_knowledge_bases": 25,
    "new_knowledge_bases": 3,
    "total_documents": 1250,
    "new_documents": 85,
    "total_queries": 15680,
    "successful_queries": 15234,
    "failed_queries": 446,
    "average_response_time": 125.5,
    "system_uptime": 99.8,
    "storage_used": "2.5GB",
    "bandwidth_used": "150GB"
  },
  "message": "获取系统概览成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 3. 获取用户活动统计

**端点**: `GET /user-activity`

**描述**: 获取用户活动的详细统计信息

**权限要求**: 管理员权限

**查询参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| start_date | string | 否 | 7天前 | 开始日期 (ISO 8601) |
| end_date | string | 否 | 今天 | 结束日期 (ISO 8601) |
| user_id | integer | 否 | - | 特定用户ID |
| activity_type | string | 否 | - | 活动类型过滤 |
| limit | integer | 否 | 100 | 返回记录数限制 |

**请求示例**:
```http
GET /api/v1/admin/analytics/user-activity?start_date=2024-08-01&end_date=2024-08-05&limit=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-08-01T00:00:00Z",
      "end_date": "2024-08-05T23:59:59Z"
    },
    "summary": {
      "total_activities": 2450,
      "unique_users": 89,
      "most_active_user": {
        "user_id": 5,
        "email": "power_user@example.com",
        "activity_count": 156
      }
    },
    "activity_breakdown": {
      "login": 245,
      "document_upload": 89,
      "knowledge_base_create": 12,
      "query_submit": 1850,
      "settings_update": 34,
      "logout": 220
    },
    "daily_trends": [
      {
        "date": "2024-08-01",
        "total_activities": 580,
        "unique_users": 45
      },
      {
        "date": "2024-08-02",
        "total_activities": 620,
        "unique_users": 52
      }
    ],
    "recent_activities": [
      {
        "id": 12345,
        "user_id": 1,
        "user_email": "admin@example.com",
        "activity_type": "document_upload",
        "activity_details": {
          "document_name": "新产品手册.pdf",
          "knowledge_base_id": 3,
          "file_size": "2.5MB"
        },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "timestamp": "2024-08-05T10:25:00Z",
        "duration": 45
      }
    ]
  },
  "message": "获取用户活动统计成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 4. 获取知识库统计

**端点**: `GET /knowledge-bases`

**描述**: 获取知识库的使用统计和性能数据

**权限要求**: 管理员权限

**查询参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| period | string | 否 | "7d" | 统计周期 |
| sort_by | string | 否 | "query_count" | 排序字段 |
| limit | integer | 否 | 20 | 返回数量限制 |

**请求示例**:
```http
GET /api/v1/admin/analytics/knowledge-bases?period=30d&sort_by=query_count&limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "summary": {
      "total_knowledge_bases": 25,
      "active_knowledge_bases": 18,
      "total_documents": 1250,
      "total_queries": 15680,
      "average_accuracy": 92.5
    },
    "top_knowledge_bases": [
      {
        "id": 1,
        "name": "技术文档库",
        "domain": "技术支持",
        "document_count": 45,
        "total_size": "125MB",
        "query_count": 3250,
        "successful_queries": 3180,
        "failed_queries": 70,
        "accuracy_rate": 97.8,
        "average_response_time": 115,
        "last_updated": "2024-08-05T09:30:00Z",
        "created_at": "2024-01-15T00:00:00Z"
      }
    ],
    "usage_trends": {
      "dates": ["2024-07-29", "2024-07-30", "2024-07-31", "2024-08-01", "2024-08-02"],
      "query_counts": [450, 520, 480, 600, 580],
      "accuracy_rates": [92.1, 93.5, 91.8, 94.2, 93.7]
    }
  },
  "message": "获取知识库统计成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 5. 获取性能指标

**端点**: `GET /performance`

**描述**: 获取系统性能相关的指标数据

**权限要求**: 管理员权限

**查询参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| start_date | string | 否 | 7天前 | 开始日期 |
| end_date | string | 否 | 今天 | 结束日期 |
| metric_type | string | 否 | - | 指标类型过滤 |
| granularity | string | 否 | "hour" | 数据粒度：hour, day |

**请求示例**:
```http
GET /api/v1/admin/analytics/performance?start_date=2024-08-01&granularity=day
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-08-01T00:00:00Z",
      "end_date": "2024-08-05T23:59:59Z",
      "granularity": "day"
    },
    "summary": {
      "average_response_time": 125.5,
      "max_response_time": 2500,
      "min_response_time": 45,
      "total_requests": 15680,
      "successful_requests": 15234,
      "error_rate": 2.84,
      "uptime_percentage": 99.8
    },
    "metrics": [
      {
        "timestamp": "2024-08-01T00:00:00Z",
        "response_time": 120,
        "request_count": 3200,
        "error_count": 45,
        "cpu_usage": 65.2,
        "memory_usage": 78.5,
        "disk_usage": 45.8
      }
    ],
    "alerts": [
      {
        "timestamp": "2024-08-03T14:30:00Z",
        "type": "high_response_time",
        "value": 2500,
        "threshold": 2000,
        "severity": "warning"
      }
    ]
  },
  "message": "获取性能指标成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 6. 获取成本分析

**端点**: `GET /cost-analysis`

**描述**: 获取系统运营成本的详细分析

**权限要求**: 管理员权限

**查询参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| start_date | string | 否 | 30天前 | 开始日期 |
| end_date | string | 否 | 今天 | 结束日期 |
| breakdown | string | 否 | "service" | 分解维度：service, user, knowledge_base |

**请求示例**:
```http
GET /api/v1/admin/analytics/cost-analysis?start_date=2024-07-01&breakdown=service
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-07-01T00:00:00Z",
      "end_date": "2024-08-05T23:59:59Z"
    },
    "total_cost": 4250.75,
    "cost_breakdown": {
      "llm_api": {
        "cost": 3200.50,
        "percentage": 75.3,
        "requests": 45680,
        "cost_per_request": 0.07
      },
      "storage": {
        "cost": 450.25,
        "percentage": 10.6,
        "storage_gb": 150.5,
        "cost_per_gb": 2.99
      },
      "compute": {
        "cost": 380.00,
        "percentage": 8.9,
        "hours": 760,
        "cost_per_hour": 0.50
      },
      "bandwidth": {
        "cost": 220.00,
        "percentage": 5.2,
        "gb_transferred": 2200,
        "cost_per_gb": 0.10
      }
    },
    "daily_costs": [
      {
        "date": "2024-08-01",
        "total_cost": 125.50,
        "llm_cost": 95.20,
        "storage_cost": 15.30,
        "compute_cost": 10.00,
        "bandwidth_cost": 5.00
      }
    ],
    "projections": {
      "monthly_estimate": 1350.25,
      "yearly_estimate": 16203.00,
      "growth_rate": 12.5
    }
  },
  "message": "获取成本分析成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 7. 导出分析数据

**端点**: `POST /export`

**描述**: 导出分析数据为CSV或Excel格式

**权限要求**: 管理员权限

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| data_type | string | 是 | 数据类型：user_activity, knowledge_bases, performance, cost |
| format | string | 否 | 导出格式：csv, excel，默认csv |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| filters | object | 否 | 额外过滤条件 |

**请求示例**:
```http
POST /api/v1/admin/analytics/export
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "data_type": "user_activity",
  "format": "csv",
  "start_date": "2024-08-01",
  "end_date": "2024-08-05",
  "filters": {
    "activity_type": "query_submit"
  }
}
```

**成功响应** (200):
```http
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="user_activity_20240801_20240805.csv"

用户ID,邮箱,活动类型,时间戳,详情
1,admin@example.com,query_submit,2024-08-05T10:25:00Z,"查询内容: API文档"
2,user@example.com,query_submit,2024-08-05T10:20:00Z,"查询内容: 产品功能"
...
```

## 使用示例

### JavaScript示例

```javascript
// 获取仪表板数据
async function getDashboardData() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/admin/analytics/dashboard', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// 导出数据
async function exportData(dataType, format = 'csv', startDate, endDate) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/admin/analytics/export', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      data_type: dataType,
      format: format,
      start_date: startDate,
      end_date: endDate
    })
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${dataType}_export.${format}`;
    a.click();
  }
}
```
