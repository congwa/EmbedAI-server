# 管理员 WebSocket API (协议 V2) - 详细版

本文档详细概述了用于管理员客户端和服务器之间实时聊天通信的 WebSocket 协议 V2。管理员协议是客户端协议的超集，拥有更多权限和功能。

## 1. 连接

- **端点**: `ws://<server_address>/api/v1/ws/admin/{chat_id}`
- **路径参数**:
  - `chat_id` (整数): **必须**。指定要加入的聊天会话ID。
- **查询参数**:
  - `client_id` (字符串): **必须**。客户端实例的唯一标识符。
  - `admin_id` (整数): **必须**。管理员用户的ID。
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

## 3. 管理员到服务器事件 (C2S)

管理员客户端可以向服务器发送以下事件。

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
      "content": "你好，请问有什么可以帮助您？",
      "message_type": "TEXT"
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

通知服务器管理员正在输入或已停止输入。

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

### 3.5 `members.request` (管理员专属)

请求当前聊天室的成员列表。

- **Payload**: (空对象 `{}`)
- **示例**:
  ```json
  {
    "type": "members.request",
    "payload": {},
    "request_id": "req-members-789"
  }
  ```

---

## 4. 服务器到管理员事件 (S2C)

服务器会向管理员客户端推送以下事件。

### 4.1 `message.new`

当有新消息（来自用户、其他管理员或AI）时，服务器会广播此事件。

- **Payload**:
  - `message` (对象): **必须**。完整的消息对象。
    - `id` (整数): 消息的唯一ID。
    - `chat_id` (整数): 所属聊天ID。
    - `content` (字符串): 消息内容。
    - `message_type` (字符串): 消息类型 (例如 `TEXT`, `ASSISTANT`)。
    - `sender_id` (整数): 发送者ID。
    - `sender_type` (字符串): 发送者类型 (`official` 或 `third_party`)。
    - `created_at` (字符串): ISO 8601 格式的时间戳。
    - `metadata` (对象): 附加元数据。
- **示例**:
  ```json
  {
    "type": "message.new",
    "payload": {
      "message": {
        "id": 103,
        "chat_id": 1,
        "content": "我遇到了一个问题。",
        "message_type": "TEXT",
        "sender_id": 5678,
        "sender_type": "third_party",
        "created_at": "2023-10-27T10:00:00Z",
        "metadata": {}
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

当聊天中有人（用户或其他管理员）正在输入或停止输入时广播。

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
        "user_id": 5678,
        "client_id": "client-abc-123",
        "user_type": "third_party"
      },
      "is_typing": true
    }
  }

### 4.4 `message.read.update`

当一条或多条消息被标记为已读时，服务器会向聊天中的所有客户端（包括发送者）广播此事件。

- **Payload**:
  - `sender` (对象): **必须**。发起已读操作的用户的身份信息。
  - `messages` (消息对象数组): **必须**。已更新的消息对象列表，其结构与 `message.new` 中的 `message` 相同。这些对象将包含更新后的已读状态（例如，`read_by` 字段）。
- **示例**:
  ```json
  {
    "type": "message.read.update",
    "payload": {
      "sender": {
        "user_id": 1001,
        "client_id": "admin-xyz-789",
        "user_type": "official"
      },
      "messages": [
        {
          "id": 101,
          "chat_id": 1,
          "content": "我遇到了一个问题。",
          "message_type": "TEXT",
          "sender_id": 5678,
          "created_at": "2023-10-27T10:00:00Z",
          "metadata": {},
          "read_by": [1001]
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
      "content": "用户 5678 已加入聊天"
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

### 4.7 `members.response` (管理员专属)

响应 `members.request` 请求，返回成员列表。

- **request_id**: 与原始请求的 `request_id` 匹配。
- **Payload**:
  - `members` (字符串数组): **必须**。当前在此聊天中的所有 `client_id` 的列表。
  - `count` (整数): **必须**。连接的客户端总数。
- **示例**:
  ```json
  {
    "type": "members.response",
    "payload": {
      "members": ["client-abc-123", "admin-xyz-789"],
      "count": 2
    },
    "request_id": "req-members-789"
  }
  ```