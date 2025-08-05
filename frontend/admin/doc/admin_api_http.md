# 用户端 API 文档

本文档详细描述了面向第三方用户的客户端接口。

**接口前缀**: `/api/v1`

---

## 1. 知识库 (`/client/knowledge-base`)

### 1.1 查询知识库

- **方法**: `POST`
- **路径**: `/client/knowledge-base/{kb_id}/query`
- **描述**: 第三方用户在指定的知识库中进行查询。
- **路径参数**:
  - `kb_id` (int, required): 知识库ID。
- **查询参数**:
  - `client_id` (str, required): 用于标识调用方客户端的唯一ID。
  - `third_party_user_id` (int, required): 第三方系统中的用户唯一ID。
- **请求体**: `application/json` (`QueryRequest` schema)
  ```json
  {
    "query": "你们的退货政策是什么？",
    "top_k": 5
  }
  ```
- **响应**: 成功时返回包含查询结果和相关文档元数据的对象。

---

## 2. 聊天 (`/chat/client`)

### 2.1 创建聊天会话

- **方法**: `POST`
- **路径**: `/chat/client/create`
- **描述**: 为第三方用户创建一个新的聊天会话。
- **请求体**: `application/json` (`ChatRequest` schema)
  ```json
  {
    "third_party_user_id": 12345,
    "kb_id": 1,
    "title": "关于订单 #54321 的咨询"
  }
  ```
- **响应**: 成功时返回新创建的聊天会话信息，包含 `chat_id`。

### 2.2 获取聊天列表

- **方法**: `GET`
- **路径**: `/chat/client/list`
- **描述**: 获取指定第三方用户的聊天会话列表。
- **查询参数**:
  - `third_party_user_id` (int, required): 第三方用户ID。
  - `skip` (int, optional, default: 0): 分页起始位置。
  - `limit` (int, optional, default: 20): 每页数量。

### 2.3 获取聊天详情

- **方法**: `GET`
- **路径**: `/chat/client/{chat_id}`
- **描述**: 获取指定聊天会话的详细信息和消息历史。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **查询参数**:
  - `third_party_user_id` (int, required): 第三方用户ID，用于验证所有权。

### 2.4 获取聊天消息列表

- **方法**: `GET`
- **路径**: `/chat/client/{chat_id}/messages`
- **描述**: 获取指定聊天会话的消息列表。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **查询参数**:
  - `third_party_user_id` (int, required): 第三方用户ID，用于验证所有权。
  - `skip` (int, optional, default: 0): 分页起始位置。
  - `limit` (int, optional, default: 50): 每页数量。

### 2.5 删除聊天会话

- **方法**: `DELETE`
- **路径**: `/chat/client/{chat_id}`
- **描述**: 删除指定的聊天会话。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **查询参数**:
  - `third_party_user_id` (int, required): 第三方用户ID，用于验证所有权。

---

## 3. 用户端 WebSocket (`/ws/chat`)

### 3.1 实时聊天

请看 [./admin_api_documentation.md](./admin_api_documentation.md)


