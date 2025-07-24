from typing import Dict, Any
from fastapi import WebSocket, status
from sqlalchemy.orm import Session

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
        
    async def handle_user_message(
        self,
        message_data: Dict[str, Any]
    ) -> None:
        """处理用户消息"""
        # 验证会话状态
        if not await self.session_manager.validate_session(
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            third_party_user_id=self.user_context.user_id
        ):
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
                "identity_id": self.user_context.identity_id
            }
        )
        
        # 广播消息
        await self._broadcast_message(message)
        
        # 获取聊天模式
        chat = await self.chat_service.get_chat(self.chat_id)
        
        # AI模式自动回复
        if chat.chat_mode == ChatMode.AI:
            await self._handle_ai_response(message_data["content"])
            
    async def handle_admin_message(
        self,
        message_data: Dict[str, Any]
    ) -> None:
        """处理管理员消息"""
        # 验证会话状态
        if not await self.session_manager.validate_session(
            chat_id=self.chat_id,
            client_id=self.user_context.client_id,
            official_user_id=self.user_context.user_id
        ):
            await self.websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # 获取聊天模式
        chat = await self.chat_service.get_chat(self.chat_id)
        if chat.chat_mode != ChatMode.HUMAN:
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
                "is_admin": True
            }
        )
        
        # 广播消息
        await self._broadcast_message(message)
        
    async def _handle_ai_response(
        self,
        user_query: str
    ) -> None:
        """处理AI回复"""
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
                    "identity_id": self.user_context.identity_id
                }
            )
            
            # 广播AI回复
            await self._broadcast_message(ai_message)
            
        except Exception as e:
            Logger.error(f"AI response generation failed: {str(e)}")
            
            # 发送错误消息
            error_message = await self.chat_service.add_message(
                chat_id=self.chat_id,
                content="抱歉，生成回复时发生错误。",
                message_type=MessageType.SYSTEM,
                doc_metadata={
                    "error": str(e),
                    "client_id": self.user_context.client_id,
                    "identity_id": self.user_context.identity_id
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
        await connection_manager.broadcast_to_chat(
            chat_id=self.chat_id,
            message={
                "type": message_type,
                "data": {
                    "id": message.id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "created_at": message.created_at,
                    "sender_id": message.sender_id,
                    "doc_metadata": message.doc_metadata
                }
            },
            exclude_client=self.user_context.client_id
        ) 