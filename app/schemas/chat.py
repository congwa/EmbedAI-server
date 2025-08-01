from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.chat import MessageType
from app.models.enums import ChatMode
from .base import CustomBaseModel
from pydantic import field_validator
class ChatMessageBase(BaseModel):
    """聊天消息基础模型"""
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(..., description="消息类型")
    doc_metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据，如相关文档引用等")
    model_config = ConfigDict(from_attributes=True)

class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息的请求模型"""
    pass


class ChatMessage(ChatMessageBase):
    """聊天消息响应模型"""
    id: int = Field(..., description="消息ID")
    chat_id: int = Field(..., description="所属会话ID")
    created_at: datetime = Field(..., description="创建时间")
    model_config = ConfigDict(from_attributes=True)

class ChatBase(BaseModel):
    """聊天会话基础模型"""
    title: Optional[str] = Field(None, description="会话标题，默认为第一条用户消息")
    knowledge_base_id: int = Field(..., description="知识库ID")


class Chat(CustomBaseModel):
    """聊天会话响应模型"""
    id: int = Field(..., description="会话ID")
    third_party_user_id: int = Field(..., description="第三方用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: List[ChatMessage] = Field(default_factory=list, description="会话中的消息列表")
    model_config = ConfigDict(from_attributes=True)

class ChatList(BaseModel):
    """聊天会话列表响应模型"""
    total: int = Field(..., description="总会话数")
    items: List[Chat] = Field(..., description="会话列表")
    model_config = ConfigDict(from_attributes=True)

class ChatMessageResponse(CustomBaseModel):
    """聊天消息响应模型"""
    id: int = Field(..., description="消息ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(..., description="消息类型")  # 根据实际类型调整
    created_at: datetime = Field(..., description="创建时间") 
    is_read: bool = Field(..., description="是否已读")
    model_config = ConfigDict(from_attributes=True)

class ChatResponse(CustomBaseModel):
    """聊天会话响应模型"""
    id: int = Field(..., description="会话ID")
    title: Optional[str] = Field(None, description="会话标题")
    chat_mode: str = Field(..., description="聊天模式")  # 根据实际类型调整
    created_at: datetime = Field(..., description="创建时间") 
    updated_at: datetime = Field(..., description="更新时间")
    is_active: bool = Field(..., description="是否活跃")
    unread_count: int = Field(0, description="未读消息数")
    messages: Optional[List[ChatMessageResponse]] = Field(default=None, description="会话中的消息列表")
    model_config = ConfigDict(from_attributes=True)

    # messages 期望的是 List[ChatMessageResponse]
    # 但是数据库中存储的是 List[ChatMessage]
    # 所以需要进行转换
    @field_validator("messages", mode="before")
    def convert_messages(cls, v):
        if isinstance(v, list) and all(isinstance(msg, ChatMessage) for msg in v):
            return [ChatMessageResponse.model_validate(msg) for msg in v]
        return v

class ChatListResponse(CustomBaseModel):
    """聊天会话列表响应模型"""
    total: int
    items: List[ChatResponse] 
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    third_party_user_id: int
    kb_id: int
    title: Optional[str] = None

class MarkReadRequest(BaseModel):
    """标记消息已读的请求模型"""
    last_read_message_id: int = Field(..., description="最后一条已读消息的ID")
