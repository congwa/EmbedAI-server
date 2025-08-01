# 管理员端 REST API 文档

本文档详细描述了面向管理员的 REST API 接口。

**接口前缀**: `/api/v1/chat/admin`

---

## 1. 聊天管理 (`/`)

### 1.1 获取聊天会话列表

- **方法**: `GET`
- **路径**: `/`
- **描述**: 获取管理员可见的聊天会话列表。管理员可以查看分配给自己的人工服务会话和所有AI模式的会话。
- **查询参数**:
  - `skip` (int, optional, default: 0): 分页起始位置。
  - `limit` (int, optional, default: 20): 每页数量。
  - `include_inactive` (bool, optional, default: False): 是否包含非活跃的会话。
  - `all_chats` (bool, optional, default: False): 是否获取所有聊天室列表，而不仅是分配给当前管理员的。
- **响应**: `200 OK`
  - **成功时返回** `ChatListResponse` 对象，包含会话列表和总数。

  **`ChatListResponse` 格式**:
  ```json
  {
    "total": 150, // 总会话数
    "items": [
      {
        "id": 101,
        "title": "关于订单 #54321 的咨询",
        "chat_mode": "HUMAN",
        "created_at": "2023-10-28T10:00:00Z",
        "updated_at": "2023-10-28T12:30:00Z",
        "is_active": true,
        "unread_count": 3, // 当前管理员的未读消息数
        "messages": null
      }
    ]
  }
  ```

### 1.2 获取聊天会话详情

- **方法**: `GET`
- **路径**: `/{chat_id}`
- **描述**: 获取指定聊天会话的详细信息。调用此接口会将该会话中所有未读消息标记为已读。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **响应**: `200 OK`
  - **成功时返回** `ChatResponse` 对象。

### 1.3 发送管理员消息

- **方法**: `POST`
- **路径**: `/{chat_id}/messages`
- **描述**: 在人工模式下，由当前服务的管理员发送消息。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **请求体**: `ChatMessageCreate` schema
  ```json
  {
    "content": "您好，请问有什么可以帮助您的？",
    "message_type": "TEXT"
  }
  ```
- **响应**: `200 OK`
  - **成功时返回** 新创建的 `ChatMessageResponse` 对象。

---

## 2. 会话操作

### 2.1 切换聊天模式

- **方法**: `POST`
- **路径**: `/{chat_id}/switch-mode`
- **描述**: 切换聊天模式。切换到人工模式时，会将当前管理员设为服务人员；切换到AI模式时，会清除服务人员。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **查询参数**:
  - `mode` (string, required): 目标模式，`AI` 或 `HUMAN`。
- **响应**: `200 OK`
  - **成功时返回** 更新后的 `ChatResponse` 对象。

### 2.2 管理员加入聊天

- **方法**: `POST`
- **路径**: `/{chat_id}/join`
- **描述**: 管理员手动加入一个聊天会话，成为该会话的服务人员。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **响应**: `200 OK`
  - **成功时返回** 更新后的 `ChatResponse` 对象。

### 2.3 管理员离开聊天

- **方法**: `POST`
- **路径**: `/{chat_id}/leave`
- **描述**: 管理员离开一个聊天会话，不再担任服务人员。
- **路径参数**:
  - `chat_id` (int, required): 聊天会话ID。
- **响应**: `200 OK`
  - **成功时返回** 更新后的 `ChatResponse` 对象。
