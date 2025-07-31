from typing import Dict, Any, Optional
from fastapi import WebSocket, status
from sqlalchemy.orm import Session
import time

from app.services.chat import ChatService
from app.services.chat_ai import ChatAIService
from app.services.session import SessionManager
from app.schemas.identity import UserContext
from app.models.enums import ChatMode, MessageType
from app.core.logger import Logger
from app.core.ws import connection_manager

class ChatWebSocketManager:
    """聊天WebSocket管理器
    
    负责处理WebSocket连接的消息处理、会话验证和消息广播
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
        
        # 初始化链路追踪
        trace_id = websocket.headers.get("X-Trace-ID")
        self.trace_id = Logger.init_trace(
            trace_id=trace_id,
            chat_id=chat_id,
            client_id=user_context.client_id,
            user_id=user_context.user_id,
            user_type=user_context.user_type
        )
        
        Logger.websocket_event(
            event_type="连接初始化",
            chat_id=chat_id,
            client_id=user_context.client_id,
            user_id=user_context.user_id,
            user_type=user_context.user_type
        )

    async def send_message(self, message: Dict[str, Any]):
        """发送格式化消息到当前WebSocket"""
        await self.websocket.send_json(message)

    def _format_message_for_response(self, message: Any, message_type: str = "message") -> Dict[str, Any]:
        """格式化消息以便发送"""
        return {
            "type": message_type,
            "data": {
                "id": message.id,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at.isoformat(),
                "sender_id": message.sender_id,
                "doc_metadata": message.doc_metadata,
                "trace_id": self.trace_id
            }
        }

    async def send_notification(self, content: str, message_type: str = "system"):
        """向聊天室广播通知"""
        notification = await self.chat_service.add_message(
            chat_id=self.chat_id,
            content=content,
            message_type=MessageType.SYSTEM,
            doc_metadata={"trace_id": self.trace_id}
        )
        await self._broadcast_message(notification, message_type=message_type)

    async def handle_user_message(
        self,
        message_data: Dict[str, Any]
    ) -> None:
        """处理用户消息"""
        start_time = time.time()
        
        # 处理历史记录请求
        if message_data.get("type") == "get_history":
            await self._handle_history_request(message_data)
            return

        Logger.websocket_event(
            event_type="收到用户消息",
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            message_length=len(message_data.get("content", ""))
        )
        
        # 验证会话状态
        if not await self.session_manager.validate_session(
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            third_party_user_id=self.user_context.user_id
        ):
            Logger.warning(
                "会话验证失败，关闭WebSocket连接",
                chat_id=self.chat_id,
                client_id=self.user_context.client_id,
                user_id=self.user_context.user_id
            )
            await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # 添加用户消息
        message = await self.chat_service.add_message(
            chat_id=self.chat_id,
            content=message_data["content"],
            message_type=MessageType.USER,
            sender_id=self.user_context.user_id,
            doc_metadata={
                "client_id": self.user_context.client_id,
                "identity_id": self.user_context.identity_id,
                "trace_id": self.trace_id
            }
        )
        
        # 广播消息
        await self._broadcast_message(message)
        
        # 获取聊天模式
        chat = await self.chat_service.get_chat(self.chat_id)
        
        # AI模式自动回复
        if chat.chat_mode == ChatMode.AI:
            await self._handle_ai_response(message_data["content"])
            
        process_time = time.time() - start_time
        Logger.info(
            f"用户消息处理完成，耗时: {process_time:.2f}秒",
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            process_time=process_time
        )
            
    async def handle_admin_message(
        self,
        message_data: Dict[str, Any]
    ) -> None:
        """处理管理员消息"""
        start_time = time.time()
        
        # 处理历史记录请求
        if message_data.get("type") == "get_history":
            await self._handle_history_request(message_data)
            return

        Logger.websocket_event(
            event_type="收到管理员消息",
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            message_length=len(message_data.get("content", ""))
        )
        
        # 验证会话状态
        if not await self.session_manager.validate_session(
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            official_user_id=self.user_context.user_id
        ):
            Logger.warning(
                "管理员会话验证失败，关闭WebSocket连接",
                chat_id=self.chat_id,
                client_id=self.user_context.client_id,
                admin_id=self.user_context.user_id
            )
            await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # 获取聊天模式
        chat = await self.chat_service.get_chat(self.chat_id)
        if chat.chat_mode != ChatMode.HUMAN:
            Logger.warning(
                "当前不是人工服务模式，拒绝处理管理员消息",
                chat_id=self.chat_id,
                client_id=self.user_context.client_id,
                admin_id=self.user_context.user_id,
                chat_mode=chat.chat_mode
            )
            await self.websocket.send_json({
                "type": "error",
                "message": "当前不是人工服务模式"
            })
            return
            
        # 添加管理员消息
        message = await self.chat_service.add_message(
            chat_id=self.chat_id,
            content=message_data["content"],
            message_type=MessageType.ADMIN,
            sender_id=self.user_context.user_id,
            doc_metadata={
                "client_id": self.user_context.client_id,
                "identity_id": self.user_context.identity_id,
                "is_admin": True,
                "trace_id": self.trace_id
            }
        )
        
        # 广播消息
        await self._broadcast_message(message)
        
        process_time = time.time() - start_time
        Logger.info(
            f"管理员消息处理完成，耗时: {process_time:.2f}秒",
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            admin_id=self.user_context.user_id,
            process_time=process_time
        )

    async def _handle_history_request(self, message_data: Dict[str, Any]):
        """处理历史记录请求"""
        before_message_id = message_data.get("before_message_id")
        limit = message_data.get("limit", 20)

        history = await self.chat_service.get_message_history(
            chat_id=self.chat_id,
            before_message_id=before_message_id,
            limit=limit
        )

        response = {
            "type": "history",
            "data": [self._format_message_for_response(msg)["data"] for msg in history]
        }
        await self.send_message(response)
        
    async def _handle_ai_response(
        self,
        user_query: str
    ) -> None:
        """处理AI回复"""
        start_time = time.time()
        
        Logger.info(
            "开始生成AI回复",
            chat_id=self.chat_id,
            query_length=len(user_query)
        )
        
        try:
            # 获取知识库ID
            chat = await self.chat_service.get_chat(self.chat_id)
            
            # 生成AI回复
            ai_response = await self.chat_ai_service.generate_response(
                chat_id=self.chat_id,
                user_query=user_query,
                kb_id=chat.knowledge_base_id,
                user_context=self.user_context
            )
            
            # 添加AI消息
            ai_message = await self.chat_service.add_message(
                chat_id=self.chat_id,
                content=ai_response["content"],
                message_type=MessageType.ASSISTANT,
                doc_metadata={
                    **ai_response["metadata"],
                    "is_ai": True,
                    "client_id": self.user_context.client_id,
                    "identity_id": self.user_context.identity_id,
                    "trace_id": self.trace_id
                }
            )
            
            # 广播AI回复
            await self._broadcast_message(ai_message)
            
            process_time = time.time() - start_time
            Logger.info(
                f"AI回复生成成功，耗时: {process_time:.2f}秒",
                chat_id=self.chat_id,
                response_length=len(ai_response["content"]),
                process_time=process_time
            )
            
        except Exception as e:
            process_time = time.time() - start_time
            Logger.error(
                f"AI回复生成失败: {str(e)}",
                chat_id=self.chat_id,
                error=str(e),
                process_time=process_time
            )
            
            # 发送错误消息
            error_message = await self.chat_service.add_message(
                chat_id=self.chat_id,
                content="抱歉，生成回复时发生错误。",
                message_type=MessageType.SYSTEM,
                doc_metadata={
                    "error": str(e),
                    "client_id": self.user_context.client_id,
                    "identity_id": self.user_context.identity_id,
                    "trace_id": self.trace_id
                }
            )
            
            await self._broadcast_message(
                error_message,
                message_type="error"
            )
            
    async def _broadcast_message(
        self,
        message: Any,
        message_type: str = "message"
    ) -> None:
        """广播消息"""
        Logger.debug(
            f"广播消息: {message_type}",
            chat_id=self.chat_id,
            message_id=message.id,
            message_type=message.message_type,
            exclude_client=self.user_context.client_id
        )
        
        await connection_manager.broadcast_to_chat(
            chat_id=self.chat_id,
            message=self._format_message_for_response(message, message_type),
            exclude_client=self.user_context.client_id
        )