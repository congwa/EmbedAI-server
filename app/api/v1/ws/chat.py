from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.database import get_db
from app.core.ws import connection_manager
from app.services.chat import ChatService
from app.services.chat_ai import ChatAIService
from app.services.session import SessionManager
from app.schemas.chat import ChatMessageCreate
from app.schemas.identity import UserContext, UserType
from app.models.enums import ChatMode, MessageType
from app.core.logger import Logger

router = APIRouter()

class ChatWebSocketManager:
    """聊天WebSocket管理器"""
    
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
            metadata={
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
            metadata={
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
                metadata={
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
                metadata={
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
                    "metadata": message.metadata
                }
            },
            exclude_client=self.user_context.client_id
        )

@router.websocket("/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    client_id: str,
    third_party_user_id: int,
    db: Session = Depends(get_db)
):
    """第三方用户WebSocket连接"""
    try:
        # 创建服务实例
        session_manager = SessionManager(db)
        chat_service = ChatService(db)
        
        # 创建或更新用户身份
        identity = await session_manager.create_or_update_identity(
            client_id=client_id,
            third_party_user_id=third_party_user_id
        )
        
        # 创建用户上下文
        user_context = UserContext(
            user_type=UserType.THIRD_PARTY,
            user_id=third_party_user_id,
            client_id=client_id,
            identity_id=identity.id
        )
        
        # 验证并获取聊天会话
        chat = await chat_service.get_chat(chat_id)
        if not chat or chat.third_party_user_id != third_party_user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # 创建或获取活跃的会话
        chat_session = await session_manager.create_chat_session(
            chat_id=chat_id,
            user_identity_id=identity.id,
            client_id=client_id
        )
        
        # 接受WebSocket连接
        await websocket.accept()
        
        # 添加到连接管理器
        await connection_manager.connect(
            chat_id=chat_id,
            client_id=client_id,
            websocket=websocket
        )
        
        # 创建WebSocket管理器
        ws_manager = ChatWebSocketManager(
            websocket=websocket,
            chat_id=chat_id,
            user_context=user_context,
            db=db
        )
        
        try:
            while True:
                # 接收消息
                message_data = await websocket.receive_json()
                
                # 处理心跳
                if message_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                    
                # 处理用户消息
                await ws_manager.handle_user_message(message_data)
                
        except WebSocketDisconnect:
            # 清理连接
            connection_manager.disconnect(chat_id, client_id)
            await session_manager.close_session(chat_id, client_id)
            
    except Exception as e:
        Logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.websocket("/admin/{chat_id}")
async def admin_chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    client_id: str,
    admin_id: int,
    db: Session = Depends(get_db)
):
    """管理员WebSocket连接"""
    try:
        # 创建服务实例
        session_manager = SessionManager(db)
        chat_service = ChatService(db)
        
        # 创建或更新管理员身份
        identity = await session_manager.create_or_update_identity(
            client_id=client_id,
            official_user_id=admin_id
        )
        
        # 创建用户上下文
        user_context = UserContext(
            user_type=UserType.OFFICIAL,
            user_id=admin_id,
            client_id=client_id,
            identity_id=identity.id
        )
        
        # 验证管理员权限
        chat = await chat_service.get_chat(chat_id)
        if not chat or not await chat_service.check_admin_permission(admin_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # 创建或获取活跃的会话
        chat_session = await session_manager.create_chat_session(
            chat_id=chat_id,
            user_identity_id=identity.id,
            client_id=client_id
        )
        
        # 接受WebSocket连接
        await websocket.accept()
        
        # 添加到连接管理器
        await connection_manager.connect(
            chat_id=chat_id,
            client_id=client_id,
            websocket=websocket
        )
        
        # 创建WebSocket管理器
        ws_manager = ChatWebSocketManager(
            websocket=websocket,
            chat_id=chat_id,
            user_context=user_context,
            db=db
        )
        
        try:
            while True:
                # 接收消息
                message_data = await websocket.receive_json()
                
                # 处理心跳
                if message_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                    
                # 处理管理员消息
                await ws_manager.handle_admin_message(message_data)
                
        except WebSocketDisconnect:
            # 清理连接
            connection_manager.disconnect(chat_id, client_id)
            await session_manager.close_session(chat_id, client_id)
            
    except Exception as e:
        Logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR) 