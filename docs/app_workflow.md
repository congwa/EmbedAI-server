# EmbedAI-server项目用户权限管理完整流程

## 一、用户管理流程

### 1. 管理员注册

系统初始化时，首先需要创建管理员账户：

```python
# 通过特殊注册码创建管理员账户
response = client.post(
    "/api/v1/admin/register",
    json={
        "email": "admin@example.com",
        "password": "admin123",
        "register_code": "123456"  # 系统配置的管理员注册码
    }
)
```

### 2. 管理员登录

管理员通过邮箱和密码登录系统：

```python
response = client.post(
    "/api/v1/admin/login",
    json={
        "email": "admin@example.com",
        "password": "admin123"
    }
)
# 获取访问令牌
admin_token = response.json()["data"]["access_token"]
```

### 3. 创建普通用户

管理员可以创建普通用户，系统会自动为普通用户生成SDK密钥和密钥对：

```python
response = client.post(
    "/api/v1/admin/users",
    json={
        "email": "user@example.com",
        "password": "user123",
        "is_admin": False
    },
    headers={"Authorization": f"Bearer {admin_token}"}
)
# 用户创建成功后会返回包含SDK密钥和密钥对的信息
user_id = response.json()["data"]["id"]
sdk_key = response.json()["data"]["sdk_key"]
secret_key = response.json()["data"]["secret_key"]
```

## 二、知识库权限管理

### 1. 创建知识库

用户登录后可以创建知识库，创建者自动成为知识库所有者（OWNER权限）：

```python
response = client.post(
    "/api/v1/admin/knowledge-bases",
    json={
        "name": "测试知识库",
        "domain": "测试领域",
        "example_queries": ["问题1", "问题2"],
        "entity_types": ["实体1", "实体2"],
        "llm_config": {
            # LLM配置信息
        }
    },
    headers={"Authorization": f"Bearer {user_token}"}
)
kb_id = response.json()["data"]["id"]
```

### 2. 查看知识库成员

知识库创建后，初始只有创建者一个成员，权限为OWNER：

```python
response = client.get(
    f"/api/v1/admin/knowledge-bases/{kb_id}/members",
    headers={"Authorization": f"Bearer {user_token}"}
)
members = response.json()["data"]["members"]
# 验证初始只有创建者一个成员
assert len(members) == 1
assert members[0]["is_owner"] == True
assert members[0]["permission"] == "owner"
```

### 3. 添加知识库成员

知识库所有者或管理员可以添加其他用户为知识库成员，并分配权限：

```python
response = client.post(
    f"/api/v1/admin/knowledge-bases/{kb_id}/members",
    json={
        "user_id": another_user_id,
        "permission": "editor"  # 可选：viewer, editor, admin, owner
    },
    headers={"Authorization": f"Bearer {user_token}"}
)
```

系统支持的权限级别（从低到高）：
- **VIEWER**：只读权限，可以查看和搜索
- **EDITOR**：编辑权限，可以添加和修改文档
- **ADMIN**：管理权限，可以管理成员和设置
- **OWNER**：所有者权限，完全控制权限

### 4. 更新成员权限

知识库所有者或管理员可以更新成员的权限级别：

```python
response = client.put(
    f"/api/v1/admin/knowledge-bases/{kb_id}/members/{another_user_id}",
    json={
        "permission": "admin"
    },
    headers={"Authorization": f"Bearer {user_token}"}
)
```

权限更新遵循以下规则：
- 不能修改所有者的权限
- 不能将用户权限设置为高于自己的级别
- 不能修改权限级别高于或等于自己的用户

### 5. 移除知识库成员

知识库所有者或管理员可以移除知识库成员：

```python
response = client.delete(
    f"/api/v1/admin/knowledge-bases/{kb_id}/members/{another_user_id}",
    headers={"Authorization": f"Bearer {user_token}"}
)
```

移除成员遵循以下规则：
- 不能移除知识库所有者
- 不能移除权限级别高于或等于自己的用户

## 三、权限检查机制

系统在各操作中进行权限检查，确保用户只能执行其权限范围内的操作：

```python
async def check_permission(
    self,
    kb_id: int,
    user_id: int,
    required_permission: PermissionType
) -> bool:
    """检查用户对知识库的权限"""
    kb = (await self.db.execute(
        select(KnowledgeBase).filter(KnowledgeBase.id == kb_id)
    )).scalar_one_or_none()
    
    if not kb:
        return False
        
    return await kb.check_permission(self.db, user_id, required_permission)
```

权限检查逻辑包括：
1. 系统管理员拥有所有权限
2. 根据权限等级进行检查，确保用户拥有所需的最低权限级别

## 四、文档管理与权限

知识库成员可以根据其权限级别管理文档：

```python
# 创建文档（需要EDITOR或以上权限）
response = client.post(
    f"/api/v1/admin/knowledge-bases/{kb_id}/documents",
    json={
        "title": "测试文档",
        "content": "文档内容...",
        "doc_type": "text"
    },
    headers={"Authorization": f"Bearer {user_token}"}
)
```

## 五、完整流程示例

测试用例展示了完整的用户权限管理流程：

1. 创建管理员账户
2. 管理员登录
3. 管理员创建普通用户
4. 普通用户登录
5. 普通用户创建知识库（成为所有者）
6. 添加其他用户为知识库成员
7. 更新成员权限
8. 测试成员访问权限
9. 移除成员
10. 文档管理操作

通过这一完整流程，系统实现了从用户创建到权限分配的全面管理，确保知识库资源的安全访问和有效协作。
        