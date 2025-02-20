from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.auth import get_current_user, get_current_admin_user
from app.models.database import get_db
from app.models.user import User
from app.models.enums import ChatMode, MessageType
from app.services.chat import ChatService
from app.core.ws import connection_manager

router = APIRouter()

@router.websocket("/ws/chat/{chat_id}/user")
async def chat_websocket_user(
    websocket: WebSocket,
    chat_id: int,
    client_id: str,
    db: Session = Depends(get_db)
):
    """用户端WebSocket连接
    
    用于处理第三方用户的实时聊天连接
    支持：
    1. 心跳检测
    2. 消息重试
    3. 连接状态监控
    """
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    
    # 连接WebSocket
    await connection_manager.connect(
        chat_id=chat_id,
        client_id=f"user_{client_id}",
        websocket=websocket,
        is_admin=False
    )
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 处理心跳响应
            if data.get("type") == "pong":
                continue
                
            content = data.get("content")
            if not content:
                continue
                
            # 添加用户消息
            message = await chat_service.add_message(
                chat_id=chat_id,
                content=content,
                message_type=MessageType.USER
            )
            
            # 广播消息给所有连接
            await connection_manager.broadcast_to_chat(
                chat_id,
                {
                    "type": "message",
                    "data": {
                        "id": message.id,
                        "content": message.content,
                        "message_type": message.message_type,
                        "created_at": message.created_at.isoformat(),
                        "metadata": message.metadata
                    }
                }
            )
            
            # 如果是AI模式，使用知识库生成回复
            if chat.chat_mode == ChatMode.AI:
                # TODO: 调用知识库服务生成回复
                ai_response = "这是AI的回复"  # 临时占位
                
                ai_message = await chat_service.add_message(
                    chat_id=chat_id,
                    content=ai_response,
                    message_type=MessageType.ASSISTANT
                )
                
                # 广播AI回复
                await connection_manager.broadcast_to_chat(
                    chat_id,
                    {
                        "type": "message",
                        "data": {
                            "id": ai_message.id,
                            "content": ai_message.content,
                            "message_type": ai_message.message_type,
                            "created_at": ai_message.created_at.isoformat(),
                            "metadata": ai_message.metadata
                        }
                    }
                )
            
    except WebSocketDisconnect:
        connection_manager.disconnect(chat_id, f"user_{client_id}")
        
        # 标记会话为非活跃
        chat.is_active = False
        await db.commit()

@router.websocket("/ws/chat/{chat_id}/admin")
async def chat_websocket_admin(
    websocket: WebSocket,
    chat_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员端WebSocket连接
    
    用于处理管理员的实时聊天连接
    支持：
    1. 心跳检测
    2. 消息重试
    3. 连接状态监控
    """
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    
    # 检查是否是当前会话的管理员
    if chat.chat_mode == ChatMode.HUMAN and chat.current_admin_id != current_admin.id:
        raise HTTPException(403, "您不是当前会话的服务人员")
    
    # 连接WebSocket
    await connection_manager.connect(
        chat_id=chat_id,
        client_id=f"admin_{current_admin.id}",
        websocket=websocket,
        is_admin=True
    )
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 处理心跳响应
            if data.get("type") == "pong":
                continue
                
            content = data.get("content")
            if not content:
                continue
                
            # 检查是否是人工模式
            if chat.chat_mode != ChatMode.HUMAN:
                await websocket.send_json({
                    "type": "error",
                    "message": "当前不是人工服务模式"
                })
                continue
            
            # 添加管理员消息
            await chat_service.add_message(
                chat_id=chat_id,
                content=content,
                message_type=MessageType.ADMIN,
                sender_id=current_admin.id
            )
            
    except WebSocketDisconnect:
        connection_manager.disconnect(chat_id, f"admin_{current_admin.id}") 