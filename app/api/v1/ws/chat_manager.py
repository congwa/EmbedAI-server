from typing import Dict, Any, Optional, Callable, Awaitable
from fastapi import WebSocket, status
from sqlalchemy.orm import Session
import time
import json

from app.services.chat import ChatService
from app.services.chat_ai import ChatAIService
from app.services.session import SessionManager
from app.schemas.identity import UserContext
from app.models.enums import ChatMode, MessageType
from app.core.logger import Logger
from app.core.ws import connection_manager

class ChatWebSocketManager:
    """
    管理WebSocket聊天连接，实现V2聊天协议。

    协议V2摘要:
    - 所有消息都是JSON对象，包含 `type`, `payload`, 和可选的 `request_id`。
    - `type` 使用 'domain.action' 格式 (例如, 'message.create')。
    - `request_id` 用于关联请求和响应。
    - 标准化的错误响应。
    """

    def __init__(
        self,
        websocket: WebSocket,
        chat_id: int,
        user_context: UserContext,
        db: Session
    ):
        self.websocket = websocket
        self.chat_id = chat_id
        self.user_context = user_context
        self.db = db
        self.chat_service = ChatService(db)
        self.chat_ai_service = ChatAIService(db)
        self.session_manager = SessionManager(db)
        self.trace_id = Logger.get_trace_id()

        self.message_handlers: Dict[str, Callable[[Dict[str, Any], Optional[str]], Awaitable[None]]] = {
            "message.create": self._handle_create_message,
            "history.request": self._handle_history_request,
            "members.request": self._handle_get_members_request,
            "typing.start": self._handle_typing_event,
            "typing.stop": self._handle_typing_event,
            "message.read": self._handle_read_event,
        }

    async def handle_message(self, message_data: Dict[str, Any]):
        """主消息处理器，根据消息类型分发。"""
        msg_type = message_data.get("type")
        payload = message_data.get("payload", {})
        request_id = message_data.get("request_id")

        if msg_type is None:
            await self._send_error_response("INVALID_FORMAT", "消息缺少 'type' 字段。", request_id)
            return

        handler = self.message_handlers.get(msg_type)
        if handler:
            await handler(payload, request_id)
        else:
            await self._send_error_response("UNKNOWN_TYPE", f"未知的消息类型: {msg_type}", request_id)

    async def _send_response(self, type: str, payload: Dict[str, Any], request_id: Optional[str] = None):
        """向客户端发送结构化响应。"""
        response = {"type": type, "payload": payload}
        if request_id:
            response["request_id"] = request_id
        await self.websocket.send_json(response)

    async def _send_error_response(self, code: str, message: str, request_id: Optional[str] = None):
        """发送标准化的错误响应。"""
        await self._send_response(
            "response.error",
            {"code": code, "message": message},
            request_id
        )

    async def _broadcast_event(self, type: str, payload: Dict[str, Any], exclude_self: bool = True):
        """向聊天中的所有客户端广播一个事件。"""
        event_message = {
            "type": type,
            "payload": {
                "sender": {
                    "user_id": self.user_context.user_id,
                    "client_id": self.user_context.client_id,
                    "user_type": self.user_context.user_type.value
                },
                **payload
            }
        }
        exclude_client = self.user_context.client_id if exclude_self else None
        await connection_manager.broadcast_to_chat(
            self.chat_id,
            event_message,
            exclude_client=exclude_client
        )

    async def _handle_create_message(self, payload: Dict[str, Any], request_id: Optional[str]):
        """处理接收到的新消息。"""
        content = payload.get("content")
        if not content:
            await self._send_error_response("INVALID_PAYLOAD", "Message content is missing.", request_id)
            return

        message = await self.chat_service.add_message(
            chat_id=self.chat_id,
            content=content,
            message_type=MessageType.USER if self.user_context.user_type == "third_party" else MessageType.ADMIN,
            sender_id=self.user_context.user_id,
            doc_metadata={"client_id": self.user_context.client_id, "trace_id": self.trace_id}
        )

        await self._broadcast_event("message.new", {"message": json.loads(message.to_json())}, exclude_self=False)

        chat = await self.chat_service.get_chat(self.chat_id)
        if chat.chat_mode == ChatMode.AI and self.user_context.user_type == "third_party":
            await self._handle_ai_response(content)

    async def _handle_history_request(self, payload: Dict[str, Any], request_id: Optional[str]):
        """处理消息历史记录请求。"""
        before_message_id = payload.get("before_message_id")
        limit = payload.get("limit", 20)

        history = await self.chat_service.get_message_history(
            chat_id=self.chat_id,
            before_message_id=before_message_id,
            limit=limit
        )

        await self._send_response(
            "history.response",
            {"messages": [json.loads(msg.to_json()) for msg in history]},
            request_id
        )

    async def _handle_get_members_request(self, payload: Dict[str, Any], request_id: Optional[str]):
        """处理聊天成员列表请求。"""
        members = connection_manager.get_clients_in_chat(self.chat_id)
        member_ids = list(members.keys())
        await self._send_response(
            "members.response",
            {"members": member_ids, "count": len(member_ids)},
            request_id
        )

    async def _handle_typing_event(self, payload: Dict[str, Any], request_id: Optional[str]):
        """处理正在输入开始/停止事件。"""
        is_typing = payload.get("is_typing", False)
        await self._broadcast_event("typing.update", {"is_typing": is_typing})

    async def _handle_read_event(self, payload: Dict[str, Any], request_id: Optional[str]):
        """处理消息已读回执。"""
        message_ids = payload.get("message_ids", [])
        if not isinstance(message_ids, list):
            await self._send_error_response("INVALID_PAYLOAD", "'message_ids' 必须是一个列表。", request_id)
            return

        await self.chat_service.mark_messages_as_read(
            chat_id=self.chat_id,
            message_ids=message_ids,
            user_id=self.user_context.user_id
        )
        await self._broadcast_event("message.read.update", {"message_ids": message_ids})

    async def _handle_ai_response(self, user_query: str):
        """生成并广播AI响应。"""
        try:
            chat = await self.chat_service.get_chat(self.chat_id)
            ai_response = await self.chat_ai_service.generate_response(
                chat_id=self.chat_id,
                user_query=user_query,
                kb_id=chat.knowledge_base_id,
                user_context=self.user_context
            )

            ai_message = await self.chat_service.add_message(
                chat_id=self.chat_id,
                content=ai_response["content"],
                message_type=MessageType.ASSISTANT,
                doc_metadata={**ai_response["metadata"], "is_ai": True, "trace_id": self.trace_id}
            )
            await self._broadcast_event("message.new", {"message": json.loads(ai_message.to_json())}, exclude_self=False)
        except Exception as e:
            Logger.error(f"AI响应生成失败: {e}", chat_id=self.chat_id, error=str(e))
            await self._broadcast_event(
                "notification.system",
                {"level": "error", "content": "抱歉，生成AI响应时发生错误。"},
                exclude_self=False
            )

    async def send_initial_history(self):
        """连接成功后发送初始消息历史记录。"""
        await self._handle_history_request({"limit": 20}, None)

    async def send_notification(self, content: str, level: str = "info"):
        """向聊天中的所有用户发送系统通知。"""
        await self._broadcast_event(
            "notification.system",
            {"level": level, "content": content},
            exclude_self=False
        )