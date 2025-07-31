from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.chat import ChatService
from app.services.auth import get_current_admin_user
from app.models.user import User
from app.schemas.chat import ChatList
from app.core.logger import Logger
from sqlalchemy.orm import Session
from app.core.response import APIResponse, ResponseModel
from app.models.enums import ChatMode, MessageType
from app.schemas.chat import (
    ChatResponse,
    ChatMessageResponse,
    ChatMessageCreate,
    ChatListResponse
)

# 创建管理员聊天路由
router = APIRouter()

@router.get("/", response_model=ResponseModel[List[ChatListResponse]])
async def list_chats(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(False),
    all_chats: bool = Query(False, description="是否获取所有聊天室列表"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取聊天会话列表
    
    管理员可以查看：
    1. 分配给自己的人工服务会话
    2. 所有AI模式的会话
    """
    chat_service = ChatService(db)
    chats = await chat_service.list_admin_chats(
        admin_id=current_admin.id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        all_chats=all_chats
    )
    return APIResponse.success(data=chats)

@router.get("/{chat_id}", response_model=ResponseModel[ChatResponse])
async def get_chat(
    chat_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取聊天会话详情"""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    
    # 标记消息为已读
    await chat_service.mark_messages_as_read(
        chat_id=chat_id,
        user_id=current_admin.id
    )
    
    return APIResponse.success(data=chat)

@router.post("/{chat_id}/switch-mode", response_model=ResponseModel[ChatResponse])
async def switch_chat_mode(
    chat_id: int,
    mode: ChatMode,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """切换聊天模式
    
    - 切换到人工模式时，会将当前管理员设置为服务人员
    - 切换到AI模式时，会清除当前服务人员
    """
    chat_service = ChatService(db)
    chat = await chat_service.switch_chat_mode(
        chat_id=chat_id,
        admin_id=current_admin.id,
        mode=mode
    )
    return APIResponse.success(data=chat)


@router.post("/{chat_id}/join", response_model=ResponseModel[ChatResponse])
async def join_chat(
    chat_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员加入聊天"""
    chat_service = ChatService(db)
    chat = await chat_service.admin_join_chat(chat_id, current_admin.id)
    return APIResponse.success(data=chat)

@router.post("/{chat_id}/leave", response_model=ResponseModel[ChatResponse])
async def leave_chat(
    chat_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员离开聊天"""
    chat_service = ChatService(db)
    chat = await chat_service.admin_leave_chat(chat_id, current_admin.id)
    return APIResponse.success(data=chat)
@router.post("/{chat_id}/messages", response_model=ResponseModel[ChatMessageResponse])
async def send_admin_message(
    chat_id: int,
    message: ChatMessageCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """发送管理员消息
    
    - 只有在人工模式下才能发送消息
    - 只有当前服务的管理员才能发送消息
    """
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    
    # 检查是否是人工模式
    if chat.chat_mode != ChatMode.HUMAN:
        raise HTTPException(400, "当前不是人工服务模式")
        
    # 检查是否是当前会话的管理员
    if chat.current_admin_id != current_admin.id:
        raise HTTPException(403, "您不是当前会话的服务人员")
    
    # 发送消息
    chat_message = await chat_service.add_message(
        chat_id=chat_id,
        content=message.content,
        message_type=MessageType.ADMIN,
        sender_id=current_admin.id,
        doc_metadata=message.metadata
    )
    
    return APIResponse.success(data=chat_message)

@router.get("/{chat_id}/messages", response_model=ResponseModel[List[ChatMessageResponse]])
async def list_chat_messages(
    chat_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取聊天消息列表"""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    
    # 获取消息列表
    messages, total = await chat_service.list_messages(
        chat_id=chat_id,
        page=(skip // limit) + 1,
        page_size=limit
    )
    
    return APIResponse.success(data=messages)

@router.get("/users/{third_party_user_id}/stats", response_model=ResponseModel)
async def get_user_chat_stats(
    third_party_user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户聊天统计信息
    
    管理员可以查看第三方用户的聊天统计数据
    """
    Logger.info(f"Admin {current_admin.email} requesting chat stats for user {third_party_user_id}")
    
    chat_service = ChatService(db)
    chats = await chat_service.list_user_chats(
        third_party_user_id=third_party_user_id,
        limit=1000  # 获取足够多的聊天记录用于统计
    )
    
    total_chats = len(chats)
    total_messages = sum(len(chat.messages) for chat in chats if hasattr(chat, 'messages') and chat.messages)
    
    return APIResponse.success(data={
        "third_party_user_id": third_party_user_id,
        "total_chats": total_chats,
        "total_messages": total_messages,
        "last_active": max((chat.updated_at for chat in chats), default=None) if chats else None
    })

@router.get("/knowledge-bases/{kb_id}/stats", response_model=ResponseModel)
async def get_knowledge_base_chat_stats(
    kb_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库聊天统计信息
    
    管理员可以查看知识库的聊天使用统计数据
    """
    Logger.info(f"Admin {current_admin.email} requesting chat stats for knowledge base {kb_id}")
    
    # TODO: 实现知识库聊天统计功能
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="知识库聊天统计功能尚未实现"
    )

@router.post("/{chat_id}/restore", response_model=ResponseModel)
async def restore_chat(
    chat_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """恢复已删除的聊天会话
    
    管理员可以恢复任何已删除的聊天会话
    """
    Logger.info(f"Admin {current_admin.email} restoring chat {chat_id}")
    
    chat_service = ChatService(db)
    chat = await chat_service.restore_chat(
        chat_id=chat_id,
        admin_user_id=current_admin.id
    )
    return APIResponse.success(data={"message": "聊天会话已恢复", "chat_id": chat.id})

@router.get("/deleted", response_model=ResponseModel[ChatList])
async def list_deleted_chats(
    third_party_user_id: Optional[int] = None,
    knowledge_base_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取已删除的聊天会话列表
    
    管理员可以查看所有已删除的聊天会话
    支持按第三方用户ID和知识库ID筛选
    """
    Logger.info(f"Admin {current_admin.email} requesting deleted chat list")
    
    chat_service = ChatService(db)
    if third_party_user_id:
        # 获取指定用户的已删除聊天列表
        chats = await chat_service.list_user_chats(
            third_party_user_id=third_party_user_id,
            kb_id=knowledge_base_id,
            skip=skip,
            limit=limit,
            include_deleted=True
        )
        # 只返回已删除的会话
        chats = [chat for chat in chats if chat.is_deleted]
    else:
        # TODO: 实现获取所有已删除聊天会话的功能
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="获取所有已删除聊天会话功能尚未实现"
        )
    
    return APIResponse.success(data=ChatList(
        total=len(chats),
        items=chats
    )) 