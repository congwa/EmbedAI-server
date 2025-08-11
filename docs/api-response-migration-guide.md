# API响应系统迁移指南

## 概述

本项目已将API响应系统从基于`APIResponse.success()`和`APIResponse.error()`的模式迁移到现代化的异常驱动模式。新系统提供更清晰的代码结构、更好的错误处理和统一的响应格式。

## 新系统优势

1. **声明式错误处理** - 通过抛出异常来处理错误，代码更简洁
2. **统一响应格式** - 所有响应都有一致的格式
3. **更好的类型安全** - 异常类型明确，IDE支持更好
4. **集中异常处理** - 全局异常处理器统一处理所有异常
5. **更好的调试体验** - 详细的错误信息和追踪支持

## 快速迁移指南

### 1. 导入新的工具

```python
# 旧的导入（已废弃）
from app.core.response import APIResponse

# 新的导入
from app.core.response_utils import success_response, pagination_response, created_response
from app.core.exceptions_new import (
    ResourceNotFoundError,
    BusinessError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    SystemError
)
```

### 2. 成功响应迁移

#### 旧代码
```python
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await user_service.get_user(user_id)
    if not user:
        return APIResponse.error(message="用户不存在", code=404)
    return APIResponse.success(data=user, message="获取用户成功")
```

#### 新代码
```python
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await user_service.get_user(user_id)
    if not user:
        raise ResourceNotFoundError("用户", user_id)
    return success_response(data=user, message="获取用户成功")
```

### 3. 分页响应迁移

#### 旧代码
```python
@router.get("/users")
async def list_users(page: int = 1, page_size: int = 10):
    users, total = await user_service.get_users(page, page_size)
    return APIResponse.pagination(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    )
```

#### 新代码
```python
@router.get("/users")
async def list_users(page: int = 1, page_size: int = 10):
    users, total = await user_service.get_users(page, page_size)
    return pagination_response(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    )
```

### 4. 错误处理迁移

#### 旧代码
```python
@router.post("/users")
async def create_user(user_data: UserCreate):
    try:
        if await user_service.email_exists(user_data.email):
            return APIResponse.error(message="邮箱已存在", code=400)
        
        user = await user_service.create(user_data)
        return APIResponse.success(data=user, message="用户创建成功")
    except Exception as e:
        return APIResponse.error(message=str(e), code=500)
```

#### 新代码
```python
@router.post("/users")
async def create_user(user_data: UserCreate):
    if await user_service.email_exists(user_data.email):
        raise BusinessError("邮箱已存在")
    
    user = await user_service.create(user_data)
    return created_response(data=user, message="用户创建成功")
    # 异常会被全局异常处理器自动捕获和处理
```

## 异常类型选择指南

### 认证和权限异常
- `UnauthorizedError` - 用户未认证或认证失败
- `ForbiddenError` - 用户已认证但权限不足
- `InvalidTokenError` - 认证令牌无效或过期

```python
# 检查用户认证
if not current_user:
    raise UnauthorizedError("请先登录")

# 检查用户权限
if not current_user.is_admin:
    raise ForbiddenError("需要管理员权限")
```

### 资源相关异常
- `ResourceNotFoundError` - 请求的资源不存在
- `ResourceConflictError` - 资源冲突（如重复创建）

```python
# 资源不存在
user = await user_service.get(user_id)
if not user:
    raise ResourceNotFoundError("用户", user_id)

# 资源冲突
if await user_service.email_exists(email):
    raise ResourceConflictError("邮箱已被注册")
```

### 业务逻辑异常
- `BusinessError` - 通用业务逻辑错误
- `ValidationError` - 数据验证失败
- `InsufficientResourceError` - 资源不足（如库存不足）
- `OperationNotAllowedError` - 当前状态下不允许的操作

```python
# 业务规则验证
if order.quantity > product.stock:
    raise InsufficientResourceError(
        "库存",
        available=product.stock,
        required=order.quantity
    )

# 状态检查
if order.status == "completed":
    raise OperationNotAllowedError("已完成的订单无法修改")
```

### 系统异常
- `SystemError` - 系统内部错误
- `DatabaseError` - 数据库操作错误
- `ExternalServiceError` - 外部服务调用失败
- `ConfigurationError` - 配置错误

```python
# 系统错误（通常在service层抛出）
try:
    result = await external_api.call()
except Exception as e:
    raise ExternalServiceError("支付服务", original_exception=e)
```

## 响应工具函数

