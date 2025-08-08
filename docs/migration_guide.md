# API响应系统迁移指南

本指南将帮助你从旧的APIResponse机制迁移到新的优雅响应系统。

## 🎯 迁移目标

- **简化代码**：移除繁琐的try-catch包装和手动异常处理
- **统一异常**：使用全局异常处理器和自定义异常类
- **类型安全**：充分利用FastAPI的response_model和类型提示
- **向后兼容**：确保迁移过程中系统稳定运行

## 📋 迁移前准备

### 1. 运行迁移分析工具

```bash
python -m app.utils.migration_tools
```

这将生成一个详细的迁移报告，帮助你了解需要迁移的代码。

### 2. 启用废弃警告

在开发环境中启用废弃警告，以便及时发现需要迁移的代码：

```python
import warnings
warnings.filterwarnings("default", category=DeprecationWarning)
```

## 🔄 迁移步骤

### 步骤1：替换成功响应

**旧代码：**
```python
@router.get("/config")
async def get_config():
    try:
        config = await get_config_data()
        return APIResponse.success(data=config, message="获取配置成功")
    except Exception as e:
        Logger.error(f"获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")
```

**新代码：**
```python
@router.get("/config", response_model=ResponseModel[ConfigSchema])
async def get_config():
    config = await get_config_data()
    return ResponseModel.create_success(
        data=config,
        message="获取配置成功"
    )
```

### 步骤2：替换错误处理

**旧代码：**
```python
try:
    user = await get_user(user_id)
    if not user:
        return APIResponse.error("用户不存在", code=404)
    return APIResponse.success(data=user)
except Exception as e:
    return APIResponse.error("服务器错误", code=500)
```

**新代码：**
```python
user = await get_user(user_id)
if not user:
    raise ResourceNotFoundException("用户", user_id)

return ResponseModel.create_success(data=user)
```

### 步骤3：替换分页响应

**旧代码：**
```python
items, total = await get_items_paginated(page, page_size)
return APIResponse.pagination(
    items=items,
    total=total,
    page=page,
    page_size=page_size
)
```

**新代码：**
```python
items, total = await get_items_paginated(page, page_size)
return ResponseModel.create_pagination(
    items=items,
    total=total,
    page=page,
    page_size=page_size
)
```

### 步骤4：移除装饰器

**旧代码：**
```python
@response_wrapper()
async def my_endpoint():
    return some_data
```

**新代码：**
```python
async def my_endpoint():
    return ResponseModel.create_success(data=some_data)
```

### 步骤5：更新服务层

**旧代码：**
```python
class MyService:
    async def get_data(self):
        try:
            # 业务逻辑
            return data
        except Exception as e:
            Logger.error(f"操作失败: {str(e)}")
            raise HTTPException(status_code=500, detail="操作失败")
```

**新代码：**
```python
from app.services.base import BaseService

class MyService(BaseService):
    async def get_data(self):
        # 业务逻辑
        # 如果出错，直接抛出自定义异常
        if error_condition:
            raise BusinessException("业务规则验证失败")
        
        return data
```

## 🛠️ 新的异常处理机制

### 使用自定义异常类

```python
from app.core.exceptions import (
    APIException,
    BusinessException,
    ResourceNotFoundException,
    PermissionDeniedException,
    ValidationException,
    SystemException,
    ConfigurationException
)

# 业务逻辑异常
raise BusinessException("用户名已存在")

# 资源未找到
raise ResourceNotFoundException("用户", user_id)

# 权限不足
raise PermissionDeniedException("需要管理员权限", "admin")

# 数据验证失败
raise ValidationException("邮箱格式不正确", field="email", value=email)

# 系统错误
raise SystemException("数据库连接失败", "DB_CONNECTION_ERROR")

# 配置错误
raise ConfigurationException("配置项不存在", "database.host")
```

### 服务层最佳实践

```python
from app.services.base import BaseService

class UserService(BaseService):
    async def create_user(self, user_data: UserCreate) -> User:
        # 使用基类的验证方法
        self.validate_business_rule(
            not await self.user_exists(user_data.email),
            "用户邮箱已存在"
        )
        
        # 使用安全执行方法
        user = await self.safe_execute(
            lambda: self.db.create_user(user_data),
            "创建用户失败",
            "USER_CREATE_ERROR"
        )
        
        # 记录操作日志
        self.log_operation("create_user", details={"email": user_data.email})
        
        return user
```

## 📊 迁移验证

### 1. 运行测试

确保所有测试通过：
```bash
pytest tests/
```

### 2. 检查API文档

访问 `/docs` 确保API文档正确生成。

### 3. 验证响应格式

确保响应格式与之前完全一致：

```json
{
    "success": true,
    "code": 200,
    "message": "操作成功",
    "data": {...}
}
```

### 4. 性能测试

新的响应机制应该有更好的性能表现。

## 🚨 常见问题

### Q: 迁移后响应格式发生变化怎么办？

A: 新的ResponseModel.create_success()方法会生成与旧格式完全一致的响应。如果发现格式不一致，请检查：
- 是否正确使用了create_success()方法
- response_model是否正确设置
- 数据序列化是否正确

### Q: 异常处理变得复杂了怎么办？

A: 新的异常处理机制实际上更简单：
- 不需要手动try-catch
- 直接抛出自定义异常
- 全局异常处理器自动处理转换

### Q: 如何处理复杂的错误场景？

A: 使用自定义异常类的data参数传递额外信息：

```python
raise ValidationException(
    "数据验证失败",
    data={
        "errors": [
            {"field": "email", "message": "邮箱格式不正确"},
            {"field": "password", "message": "密码长度不足"}
        ]
    }
)
```

### Q: 旧代码可以继续使用吗？

A: 可以，但会收到废弃警告。建议尽快迁移：
- APIResponse类仍然可用，但已标记为废弃
- response_wrapper装饰器仍然可用，但已标记为废弃
- 新旧机制可以在同一个项目中并存

## 📈 迁移收益

迁移完成后，你将获得：

1. **更简洁的代码**：减少50%以上的样板代码
2. **更好的类型安全**：充分利用FastAPI的类型系统
3. **统一的异常处理**：不再需要手动处理异常
4. **更好的性能**：减少不必要的数据转换
5. **更好的可维护性**：代码结构更清晰

## 🎉 迁移完成检查清单

- [ ] 所有APIResponse.success()调用已替换
- [ ] 所有APIResponse.error()调用已替换  
- [ ] 所有APIResponse.pagination()调用已替换
- [ ] 所有@response_wrapper装饰器已移除
- [ ] 手动try-catch异常处理已简化
- [ ] 使用新的异常类替代HTTPException
- [ ] 服务层继承BaseService基类
- [ ] API文档生成正常
- [ ] 所有测试通过
- [ ] 响应格式保持一致
- [ ] 性能测试通过

恭喜！你已经成功迁移到新的优雅API响应系统！🎊