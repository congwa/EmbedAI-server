# 客户端 WebSocket API (协议 V2) - 详细版

本文档详细概述了用于客户端和服务器之间实时聊天通信的 WebSocket 协议 V2。

## 1. 连接

- **端点**: `ws://<server_address>/api/v1/ws/client/{chat_id}`
- **路径参数**:
  - `chat_id` (整数): **必须**。指定要加入的聊天会话ID。
- **查询参数**:
  - `client_id` (字符串): **必须**。客户端实例的唯一标识符。
  - `third_party_user_id` (整数): **必须**。第三方系统的用户ID。
- **请求头**:
  - `X-Trace-ID` (字符串, 可选): 用于端到端请求追踪的ID。

## 2. 通用消息格式

所有客户端与服务器之间的消息都遵循此JSON结构。

```json
{
  "type": "domain.action",
  "payload": { ... },
  "request_id": "unique_string_for_request"
}
```

- `type` (字符串): **必须**。消息的类型，格式为 `domain.action`。
- `payload` (对象): **必须**。与消息类型相关的具体数据。
- `request_id` (字符串, 可选): 唯一的请求标识符。对于需要响应的请求，响应消息将包含相同的 `request_id`。

---

## 3. 客户端到服务器事件 (C2S)

客户端可以向服务器发送以下事件。

### 3.1 `message.create`

发送一条聊天消息。

- **Payload**:
  - `content` (字符串): **必须**。消息的文本内容。
  - `message_type` (字符串, 可选): 消息类型，默认为 `TEXT`。
  - `metadata` (对象, 可选): 附加的元数据。
- **示例**:
  ```json
  {
    "type": "message.create",
    "payload": {
      "content": "你好，我的订单需要帮助。"
    },
    "request_id": "req-msg-123"
  }
  ```

### 3.2 `history.request`

请求聊天历史消息。

- **Payload**:
  - `before_message_id` (整数, 可选): 如果提供，则返回此消息ID之前的消息。用于分页加载。
  - `limit` (整数, 可选, 默认值: 20): 要获取的消息数量。
- **示例**:
  ```json
  {
    "type": "history.request",
    "payload": {
      "limit": 50
    },
    "request_id": "req-hist-456"
  }
  ```

### 3.3 `typing.start` / `typing.stop`

通知服务器客户端正在输入或已停止输入。

- **Payload**:
  - `is_typing` (布尔值): **必须**。`true` 表示正在输入，`false` 表示停止输入。
- **示例 (`typing.start`)**:
  ```json
  {
    "type": "typing.start",
    "payload": {
      "is_typing": true
    }
  }
  ```

### 3.4 `message.read`

将一条或多条消息标记为已读。

- **Payload**:
  - `message_ids` (整数数组): **必须**。需要标记为已读的消息ID列表。
- **示例**:
  ```json
  {
    "type": "message.read",
    "payload": {
      "message_ids": [101, 102]
    }
  }
  ```

---

## 4. 服务器到客户端事件 (S2C)

服务器会向客户端推送以下事件。

### 4.1 `message.new`

当有新消息（来自用户、管理员或AI）时，服务器会广播此事件。

- **Payload**:
  - `message` (对象): **必须**。完整的消息对象。
    - `id` (整数): 消息的唯一ID。
    - `chat_id` (整数): 所属聊天ID。
    - `content` (字符串): 消息内容。
    - `message_type` (字符串): 消息类型 (例如 `USER`, `ASSISTANT`, `OFFICIAL`)。
    - `sender_id` (整数): 发送者ID。
    - `sender_type` (字符串): 发送者类型 (`third_party` 或 `official`)。
    - `created_at` (字符串): ISO 8601 格式的时间戳。
    - `metadata` (对象): 附加元数据。
    - `read_by` (用户身份对象数组): **新增**。已读此消息的用户身份列表。如果为空，表示无人已读。
      - `id` (整数): 用户身份的唯一ID。
      - `user_id` (整数): 关联的用户ID。
      - `user_type` (字符串): 用户类型 (`official` 或 `third_party`)。
- **示例**:
  ```json
  {
    "type": "message.new",
    "payload": {
      "message": {
        "id": 103,
        "chat_id": 1,
        "content": "你好，我的订单需要帮助。",
        "message_type": "USER",
        "sender_id": 5678,
        "sender_type": "third_party",
        "created_at": "2023-10-27T10:00:00Z",
        "metadata": {},
        "read_by": []
      }
    }
  }
  ```

### 4.2 `history.response`

响应 `history.request` 请求，返回历史消息列表。

- **request_id**: 与原始请求的 `request_id` 匹配。
- **Payload**:
  - `messages` (消息对象数组): **必须**。消息对象列表，结构与 `message.new` 中的 `message` 相同。
- **示例**:
  ```json
  {
    "type": "history.response",
    "payload": {
      "messages": [ ... ]
    },
    "request_id": "req-hist-456"
  }
  ```

### 4.3 `typing.update`

当聊天中有人（用户或管理员）正在输入或停止输入时广播。

- **Payload**:
  - `sender` (对象): **必须**。事件发送者的信息。
    - `user_id` (整数): 发送者用户ID。
    - `client_id` (字符串): 发送者客户端ID。
    - `user_type` (字符串): 发送者类型 (`official` 或 `third_party`)。
  - `is_typing` (布尔值): **必须**。`true` 表示正在输入。
- **示例**:
  ```json
  {
    "type": "typing.update",
    "payload": {
      "sender": {
        "user_id": 1234,
        "client_id": "admin-xyz-789",
        "user_type": "official"
      },
      "is_typing": true
    }
  }
  ```

### 4.4 `message.read.update`

当一条或多条消息被读取时广播。此事件通知所有客户端更新特定消息的已读状态。

- **Payload**:
  - `messages` (消息对象数组): **必须**。被更新的消息对象列表。每个对象的结构与 `message.new` 中的 `message` 相同，包含了最新的 `read_by` 列表。
- **示例**:
  ```json
  {
    "type": "message.read.update",
    "payload": {
      "messages": [
        {
          "id": 101,
          "chat_id": 1,
          "content": "你好，我的订单需要帮助。",
          "message_type": "USER",
          "sender_id": 5678,
          "sender_type": "third_party",
          "created_at": "2023-10-27T10:00:00Z",
          "metadata": {},
          "read_by": [
            {
              "id": 1,
              "user_id": 1234,
              "user_type": "official"
            }
          ]
        }
      ]
    }
  }
  ```

### 4.5 `notification.system`

发送系统级通知，例如用户加入/离开聊天。

- **Payload**:
  - `level` (字符串): **必须**。通知级别 (`info`, `warning`, `error`)。
  - `content` (字符串): **必须**。通知内容。
- **示例**:
  ```json
  {
    "type": "notification.system",
    "payload": {
      "level": "info",
      "content": "管理员已加入聊天"
    }
  }
  ```

### 4.6 `response.error`

当处理C2S请求发生错误时，服务器发送此响应。

- **request_id**: 与导致错误的原始请求的 `request_id` 匹配。
- **Payload**:
  - `code` (字符串): **必须**。标准化的错误码 (例如 `INVALID_PAYLOAD`, `UNKNOWN_TYPE`)。
  - `message` (字符串): **必须**。详细的错误信息。
- **示例**:
  ```json
  {
    "type": "response.error",
    "payload": {
      "code": "INVALID_FORMAT",
      "message": "消息缺少 'type' 字段。"
    },
    "request_id": "req-msg-bad-123"
  }
  ```