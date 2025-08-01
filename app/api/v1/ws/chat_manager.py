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
    Manages WebSocket chat connections, implementing V2 of the chat protocol.

    Protocol V2 Summary:
    - All messages are JSON objects with `type`, `payload`, and optional `request_id`.
    - `type` uses a 'domain.action' format (e.g., 'message.create').
    - `request_id` is used to correlate requests and responses.
    - Standardized error responses.
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
        """Main message handler, dispatches based on message type."""
        msg_type = message_data.get("type")
        payload = message_data.get("payload", {})
        request_id = message_data.get("request_id")

        if msg_type is None:
            await self._send_error_response("INVALID_FORMAT", "Message 'type' is missing.", request_id)
            return

        handler = self.message_handlers.get(msg_type)
        if handler:
            await handler(payload, request_id)
        else:
            await self._send_error_response("UNKNOWN_TYPE", f"Unknown message type: {msg_type}", request_id)

    async def _send_response(self, type: str, payload: Dict[str, Any], request_id: Optional[str] = None):
        """Sends a structured response to the client."""
        response = {"type": type, "payload": payload}
        if request_id:
            response["request_id"] = request_id
        await self.websocket.send_json(response)

    async def _send_error_response(self, code: str, message: str, request_id: Optional[str] = None):
        """Sends a standardized error response."""
        await self._send_response(
            "response.error",
            {"code": code, "message": message},
            request_id
        )

    async def _broadcast_event(self, type: str, payload: Dict[str, Any], exclude_self: bool = True):
        """Broadcasts an event to all clients in the chat."""
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
        """Handles incoming new messages."""
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
        """Handles request for message history."""
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
        """Handles request for chat members."""
        members = connection_manager.get_clients_in_chat(self.chat_id)
        member_ids = list(members.keys())
        await self._send_response(
            "members.response",
            {"members": member_ids, "count": len(member_ids)},
            request_id
        )

    async def _handle_typing_event(self, payload: Dict[str, Any], request_id: Optional[str]):
        """Handles typing start/stop events."""
        is_typing = payload.get("is_typing", False)
        await self._broadcast_event("typing.update", {"is_typing": is_typing})

    async def _handle_read_event(self, payload: Dict[str, Any], request_id: Optional[str]):
        """Handles message read receipts."""
        message_ids = payload.get("message_ids", [])
        if not isinstance(message_ids, list):
            await self._send_error_response("INVALID_PAYLOAD", "'message_ids' must be a list.", request_id)
            return

        await self.chat_service.mark_messages_as_read(
            chat_id=self.chat_id,
            message_ids=message_ids,
            user_id=self.user_context.user_id
        )
        await self._broadcast_event("message.read.update", {"message_ids": message_ids})

    async def _handle_ai_response(self, user_query: str):
        """Generates and broadcasts an AI response."""
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
            Logger.error(f"AI response generation failed: {e}", chat_id=self.chat_id, error=str(e))
            await self._broadcast_event(
                "notification.system",
                {"level": "error", "content": "Sorry, an error occurred while generating a response."},
                exclude_self=False
            )

    async def send_initial_history(self):
        """Sends initial message history upon connection."""
        await self._handle_history_request({"limit": 20}, None)

    async def send_notification(self, content: str, level: str = "info"):
        """Sends a system notification to all users in the chat."""
        await self._broadcast_event(
            "notification.system",
            {"level": level, "content": content},
            exclude_self=False
        )