# 客户端 WebSocket API (协议 V2) - 详细版

本文档详细概述了用于客户端和服务器之间实时聊天通信的 WebSocket 协议 V2。

## 1. 连接

- **端点**: `ws://<server_address>/api/v1/ws/client/{chat_id}`
- **路径参数**:
  - `chat_id` (整数): 必须的，指定要加入的聊天会话ID。
- **查询参数**:
  - `client_id` (字符串): 必须的，客户端实例的唯一标识符。
  - `third_party_user_id` (整数): 必须的，第三方系统的用户ID。
- **请求头**:
  - `X-Trace-ID` (字符串, 可选): 用于端到端请求追踪的ID。如果未提供，系统将自动生成。

## 2. 通用消息格式

所有通过 WebSocket 交换的消息都是 JSON 对象，并遵循以下结构：

```json
{
  "type": "domain.action",
  "payload": { ... },
  "request_id": "unique_string_for_request"
}
```

- `type` (字符串): **必须**。标识消息的用途，使用 `域.动作` 的约定。
- `payload` (对象): **必须**。包含与消息类型相关的数据。
- `request_id` (字符串, 可选): 由客户端为需要响应的请求生成的唯一ID。服务器将在其响应消息中原样返回此ID，用于请求-响应的精确匹配。

---

## 3. 客户端到服务器事件 (C2S)

### 3.1. 创建消息

发送一条新的聊天消息。服务器会将此消息广播给聊天室中的所有成员。

- **type**: `message.create`
- **payload**:
  - `content` (字符串): **必须**。消息的文本内容。
- **示例**:
  ```json
  {
    "type": "message.create",
    "payload": {
      "content": "你好，我的订单需要帮助。"
    }
  }
  ```

### 3.2. 请求历史记录

请求指定数量的历史消息，通常用于初次加载或滚动加载。

- **type**: `history.request`
- **payload**:
  - `before_message_id` (整数, 可选): 如果提供，则获取此消息ID之前的消息（用于分页）。
  - `limit` (整数, 可选, 默认: 20): 返回的最大消息数量。
- **示例**:
  ```json
  {
    "type": "history.request",
    "payload": {
      "limit": 50
    },
    "request_id": "req-hist-123"
  }
  ```

### 3.3. 更新输入状态

通知服务器和其他用户本客户端的输入状态。

- **type**: `typing.start` 或 `typing.stop`
- **payload**:
  - `is_typing` (布尔值): **必须**。`true` 表示用户开始输入，`false` 表示停止。
- **示例**:
  ```json
  {
    "type": "typing.start",
    "payload": { "is_typing": true }
  }
  ```

### 3.4. 标记消息已读

通知服务器某些消息已被当前用户阅读。

- **type**: `message.read`
- **payload**:
  - `message_ids` (整数数组): **必须**。已被阅读的消息ID列表。
- **示例**:
  ```json
  {
    "type": "message.read",
    "payload": {
      "message_ids": [101, 102, 103]
    }
  }
  ```

---

## 4. 服务器到客户端事件 (S2C)

### 4.1. 新消息

当有新消息（来自用户、AI或管理员）被创建时，服务器会广播此事件。

- **type**: `message.new`
- **payload**:
  - `message` (对象): 完整的聊天消息对象。
    - `id` (整数): 消息的唯一ID。
    - `content` (字符串): 消息内容。
    - `message_type` (字符串): 消息类型，枚举值包括: `"user"`, `"assistant"`, `"admin"`, `"system"`。
    - `created_at` (字符串): 消息创建时间的 ISO 8601 格式字符串。
    - `is_read` (布尔值): 消息是否已读。
    - `sender_id` (整数 | null): 发送者的ID。对于系统消息，此字段可能为 `null`。
    - `doc_metadata` (对象 | null): 附加的元数据，例如AI回复引用的文档等。

### 4.2. 历史记录响应

响应客户端的 `history.request` 请求。

- **type**: `history.response`
- **request_id**: 与原始请求的 `request_id` 匹配。
- **payload**:
  - `messages` (消息对象数组): 按时间顺序排列的历史消息列表。每个消息对象的结构与 `message.new` 事件中的 `message` 对象相同。

### 4.3. 输入状态更新

当聊天中任何成员的输入状态改变时，服务器广播此事件。

- **type**: `typing.update`
- **payload**:
  - `sender` (对象): 触发此事件的用户信息。
    - `user_id` (整数): 用户的ID。
    - `client_id` (字符串): 用户的客户端ID。
    - `user_type` (字符串): 用户类型，如 `"third_party"` 或 `"admin"`。
  - `is_typing` (布尔值): `true` 表示正在输入，`false` 表示停止输入。

### 4.4. 系统通知

用于发送系统级通知，例如用户加入/离开聊天、服务模式切换等。

- **type**: `notification.system`
- **payload**:
  - `level` (字符串): 通知级别，枚举值包括: `"info"`, `"warning"`, `"error"`。
  - `content` (字符串): 通知的文本内容。

### 4.5. 错误响应

当客户端的请求因故失败时，服务器发送此事件。

- **type**: `response.error`
- **request_id**: 与导致错误的原始请求的 `request_id` 匹配（如果可用）。
- **payload**:
  - `code` (字符串): 机器可读的错误代码，例如 `INVALID_PAYLOAD`, `UNKNOWN_TYPE`。
  - `message` (字符串): 对错误的详细、人类可读的描述。