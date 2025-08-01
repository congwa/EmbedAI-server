# WebSocket API for Admins (Protocol V2)

This document outlines the WebSocket protocol for real-time chat communication between admin clients and the server. The admin protocol is an extension of the client protocol, with additional capabilities.

## Connection

- **Endpoint**: `ws://<server_address>/api/v1/ws/admin/{chat_id}`
- **Parameters**:
  - `chat_id` (int, path): The ID of the chat session.
  - `client_id` (str, query): A unique identifier for the client instance.
  - `admin_id` (int, query): The ID of the admin user.
- **Headers**:
  - `X-Trace-ID` (str, optional): A trace ID for request correlation.

## General Message Format

The message format is identical to the client protocol. All messages are JSON objects with `type`, `payload`, and an optional `request_id`.

```json
{
  "type": "domain.action",
  "payload": { ... },
  "request_id": "unique_string_for_request" 
}
```

---

## Admin-to-Server Events

Admins can use all **Client-to-Server Events** (like `message.create`, `history.request`, etc.) plus the following admin-specific events.

### 1. Request Chat Members

Retrieves a list of all clients currently connected to the chat.

- **type**: `members.request`
- **payload**: (empty)
- **Example**:
  ```json
  {
    "type": "members.request",
    "payload": {},
    "request_id": "req-admin-456"
  }
  ```

---

## Server-to-Admin Events

Admins receive all **Server-to-Client Events** (like `message.new`, `typing.update`, etc.) plus the following admin-specific events.

### 1. Members Response

Returns the list of connected clients in response to a `members.request`.

- **type**: `members.response`
- **request_id**: Matches the ID from the original request.
- **payload**:
  - `members` (array of strings): A list of `client_id`s.
  - `count` (int): The number of connected clients.

---

## Shared Events Summary

For clarity, admins have access to the full suite of events available to clients, including:

- **Sending**:
  - `message.create`
  - `history.request`
  - `typing.start` / `typing.stop`
  - `message.read`
- **Receiving**:
  - `message.new`
  - `history.response`
  - `typing.update`
  - `notification.system`
  - `response.error`