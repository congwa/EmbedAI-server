from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.chat import ChatService
from app.schemas.chat import ChatResponse, ChatListResponse, ChatRequest, ChatMessageResponse, MarkReadRequest, MessageResponse
from typing import Optional, List
from app.core.response import ResponseModel
from app.core.response_utils import success_response
from app.core.exceptions_new import SystemError, BusinessError, ResourceNotFoundError, ForbiddenError
from app.core.logger import Logger

# 创建客户端聊天路由
router = APIRouter()

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
    
    return success_response(data=chat_response)

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
    return success_response(data=ChatListResponse(total=total, items=chats))

@router.get("/{chat_id}", response_model=ResponseModel[ChatResponse])
async def get_chat(
    chat_id: int,
    third_party_user_id: int,
    db: Session = Depends(get_db)
):
    """获取聊天会话详情"""
    chat_service = ChatService(db)
    
    # 验证会话所有权
    if not await chat_service.check_chat_ownership(chat_id, third_party_user_id):
        raise ForbiddenError("您无权访问该聊天会话")
    
    chat = await chat_service.get_chat(chat_id)
    
    # 标记消息为已读
    await chat_service.mark_messages_as_read(
        chat_id=chat_id,
        user_id=third_party_user_id
    )
    
    return success_response(data=chat)

@router.get("/{chat_id}/messages", response_model=ResponseModel)
async def get_messages(
    chat_id: int,
    third_party_user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取聊天消息列表"""
    chat_service = ChatService(db)
    
    # 验证会话所有权
    if not await chat_service.check_chat_ownership(chat_id, third_party_user_id):
        raise ForbiddenError("您无权访问该聊天会话")
    
    # 获取消息
    user = await chat_service.get_or_create_third_party_user(third_party_user_id)
    if not user.identity:
        raise ResourceNotFoundError("用户身份", third_party_user_id)

    messages_data = await chat_service.get_messages(
        chat_id=chat_id,
        user_identity_id=user.identity.id,
        page=page,
        page_size=page_size
    )
    
    return success_response(data=messages_data)

@router.delete("/{chat_id}", response_model=ResponseModel)
async def delete_chat(
    chat_id: int,
    third_party_user_id: int,
    db: Session = Depends(get_db)
):
    """删除聊天会话"""
    chat_service = ChatService(db)
    
    # 验证会话所有权
    if not await chat_service.check_chat_ownership(chat_id, third_party_user_id):
        raise ForbiddenError("您无权删除该聊天会话")
    
    # 删除会话
    await chat_service.delete_chat(
        chat_id=chat_id,
        user_id=third_party_user_id
    )
    
    return success_response(data={"message": "聊天会话已删除", "chat_id": chat_id})


@router.post("/{chat_id}/mark_read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_as_read(
    chat_id: int,
    third_party_user_id: int,
    request: MarkReadRequest,
    db: Session = Depends(get_db),
):
    """将指定会话中的消息标记为已读"""
    chat_service = ChatService(db)

    # 验证会话所有权
    if not await chat_service.check_chat_ownership(chat_id, third_party_user_id):
        raise ForbiddenError("您无权访问该聊天会话")

    user = await chat_service.get_or_create_third_party_user(third_party_user_id)
    if not user.identity:
        raise ResourceNotFoundError("用户身份", third_party_user_id)

    await chat_service.mark_messages_as_read(
        chat_id=chat_id,
        user_identity_id=user.identity.id,
        last_read_message_id=request.last_read_message_id
    )
    return 