### success_response()
用于普通成功响应：
```python
return success_response(
    data={"id": 1, "name": "test"},
    message="操作成功"
)
```

### created_response()
用于资源创建成功响应（201状态码）：
```python
return created_response(
    data=new_user,
    message="用户创建成功"
)
```

### pagination_response()
用于分页数据响应：
```python
return pagination_response(
    items=users,
    total=100,
    page=1,
    page_size=10,
    message="获取用户列表成功"
)
```

### no_content_response()
用于删除等无需返回数据的操作（204状态码）：
```python
return no_content_response("删除成功")
```

### accepted_response()
用于异步任务响应（202状态码）：
```python
return accepted_response(
    message="任务已提交",
    task_id="task-123"
)
```

## 高级用法

### 自动响应装饰器
对于简单的路由函数，可以使用自动响应装饰器：

```python
from app.core.response_utils import auto_response

@auto_response(success_message="获取用户成功")
async def get_user(user_id: int):
    user = await user_service.get_user(user_id)
    if not user:
        raise ResourceNotFoundError("用户", user_id)
    return user  # 自动包装为标准响应格式
```

### 自定义异常数据
异常可以携带额外的上下文数据：

```python
raise ValidationError(
    "邮箱格式无效",
    field="email",
    value="invalid-email"
)

raise InsufficientResourceError(
    "库存",
    available=5,
    required=10
)
```

### 开发环境调试
在开发环境中，异常响应会包含更多调试信息：

```python
# 开发环境响应示例
{
    "success": false,
    "code": 500,
    "message": "系统内部错误",
    "data": {
        "internal_error_code": "DB001",
        "original_error": "Connection timeout",
        "traceback": ["...", "..."]
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "trace_id": "trace-abc123"
}
```

## 最佳实践

### 1. 异常选择原则
- 优先使用具体的异常类型而不是通用的BusinessError
- 异常消息要对用户友好，避免暴露技术细节
- 在service层抛出异常，在controller层处理响应

### 2. 错误消息规范
```python
# 好的错误消息
raise ResourceNotFoundError("用户", user_id)
raise BusinessError("库存不足，无法完成订单")

# 避免的错误消息
raise SystemError("NullPointerException in UserService.java:123")
raise BusinessError("Error code: 500")
```

### 3. 异常数据使用
```python
# 提供有用的上下文信息
raise ValidationError(
    "密码强度不足",
    field="password",
    value="***"  # 不要暴露实际密码
)

# 提供解决建议
raise InsufficientResourceError(
    "积分",
    available=current_points,
    required=required_points
)
```

### 4. 服务层异常处理
```python
class UserService:
    async def create_user(self, user_data: UserCreate):
        # 业务规则验证
        if await self.email_exists(user_data.email):
            raise ResourceConflictError("邮箱已被注册")
        
        try:
            # 数据库操作
            user = await self.db.create(user_data)
            return user
        except SQLAlchemyError as e:
            # 转换为业务异常
            raise DatabaseError("用户创建失败", original_exception=e)
```

## 迁移检查清单

- [ ] 替换所有`APIResponse.success()`调用
- [ ] 替换所有`APIResponse.error()`调用
- [ ] 替换所有`APIResponse.pagination()`调用
- [ ] 移除不必要的try-catch块
- [ ] 使用合适的异常类型
- [ ] 更新路由函数的返回类型注解
- [ ] 测试异常情况的响应格式
- [ ] 验证日志记录是否正常
- [ ] 检查前端是否需要适配新的响应格式

## 常见问题

### Q: 旧的APIResponse方法还能使用吗？
A: 可以，但会显示废弃警告。建议尽快迁移到新系统。

### Q: 如何处理复杂的错误场景？
A: 创建自定义异常类继承BaseAPIException，或使用现有异常类的data参数传递额外信息。

### Q: 异常会影响性能吗？
A: 异常只在错误情况下抛出，对正常流程性能影响很小。新系统实际上减少了不必要的条件判断。

### Q: 如何在中间件中处理异常？
A: 全局异常处理器会自动处理所有异常，中间件无需特殊处理。

### Q: 前端需要修改吗？
A: 响应格式保持不变，前端无需修改。但可以利用新的错误代码进行更精确的错误处理。

## 支持和反馈

如果在迁移过程中遇到问题，请：
1. 查看现有的迁移示例
2. 运行单元测试验证功能
3. 查看日志中的异常信息
4. 联系开发团队获取支持