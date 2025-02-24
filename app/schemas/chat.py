from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.chat import MessageType

class ChatMessageBase(BaseModel):
    """聊天消息基础模型"""
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(..., description="消息类型")
    doc_metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据，如相关文档引用等")

class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息的请求模型"""
    pass

class ChatMessageUpdate(ChatMessageBase):
    """更新聊天消息的请求模型"""
    content: Optional[str] = Field(None, description="消息内容")
    message_type: Optional[MessageType] = Field(None, description="消息类型")

class ChatMessage(ChatMessageBase):
    """聊天消息响应模型"""
    id: int = Field(..., description="消息ID")
    chat_id: int = Field(..., description="所属会话ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    """聊天会话基础模型"""
    title: Optional[str] = Field(None, description="会话标题，默认为第一条用户消息")
    knowledge_base_id: int = Field(..., description="知识库ID")

class ChatCreate(ChatBase):
    """创建聊天会话的请求模型"""
    third_party_user_id: int = Field(..., description="第三方用户ID")

class ChatUpdate(ChatBase):
    """更新聊天会话的请求模型"""
    title: Optional[str] = Field(None, description="会话标题")
    knowledge_base_id: Optional[int] = Field(None, description="知识库ID")

class Chat(ChatBase):
    """聊天会话响应模型"""
    id: int = Field(..., description="会话ID")
    third_party_user_id: int = Field(..., description="第三方用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: List[ChatMessage] = Field(default_factory=list, description="会话中的消息列表")

    class Config:
        from_attributes = True

class ChatList(BaseModel):
    """聊天会话列表响应模型"""
    total: int = Field(..., description="总会话数")
    items: List[Chat] = Field(..., description="会话列表")

    class Config:
        from_attributes = True 