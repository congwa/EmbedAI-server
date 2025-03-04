from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.chat import ChatService
from app.schemas.chat import ChatResponse, ChatListResponse
from typing import Optional

router = APIRouter(prefix="/client/chat", tags=["client-chat"])

@router.post("/create", response_model=ChatResponse)
async def create_chat(
    third_party_user_id: int,
    kb_id: int,
    title: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建聊天会话并返回chat_id
    
    Args:
        third_party_user_id (int): 第三方用户ID
        kb_id (int): 知识库ID
        title (Optional[str]): 会话标题（可选）
    
    Returns:
        dict: 包含chat_id的响应
    """
    chat_service = ChatService(db)
    chat = await chat_service.create_chat(third_party_user_id, kb_id, title)
    return {"chat_id": chat.id}

@router.get("/list", response_model=ChatListResponse)
async def list_chats(
    third_party_user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """获取聊天会话列表
    
    Args:
        third_party_user_id (int): 第三方用户ID
        skip (int): 分页起始位置
        limit (int): 每页数量
    
    Returns:
        ChatListResponse: 包含会话列表的响应
    """
    chat_service = ChatService(db)
    chats = await chat_service.list_user_chats(third_party_user_id, skip=skip, limit=limit)
    total = len(chats)  # 这里可以根据实际情况调整总数的获取方式
    return ChatListResponse(total=total, items=chats) 