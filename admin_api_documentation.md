# 管理端 API 文档

本文档详细描述了项目的管理端接口。

**接口前缀**: `/api/v1/admin`

---

## 1. 认证 (`/auth`)

### 1.1 管理员登录

- **方法**: `POST`
- **路径**: `/auth/login`
- **描述**: 验证管理员的邮箱和密码，成功后返回访问令牌。
- **请求体**: `application/json`
  ```json
  {
    "email": "admin@example.com",
    "password": "admin_password"
  }
  ```
- **响应**: 成功时返回包含 `access_token` 和 `user` 信息的对象。

---

## 2. 用户管理 (`/users`)

### 2.1 注册管理员

- **方法**: `POST`
- **路径**: `/register`
- **描述**: 使用特殊的注册码创建新的管理员账户。
- **请求体**: `application/json`
  ```json
  {
    "email": "new_admin@example.com",
    "password": "secure_password",
    "register_code": "your_secret_register_code"
  }
  ```

### 2.2 创建普通用户

- **方法**: `POST`
- **路径**: `/users`
- **描述**: 管理员创建新的普通用户。
- **请求体**: `application/json`
  ```json
  {
    "email": "user@example.com",
    "password": "user_password"
  }
  ```

### 2.3 获取用户列表

- **方法**: `GET`
- **路径**: `/users`
- **描述**: 获取普通用户列表，支持分页。
- **查询参数**:
  - `page` (int, optional, default: 1): 页码。
  - `page_size` (int, optional, default: 10): 每页数量。

### 2.4 修改用户密码

- **方法**: `PUT`
- **路径**: `/users/{user_id}/password`
- **描述**: 管理员修改指定普通用户的密码。
- **路径参数**:
  - `user_id` (int, required): 用户ID。
- **请求体**: `application/json`
  ```json
  {
    "new_password": "new_secure_password"
  }
  ```

### 2.5 更新用户状态

- **方法**: `PUT`
- **路径**: `/users/{user_id}/status`
- **描述**: 管理员启用或禁用指定用户。
- **路径参数**:
  - `user_id` (int, required): 用户ID。
- **请求体**: `application/json`
  ```json
  {
    "is_active": true
  }
  ```

### 2.6 重置用户密钥

- **方法**: `POST`
- **路径**: `/users/{user_id}/reset-keys`
- **描述**: 重置用户的SDK密钥和密钥对。
- **路径参数**:
  - `user_id` (int, required): 用户ID。

---

## 3. 知识库管理 (`/knowledge-bases`)

### 3.1 创建知识库

- **方法**: `POST`
- **路径**: `/knowledge-bases`
- **描述**: 创建一个新的知识库。
- **请求体**: `application/json` (`KnowledgeBaseCreate` schema)
  ```json
  {
    "name": "产品知识库",
    "domain": "电子商务",
    "example_queries": ["如何退货?", "运费是多少?"],
    "entity_types": ["订单", "商品"],
    "llm_config": { ... }
  }
  ```

### 3.2 获取我的知识库列表

- **方法**: `GET`
- **路径**: `/knowledge-bases/my`
- **描述**: 获取当前管理员可访问的所有知识库列表。

### 3.3 获取知识库详情

- **方法**: `GET`
- **路径**: `/knowledge-bases/{kb_id}`
- **描述**: 获取指定知识库的详细信息。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。

### 3.4 更新知识库

- **方法**: `PUT`
- **路径**: `/knowledge-bases/{kb_id}`
- **描述**: 更新指定知识库的信息。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。
- **请求体**: `application/json` (`KnowledgeBaseUpdate` schema, 所有字段可选)
  ```json
  {
    "name": "更新后的产品知识库",
    "domain": "客户服务"
  }
  ```

### 3.5 删除知识库

- **方法**: `DELETE`
- **路径**: `/knowledge-bases/{kb_id}`
- **描述**: 软删除指定的知识库。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。

### 3.6 训练知识库

- **方法**: `POST`
- **路径**: `/knowledge-bases/{kb_id}/train`
- **描述**: 触发对知识库的训练流程。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。

### 3.7 查询知识库

