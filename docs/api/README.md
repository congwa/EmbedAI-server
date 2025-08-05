# EmbedAI 管理后台 API 文档

## 概述

EmbedAI管理后台提供了完整的RESTful API接口，支持用户管理、知识库管理、分析报告、系统监控等功能。所有API都遵循统一的响应格式和认证机制。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证机制

### JWT Token 认证

所有需要认证的API都需要在请求头中包含JWT token：

```http
Authorization: Bearer <your_jwt_token>
```

### 获取Token

```http
POST /api/v1/admin/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "your_password"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "is_admin": true
    }
  },
  "message": "登录成功"
}
```

## 统一响应格式

所有API响应都遵循以下格式：

### 成功响应
```json
{
  "success": true,
  "data": <响应数据>,
  "message": "操作成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "请求参数错误",
    "details": "具体错误信息"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

## HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或token无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

## API模块分类

### 1. 认证管理 (`/admin/auth`)
- 用户登录、登出
- Token刷新
- 密码重置

### 2. 用户管理 (`/admin/users`)
- 用户CRUD操作
- 用户状态管理
- 批量操作

### 3. 知识库管理 (`/admin/knowledge-bases`)
- 知识库CRUD操作
- 文档管理
- 训练状态管理

### 4. 分析报告 (`/admin/analytics`)
- 系统概览数据
- 用户活动统计
- 性能指标分析
- 数据导出

### 5. 系统健康监控 (`/admin/health`)
- 系统健康检查
- 性能监控
- 告警管理

### 6. 系统配置 (`/admin/config`)
- 系统参数配置
- 环境变量管理
- 配置备份恢复

### 7. 安全管理 (`/admin/security`)
- IP白名单/黑名单
- 安全事件监控
- 双因子认证

### 8. 内容管理 (`/admin/content`)
- 内容审核规则
- 批量操作
- 内容统计

### 9. 集成管理 (`/admin/integrations`)
- API密钥管理
- Webhook配置
- 第三方集成

### 10. 权限管理 (`/admin/rbac`)
- 角色权限管理
- 用户组管理
- 权限分配

## 分页参数

支持分页的API使用以下标准参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码，从1开始 |
| size | integer | 20 | 每页数量，最大100 |
| sort | string | "id" | 排序字段 |
| order | string | "asc" | 排序方向：asc/desc |

**分页响应格式**:
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 过滤和搜索

支持过滤的API使用以下参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| search | string | 关键词搜索 |
| filter | object | 字段过滤条件 |
| date_from | string | 开始日期 (ISO 8601) |
| date_to | string | 结束日期 (ISO 8601) |

## 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| AUTH_001 | Token已过期 | 重新登录获取新token |
| AUTH_002 | Token无效 | 检查token格式 |
| AUTH_003 | 权限不足 | 联系管理员分配权限 |
| VALID_001 | 参数验证失败 | 检查请求参数格式 |
| VALID_002 | 必填参数缺失 | 补充必填参数 |
| RESOURCE_001 | 资源不存在 | 检查资源ID是否正确 |
| RESOURCE_002 | 资源已存在 | 使用不同的标识符 |

## 速率限制

为了保护系统稳定性，API实施了速率限制：

- **普通用户**: 每分钟100次请求
- **管理员用户**: 每分钟500次请求
- **系统级API**: 每分钟1000次请求

超出限制时返回HTTP 429状态码。

## 开发工具

### Postman集合
我们提供了完整的Postman集合文件，包含所有API的示例请求。

### OpenAPI规范
系统自动生成OpenAPI 3.0规范文档，可通过以下地址访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## 版本控制

API版本通过URL路径进行控制：
- 当前版本: `v1`
- 版本格式: `/api/v{version}`

## 联系支持

如有API使用问题，请联系：
- 技术支持邮箱: support@embedai.com
- 开发者文档: https://docs.embedai.com
- GitHub Issues: https://github.com/embedai/admin-backend/issues

---

**注意**: 本文档持续更新，请关注最新版本。
