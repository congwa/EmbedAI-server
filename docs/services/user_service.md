# UserService 用户服务类

## 概述

`UserService` 是用户管理的核心业务服务类，提供用户的创建、查询、更新、删除等完整的CRUD操作，以及用户认证、权限管理等功能。

## 类定义

```python
from app.services.user import UserService
```

**文件路径**: `app/services/user.py`

## 类初始化

### 构造函数

```python
def __init__(self, db: AsyncSession)
```

**参数**:
- `db` (AsyncSession): 异步数据库会话对象

**示例**:
```python
from app.models.database import AsyncSessionLocal
from app.services.user import UserService

async with AsyncSessionLocal() as db:
    user_service = UserService(db)
```

## 核心方法

### 1. 创建用户

```python
async def create_user(self, user_data: UserCreate) -> User
```

**功能**: 创建新的用户账户，自动生成SDK密钥和密钥

**参数**:
- `user_data` (UserCreate): 用户创建数据模型
  - `email` (str): 用户邮箱地址，必须唯一
  - `password` (str): 用户密码，将被自动哈希
  - `is_admin` (bool, 可选): 是否为管理员，默认False

**返回值**:
- `User`: 创建成功的用户对象

**异常**:
- `ValueError`: 邮箱已存在时抛出
- `ValidationError`: 数据验证失败时抛出

**使用示例**:
```python
from app.schemas.user import UserCreate

# 创建普通用户
user_data = UserCreate(
    email="newuser@example.com",
    password="SecurePassword123!",
    is_admin=False
)

try:
    new_user = await user_service.create_user(user_data)
    print(f"用户创建成功，ID: {new_user.id}")
    print(f"SDK密钥: {new_user.sdk_key}")
except ValueError as e:
    print(f"创建失败: {e}")
```

### 2. 根据ID获取用户

```python
async def get_user_by_id(self, user_id: int) -> Optional[User]
```

**功能**: 根据用户ID获取用户详细信息

**参数**:
- `user_id` (int): 用户ID

**返回值**:
- `Optional[User]`: 用户对象，如果不存在则返回None

**使用示例**:
```python
user = await user_service.get_user_by_id(1)
if user:
    print(f"用户邮箱: {user.email}")
    print(f"是否管理员: {user.is_admin}")
else:
    print("用户不存在")
```

### 3. 根据邮箱获取用户

```python
async def get_user_by_email(self, email: str) -> Optional[User]
```

**功能**: 根据邮箱地址获取用户信息

**参数**:
- `email` (str): 用户邮箱地址

**返回值**:
- `Optional[User]`: 用户对象，如果不存在则返回None

**使用示例**:
```python
user = await user_service.get_user_by_email("admin@example.com")
if user:
    print(f"用户ID: {user.id}")
    print(f"创建时间: {user.created_at}")
```

### 4. 获取用户列表

```python
async def get_users(
    self, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None
) -> Tuple[List[User], int]
```

**功能**: 获取用户列表，支持分页、搜索和过滤

**参数**:
- `skip` (int, 可选): 跳过的记录数，默认0
- `limit` (int, 可选): 返回的最大记录数，默认100
- `search` (str, 可选): 搜索关键词，在邮箱中搜索
- `is_active` (bool, 可选): 过滤活跃状态
- `is_admin` (bool, 可选): 过滤管理员状态

**返回值**:
- `Tuple[List[User], int]`: 用户列表和总数的元组

**使用示例**:
```python
# 获取前20个活跃用户
users, total = await user_service.get_users(
    skip=0, 
    limit=20, 
    is_active=True
)

print(f"找到 {total} 个用户，返回前 {len(users)} 个")
for user in users:
    print(f"- {user.email} (ID: {user.id})")

# 搜索包含"admin"的用户
admin_users, count = await user_service.get_users(search="admin")
print(f"找到 {count} 个包含'admin'的用户")
```

### 5. 更新用户信息

```python
async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]
```

**功能**: 更新用户的基本信息

**参数**:
- `user_id` (int): 用户ID
- `user_data` (UserUpdate): 用户更新数据模型
  - `email` (str, 可选): 新的邮箱地址
  - `password` (str, 可选): 新的密码

**返回值**:
- `Optional[User]`: 更新后的用户对象，如果用户不存在则返回None

**异常**:
- `ValueError`: 邮箱已被其他用户使用时抛出

**使用示例**:
```python
from app.schemas.user import UserUpdate

# 更新用户邮箱
update_data = UserUpdate(email="newemail@example.com")
updated_user = await user_service.update_user(1, update_data)

if updated_user:
    print(f"用户邮箱已更新为: {updated_user.email}")
else:
    print("用户不存在")

# 更新密码
password_update = UserUpdate(password="NewPassword456!")
await user_service.update_user(1, password_update)
print("密码已更新")
```

### 6. 更新用户状态

```python
async def update_user_status(self, user_id: int, is_active: bool) -> Optional[User]
```

**功能**: 启用或禁用用户账户

**参数**:
- `user_id` (int): 用户ID
- `is_active` (bool): 新的活跃状态

**返回值**:
- `Optional[User]`: 更新后的用户对象