- **方法**: `POST`
- **路径**: `/knowledge-bases/{kb_id}/query`
- **描述**: 在指定知识库内进行查询。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。
- **请求体**: `application/json`
  ```json
  {
      "query": "你们的退货政策是什么？",
      "method": "hybrid_search",
      "top_k": 5,
      "use_rerank": true
  }
  ```

### 3.8 知识库成员管理

- **获取成员列表**: `GET /knowledge-bases/{kb_id}/members`
- **添加成员**: `POST /knowledge-bases/{kb_id}/members`
  - **请求体**: `{"user_id": 123, "permission": "viewer"}`
- **更新成员权限**: `PUT /knowledge-bases/{kb_id}/members/{user_id}`
  - **请求体**: `{"permission": "editor"}`
- **移除成员**: `DELETE /knowledge-bases/{kb_id}/members/{user_id}`

---

## 4. 文档管理 (`/documents`)

### 4.1 创建文本类型文档

- **方法**: `POST`
- **路径**: `/documents/knowledge-bases/{kb_id}/documents/text`
- **描述**: 在指定知识库中创建一个基于文本的文档。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。
- **请求体**: `application/json` (`DocumentCreate` schema)
  ```json
  {
    "title": "关于退货政策",
    "content": "我们的退货政策是...",
    "doc_type": "text"
  }
  ```

### 4.2 上传文件创建文档

- **方法**: `POST`
- **路径**: `/documents/knowledge-bases/{kb_id}/documents/upload`
- **描述**: 上传文件（如PDF, DOCX等）来创建文档。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。
- **请求体**: `multipart/form-data`
  - `file`: 上传的文件。

### 4.3 获取文档列表

- **方法**: `GET`
- **路径**: `/documents/knowledge-bases/{kb_id}/documents`
- **描述**: 获取指定知识库的文档列表，支持过滤和分页。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。
- **查询参数**:
  - `skip` (int, optional, default: 0): 分页偏移量。
  - `limit` (int, optional, default: 10): 每页数量。
  - `title` (str, optional): 按标题模糊搜索。
  - `doc_type` (str, optional): 按文档类型过滤。
  - `start_time` (datetime, optional): 创建时间范围开始。
  - `end_time` (datetime, optional): 创建时间范围结束。

### 4.4 获取/更新/删除/重新处理 文档

- **获取详情**: `GET /documents/{doc_id}`
- **更新文档**: `PUT /documents/{doc_id}`
  - **请求体**: `DocumentUpdate` schema (所有字段可选)
- **删除文档**: `DELETE /documents/{doc_id}`
- **重新处理**: `POST /documents/{doc_id}/reprocess`

---

## 5. 聊天管理 (`/api/v1/chat/admin`)

### 5.1 获取聊天列表

- **方法**: `GET`
- **路径**: `/`
- **描述**: 管理员获取聊天会话列表。
- **查询参数**:
  - `skip` (int, optional, default: 0)
  - `limit` (int, optional, default: 20)
  - `include_inactive` (bool, optional, default: false)
  - `all_chats` (bool, optional, default: false)

### 5.2 获取/发送 聊天消息

- **获取详情**: `GET /{chat_id}`
- **获取消息列表**: `GET /{chat_id}/messages`
- **发送消息**: `POST /{chat_id}/messages`
  - **请求体**: `ChatMessageCreate` schema

### 5.3 聊天操作

- **切换模式**: `POST /{chat_id}/switch-mode` (Query param: `mode`)
- **加入聊天**: `POST /{chat_id}/join`
- **离开聊天**: `POST /{chat_id}/leave`
- **恢复聊天**: `POST /{chat_id}/restore`

### 5.4 统计与查询

- **获取已删除列表**: `GET /deleted`
- **获取用户聊天统计**: `GET /users/{third_party_user_id}/stats`
- **获取知识库聊天统计**: `GET /knowledge-bases/{kb_id}/stats` (未实现)

---

## 6. 管理端 WebSocket (`/api/v1/ws/chat/admin`)

### 6.1 管理员实时聊天

- **方法**: `WEBSOCKET`
- **路径**: `/{chat_id}`
- **描述**: 管理员通过WebSocket连接进行实时聊天。
- **查询参数**:
  - `client_id` (str, required)
  - `admin_id` (int, required)