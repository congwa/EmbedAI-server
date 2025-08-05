# 用户管理 API

## 概述

用户管理API提供完整的用户CRUD操作，包括用户创建、查询、更新、删除以及批量操作功能。

## 基础路径

```
/api/v1/admin/users
```

## API端点列表

### 1. 获取用户列表

**端点**: `GET /`

**描述**: 获取系统中所有用户的分页列表，支持搜索和过滤

**权限要求**: 管理员权限

**请求头**:
```http
Authorization: Bearer <your_jwt_token>
```

**查询参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 | 示例 |
|--------|------|------|--------|------|------|
| page | integer | 否 | 1 | 页码，从1开始 | 1 |
| size | integer | 否 | 20 | 每页数量，最大100 | 20 |
| search | string | 否 | - | 搜索关键词（邮箱） | "admin" |
| is_active | boolean | 否 | - | 过滤活跃状态 | true |
| is_admin | boolean | 否 | - | 过滤管理员状态 | false |
| sort | string | 否 | "id" | 排序字段 | "created_at" |
| order | string | 否 | "asc" | 排序方向 | "desc" |

**请求示例**:
```http
GET /api/v1/admin/users?page=1&size=10&search=admin&is_active=true&sort=created_at&order=desc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "email": "admin@example.com",
        "is_admin": true,
        "is_active": true,
        "sdk_key": "sk_test_1234567890abcdef",
        "secret_key": "sk_secret_abcdef1234567890",
        "created_at": "2024-01-01T00:00:00Z",
        "last_login": "2024-08-05T10:00:00Z",
        "login_count": 42
      },
      {
        "id": 2,
        "email": "user@example.com",
        "is_admin": false,
        "is_active": true,
        "sdk_key": "sk_test_0987654321fedcba",
        "secret_key": "sk_secret_fedcba0987654321",
        "created_at": "2024-01-02T00:00:00Z",
        "last_login": "2024-08-04T15:30:00Z",
        "login_count": 15
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 25,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    }
  },
  "message": "获取用户列表成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 2. 获取单个用户详情

**端点**: `GET /{user_id}`

**描述**: 根据用户ID获取用户的详细信息

**权限要求**: 管理员权限

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

**请求示例**:
```http
GET /api/v1/admin/users/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "admin@example.com",
    "is_admin": true,
    "is_active": true,
    "sdk_key": "sk_test_1234567890abcdef",
    "secret_key": "sk_secret_abcdef1234567890",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-08-05T10:00:00Z",
    "login_count": 42,
    "knowledge_bases": [
      {
        "id": 1,
        "name": "技术文档库",
        "domain": "技术支持",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "recent_activities": [
      {
        "activity_type": "login",
        "timestamp": "2024-08-05T10:00:00Z",
        "ip_address": "192.168.1.100"
      }
    ]
  },
  "message": "获取用户详情成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

**错误响应**:

- **404 Not Found** - 用户不存在:
```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "用户不存在",
    "details": "User with id 999 not found"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 3. 创建新用户

**端点**: `POST /`

**描述**: 创建新的用户账户

**权限要求**: 管理员权限

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 | 约束 |
|--------|------|------|------|------|
| email | string | 是 | 用户邮箱 | 必须是有效的邮箱格式，系统内唯一 |
| password | string | 是 | 用户密码 | 长度8-128位，包含字母和数字 |
| is_admin | boolean | 否 | 是否为管理员 | 默认false |

**请求示例**:
```http
POST /api/v1/admin/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "is_admin": false
}
```

**成功响应** (201):
```json
{
  "success": true,
  "data": {
    "id": 3,
    "email": "newuser@example.com",
    "is_admin": false,
    "is_active": true,
    "sdk_key": "sk_test_newuser123456789",
    "secret_key": "sk_secret_newuser987654321",
    "created_at": "2024-08-05T10:30:00Z"
  },
  "message": "用户创建成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

**错误响应**:

- **400 Bad Request** - 邮箱已存在:
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "邮箱已存在",
    "details": "Email already exists"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 4. 更新用户信息

**端点**: `PUT /{user_id}`

**描述**: 更新指定用户的信息

**权限要求**: 管理员权限

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 | 约束 |
|--------|------|------|------|------|
| email | string | 否 | 新邮箱地址 | 必须是有效的邮箱格式 |
| password | string | 否 | 新密码 | 长度8-128位，包含字母和数字 |

**请求示例**:
```http
PUT /api/v1/admin/users/3
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "email": "updated@example.com",
  "password": "NewPassword456!"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 3,
    "email": "updated@example.com",
    "is_admin": false,
    "is_active": true,
    "sdk_key": "sk_test_newuser123456789",
    "secret_key": "sk_secret_newuser987654321",
    "created_at": "2024-08-05T10:30:00Z",
    "updated_at": "2024-08-05T11:00:00Z"
  },
  "message": "用户信息更新成功",
  "timestamp": "2024-08-05T11:00:00Z"
}
```

### 5. 更新用户状态

**端点**: `PATCH /{user_id}/status`

**描述**: 启用或禁用用户账户

**权限要求**: 管理员权限

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| is_active | boolean | 是 | 用户状态 |

**请求示例**:
```http
PATCH /api/v1/admin/users/3/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "is_active": false
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 3,
    "email": "updated@example.com",
    "is_admin": false,
    "is_active": false,
    "updated_at": "2024-08-05T11:15:00Z"
  },
  "message": "用户状态更新成功",
  "timestamp": "2024-08-05T11:15:00Z"
}
```

### 6. 删除用户

**端点**: `DELETE /{user_id}`

**描述**: 删除指定的用户账户（软删除）

**权限要求**: 管理员权限

**路径参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| user_id | integer | 是 | 用户ID |

**请求示例**:
```http
DELETE /api/v1/admin/users/3
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": null,
  "message": "用户删除成功",
  "timestamp": "2024-08-05T11:30:00Z"
}
```

**错误响应**:

- **400 Bad Request** - 不能删除自己:
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "不能删除自己的账户",
    "details": "Cannot delete your own account"
  },
  "timestamp": "2024-08-05T11:30:00Z"
}
```

### 7. 批量操作

**端点**: `POST /batch`

**描述**: 对多个用户执行批量操作

**权限要求**: 管理员权限

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| user_ids | array[integer] | 是 | 用户ID列表 |
| action | string | 是 | 操作类型：activate, deactivate, delete |

**请求示例**:
```http
POST /api/v1/admin/users/batch
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "user_ids": [4, 5, 6],
  "action": "deactivate"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "processed": 3,
    "failed": 0,
    "results": [
      {"user_id": 4, "status": "success"},
      {"user_id": 5, "status": "success"},
      {"user_id": 6, "status": "success"}
    ]
  },
  "message": "批量操作完成",
  "timestamp": "2024-08-05T11:45:00Z"
}
```

## 使用示例

### JavaScript示例

```javascript
// 获取用户列表
async function getUsers(page = 1, size = 20, search = '') {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    page: page.toString(),
    size: size.toString(),
    ...(search && { search })
  });
  
  const response = await fetch(`/api/v1/admin/users?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// 创建用户
async function createUser(userData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/admin/users', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  });
  
  return await response.json();
}
```

### Python示例

```python
import requests

class UserAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get_users(self, page=1, size=20, search=None):
        params = {'page': page, 'size': size}
        if search:
            params['search'] = search
            
        response = requests.get(
            f'{self.base_url}/admin/users',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def create_user(self, email, password, is_admin=False):
        data = {
            'email': email,
            'password': password,
            'is_admin': is_admin
        }
        
        response = requests.post(
            f'{self.base_url}/admin/users',
            headers=self.headers,
            json=data
        )
        return response.json()
```
