from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.chat import ChatService
from app.schemas.chat import ChatResponse, ChatListResponse, ChatRequest, ChatMessageResponse
from typing import Optional
from app.core.response import ResponseModel, APIResponse
from app.core.logger import Logger
router = APIRouter(prefix="/chat", tags=["client-chat"])

@router.post("/create", response_model=ResponseModel[ChatResponse])
async def create_chat(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """创建聊天会话并返回chat_id
    
    Args:
        chat_request (ChatRequest): 包含third_party_user_id, kb_id和title的请求
    
    Returns:
        dict: 包含chat_id的响应
    """
    chat_service = ChatService(db)
    chat = await chat_service.create_chat(
        chat_request.third_party_user_id,
        chat_request.kb_id,
        chat_request.title
    )
    
    chat_response = ChatResponse(
        id=chat.id,
        title=chat.title,
        chat_mode=chat.chat_mode,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        is_active=chat.is_active,
        messages=[]
    )
    
    return APIResponse.success(data=chat_response)

@router.get("/list", response_model=ResponseModel[ChatListResponse])
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
    return APIResponse.success(data=ChatListResponse(total=total, items=chats)) 