**使用示例**:
```python
# 禁用用户
disabled_user = await user_service.update_user_status(1, False)
if disabled_user:
    print(f"用户 {disabled_user.email} 已被禁用")

# 启用用户
enabled_user = await user_service.update_user_status(1, True)
if enabled_user:
    print(f"用户 {enabled_user.email} 已被启用")
```

### 7. 删除用户

```python
async def delete_user(self, user_id: int) -> bool
```

**功能**: 删除用户账户（软删除）

**参数**:
- `user_id` (int): 用户ID

**返回值**:
- `bool`: 删除是否成功

**使用示例**:
```python
success = await user_service.delete_user(1)
if success:
    print("用户删除成功")
else:
    print("用户删除失败或用户不存在")
```

### 8. 验证用户密码

```python
async def verify_password(self, user_id: int, password: str) -> bool
```

**功能**: 验证用户密码是否正确

**参数**:
- `user_id` (int): 用户ID
- `password` (str): 待验证的密码

**返回值**:
- `bool`: 密码是否正确

**使用示例**:
```python
is_valid = await user_service.verify_password(1, "UserPassword123!")
if is_valid:
    print("密码正确")
else:
    print("密码错误")
```

### 9. 批量操作

```python
async def batch_update_status(self, user_ids: List[int], is_active: bool) -> Dict[str, Any]
```

**功能**: 批量更新多个用户的状态

**参数**:
- `user_ids` (List[int]): 用户ID列表
- `is_active` (bool): 新的活跃状态

**返回值**:
- `Dict[str, Any]`: 操作结果统计
  - `processed` (int): 处理的用户数
  - `failed` (int): 失败的用户数
  - `results` (List[Dict]): 详细结果列表

**使用示例**:
```python
# 批量禁用用户
user_ids = [1, 2, 3, 4, 5]
result = await user_service.batch_update_status(user_ids, False)

print(f"处理了 {result['processed']} 个用户")
print(f"失败了 {result['failed']} 个用户")

for item in result['results']:
    print(f"用户 {item['user_id']}: {item['status']}")
```

### 10. 获取用户统计信息

```python
async def get_user_stats(self) -> Dict[str, Any]
```

**功能**: 获取用户相关的统计信息

**返回值**:
- `Dict[str, Any]`: 统计信息字典
  - `total_users` (int): 总用户数
  - `active_users` (int): 活跃用户数
  - `admin_users` (int): 管理员用户数
  - `new_users_today` (int): 今日新增用户数

**使用示例**:
```python
stats = await user_service.get_user_stats()
print(f"总用户数: {stats['total_users']}")
print(f"活跃用户数: {stats['active_users']}")
print(f"管理员数: {stats['admin_users']}")
print(f"今日新增: {stats['new_users_today']}")
```

## 异常处理

### 常见异常类型

1. **ValueError**: 业务逻辑错误
   - 邮箱已存在
   - 用户不存在
   - 无效的参数值

2. **ValidationError**: 数据验证错误
   - 邮箱格式不正确
   - 密码强度不够
   - 必填字段缺失

3. **DatabaseError**: 数据库操作错误
   - 连接失败
   - 约束违反
   - 事务回滚

### 异常处理示例

```python
from app.core.exceptions import ValidationError, DatabaseError

try:
    user_data = UserCreate(
        email="invalid-email",  # 无效邮箱格式
        password="123"  # 密码太短
    )
    new_user = await user_service.create_user(user_data)
except ValidationError as e:
    print(f"数据验证失败: {e}")
except ValueError as e:
    print(f"业务逻辑错误: {e}")
except DatabaseError as e:
    print(f"数据库错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

### 1. 事务管理

```python
from app.models.database import AsyncSessionLocal

async def create_user_with_profile():
    async with AsyncSessionLocal() as db:
        try:
            user_service = UserService(db)
            
            # 在事务中创建用户
            user_data = UserCreate(
                email="user@example.com",
                password="SecurePassword123!"
            )
            user = await user_service.create_user(user_data)
            
            # 提交事务
            await db.commit()
            return user
            
        except Exception as e:
            # 回滚事务
            await db.rollback()
            raise e
```

### 2. 密码安全

```python
# 使用强密码策略
def validate_password(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True

# 创建用户前验证密码
if validate_password(password):
    user_data = UserCreate(email=email, password=password)
    user = await user_service.create_user(user_data)
```

### 3. 分页查询优化

```python
# 高效的分页查询
async def get_users_paginated(page: int, size: int):
    skip = (page - 1) * size
    users, total = await user_service.get_users(skip=skip, limit=size)
    
    return {
        "items": users,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size
        }
    }
```

## 性能考虑

1. **数据库索引**: 确保邮箱字段有唯一索引
2. **查询优化**: 使用适当的查询条件和限制
3. **缓存策略**: 对频繁查询的用户信息进行缓存
4. **批量操作**: 使用批量操作提高性能

## 安全注意事项

1. **密码处理**: 密码始终经过哈希处理，不存储明文
2. **输入验证**: 所有输入都经过严格验证
3. **权限检查**: 确保只有授权用户可以执行操作
4. **日志记录**: 记录所有重要的用户操作
