from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time

from app.models.database import get_db
from app.core.ws import connection_manager
from app.services.chat import ChatService
from app.services.session import SessionManager
from app.schemas.identity import UserContext, UserType
from app.core.logger import Logger
from .chat_manager import ChatWebSocketManager

# 创建管理员WebSocket聊天路由
router = APIRouter()

@router.websocket("/{chat_id}")
async def admin_chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    client_id: str,
    admin_id: int,
    db: Session = Depends(get_db)
):
    """管理员WebSocket连接"""
    # 获取或创建trace_id
    trace_id = websocket.headers.get("X-Trace-ID")
    trace_id = Logger.init_trace(
        trace_id=trace_id,
        chat_id=chat_id,
        client_id=client_id,
        admin_id=admin_id,
        user_type="admin"
    )
    
    start_time = time.time()
    Logger.websocket_event(
        event_type="管理员WebSocket连接请求",
        chat_id=chat_id,
        client_id=client_id,
        admin_id=admin_id
    )
    
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
            Logger.warning(
                "管理员权限验证失败，拒绝WebSocket连接",
                chat_id=chat_id,
                client_id=client_id,
                admin_id=admin_id
            )
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
        
        connection_time = time.time() - start_time
        Logger.info(
            f"管理员WebSocket连接成功，耗时: {connection_time:.2f}秒",
            chat_id=chat_id,
            client_id=client_id,
            admin_id=admin_id,
            trace_id=trace_id
        )
        
        try:
            while True:
                # 接收消息
                message_data = await websocket.receive_json()
                
                # 处理心跳
                if message_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "trace_id": trace_id})
                    Logger.debug(
                        "管理员心跳",
                        chat_id=chat_id,
                        client_id=client_id,
                        admin_id=admin_id
                    )
                    continue
                    
                # 处理管理员消息
                await ws_manager.handle_admin_message(message_data)
                
        except WebSocketDisconnect:
            # 清理连接
            connection_manager.disconnect(chat_id, client_id)
            await session_manager.close_session(chat_id, client_id)
            Logger.websocket_event(
                event_type="管理员WebSocket断开连接",
                chat_id=chat_id,
                client_id=client_id,
                admin_id=admin_id
            )
            
    except Exception as e:
        Logger.error(
            f"管理员WebSocket错误: {str(e)}",
            chat_id=chat_id,
            client_id=client_id,
            admin_id=admin_id,
            error=str(e),
            trace_id=trace_id
        )
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR) 