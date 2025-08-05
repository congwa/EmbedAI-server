# 认证管理 API

## 概述

认证管理API提供用户登录、登出、Token刷新等功能。所有认证相关的操作都通过这个模块进行。

## 基础路径

```
/api/v1/admin/auth
```

## API端点列表

### 1. 用户登录

**端点**: `POST /login`

**描述**: 管理员用户登录，获取访问令牌

**权限要求**: 无（公开接口）

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 | 示例 |
|--------|------|------|------|------|
| email | string | 是 | 用户邮箱地址 | "admin@example.com" |
| password | string | 是 | 用户密码 | "SecurePassword123!" |

**请求示例**:
```http
POST /api/v1/admin/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "SecurePassword123!"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhZG1pbkBleGFtcGxlLmNvbSIsImlzX2FkbWluIjp0cnVlLCJleHAiOjE2OTEyMzQ1Njd9.abc123",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "is_admin": true,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  },
  "message": "登录成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

**错误响应**:

- **401 Unauthorized** - 邮箱或密码错误:
```json
{
  "success": false,
  "error": {
    "code": 401,
    "message": "邮箱或密码错误",
    "details": "Invalid email or password"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

- **403 Forbidden** - 账户被禁用:
```json
{
  "success": false,
  "error": {
    "code": 403,
    "message": "账户已被禁用",
    "details": "Account is disabled"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

- **422 Validation Error** - 参数验证失败:
```json
{
  "success": false,
  "error": {
    "code": 422,
    "message": "参数验证失败",
    "details": {
      "email": ["邮箱格式不正确"],
      "password": ["密码不能为空"]
    }
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 2. 用户登出

**端点**: `POST /logout`

**描述**: 用户登出，使当前Token失效

**权限要求**: 需要有效的JWT Token

**请求头**:
```http
Authorization: Bearer <your_jwt_token>
```

**请求参数**: 无

**请求示例**:
```http
POST /api/v1/admin/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": null,
  "message": "登出成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

**错误响应**:

- **401 Unauthorized** - Token无效或已过期:
```json
{
  "success": false,
  "error": {
    "code": 401,
    "message": "Token无效或已过期",
    "details": "Invalid or expired token"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 3. Token刷新

**端点**: `POST /refresh`

**描述**: 刷新访问令牌，延长登录状态

**权限要求**: 需要有效的JWT Token

**请求头**:
```http
Authorization: Bearer <your_jwt_token>
```

**请求参数**: 无

**请求示例**:
```http
POST /api/v1/admin/auth/refresh
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.newTokenContent.signature",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "is_admin": true,
      "is_active": true
    }
  },
  "message": "Token刷新成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 4. 获取当前用户信息

**端点**: `GET /me`

**描述**: 获取当前登录用户的详细信息

**权限要求**: 需要有效的JWT Token

**请求头**:
```http
Authorization: Bearer <your_jwt_token>
```

**请求参数**: 无

**请求示例**:
```http
GET /api/v1/admin/auth/me
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
    "login_count": 42
  },
  "message": "获取用户信息成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

### 5. 修改密码

**端点**: `PUT /change-password`

**描述**: 修改当前用户的密码

**权限要求**: 需要有效的JWT Token

**请求头**:
```http
Authorization: Bearer <your_jwt_token>
```

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 | 约束 |
|--------|------|------|------|------|
| current_password | string | 是 | 当前密码 | 必须与数据库中的密码匹配 |
| new_password | string | 是 | 新密码 | 长度8-128位，包含字母和数字 |
| confirm_password | string | 是 | 确认新密码 | 必须与new_password相同 |

**请求示例**:
```http
PUT /api/v1/admin/auth/change-password
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!",
  "confirm_password": "NewSecurePassword456!"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": null,
  "message": "密码修改成功",
  "timestamp": "2024-08-05T10:30:00Z"
}
```

**错误响应**:

- **400 Bad Request** - 当前密码错误:
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "当前密码错误",
    "details": "Current password is incorrect"
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

- **422 Validation Error** - 密码格式不符合要求:
```json
{
  "success": false,
  "error": {
    "code": 422,
    "message": "密码格式不符合要求",
    "details": {
      "new_password": ["密码长度至少8位"],
      "confirm_password": ["两次输入的密码不一致"]
    }
  },
  "timestamp": "2024-08-05T10:30:00Z"
}
```

## 安全注意事项

### 1. Token安全
- JWT Token包含敏感信息，请妥善保管
- Token有效期为1小时，过期后需要重新登录或刷新
- 建议在客户端安全存储Token（如HttpOnly Cookie）

### 2. 密码安全
- 密码在传输和存储时都经过加密处理
- 系统使用bcrypt算法进行密码哈希
- 建议使用强密码策略

### 3. 登录安全
- 系统记录所有登录尝试
- 多次登录失败会触发账户锁定
- 支持IP白名单限制

## 使用示例

### JavaScript/Fetch示例

```javascript
// 登录
async function login(email, password) {
  const response = await fetch('/api/v1/admin/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password })
  });
  
  const result = await response.json();
  if (result.success) {
    // 保存token
    localStorage.setItem('access_token', result.data.access_token);
    return result.data;
  } else {
    throw new Error(result.error.message);
  }
}

// 获取用户信息
async function getCurrentUser() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/admin/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Python/Requests示例

```python
import requests

# 登录
def login(email, password):
    response = requests.post(
        'http://localhost:8000/api/v1/admin/auth/login',
        json={'email': email, 'password': password}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data['data']['access_token']
    else:
        raise Exception(f"登录失败: {response.json()['error']['message']}")

# 使用token访问API
def get_current_user(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        'http://localhost:8000/api/v1/admin/auth/me',
        headers=headers
    )
    
    return response.json()
```
