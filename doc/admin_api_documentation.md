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

消息格式与客户端协议完全相同。

```json
{
  "type": "domain.action",
  "payload": { ... },
  "request_id": "unique_string_for_request"
}
```

- `type` (字符串): **必须**。
- `payload` (对象): **必须**。
- `request_id` (字符串, 可选)。

---

## 3. 管理员到服务器事件 (C2S)

管理员可以使用所有**客户端C2S事件** (参见客户端文档的 `message.create`, `history.request`, `typing.start`/`stop`, `message.read`)，并额外增加了以下事件：

### 3.1. 请求聊天成员列表

检索当前连接到此聊天室的所有客户端实例的列表。

- **type**: `members.request`
- **payload**: (空对象 `{}`)
- **示例**:
  ```json
  {
    "type": "members.request",
    "payload": {},
    "request_id": "req-admin-members-789"
  }
  ```

---

## 4. 服务器到管理员事件 (S2C)

管理员会接收所有**客户端S2C事件** (参见客户端文档的 `message.new`, `history.response`, `typing.update`, `notification.system`, `response.error`)，并额外增加了以下事件：

### 4.1. 成员列表响应

响应管理员的 `members.request` 请求。

- **type**: `members.response`
- **request_id**: 与原始请求的 `request_id` 匹配。
- **payload**:
  - `members` (字符串数组): 当前在此聊天中的所有 `client_id` 的列表。
  - `count` (整数): 连接的客户端总数。

---

## 5. 共享事件的快速参考

为方便起见，下表总结了管理员可用的所有事件。详细的 `payload` 结构请参考客户端API文档。

| 事件类型 (type)         | 方向 | 描述                       |
| ----------------------- | ---- | -------------------------- |
| `message.create`        | C2S  | 发送一条管理员消息         |
| `history.request`       | C2S  | 请求历史消息               |
| `typing.start` / `stop` | C2S  | 更新输入状态               |
| `message.read`          | C2S  | 标记消息为已读             |
| `members.request`       | C2S  | **(管理员专属)** 请求成员列表 |
|                         |      |                            |
| `message.new`           | S2C  | 接收新消息                 |
| `history.response`      | S2C  | 接收历史消息               |
| `typing.update`         | S2C  | 接收输入状态更新           |
| `notification.system`   | S2C  | 接收系统通知               |
| `response.error`        | S2C  | 接收错误响应               |
| `members.response`      | S2C  | **(管理员专属)** 接收成员列表 |