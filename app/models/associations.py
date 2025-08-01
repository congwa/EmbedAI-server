from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Table
from datetime import datetime
from .database import Base
from .enums import PermissionType

# 消息已读状态关联表
message_read_status = Table(
    "message_read_status",
    Base.metadata,
    Column("message_id", Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True, comment='消息ID'),
    Column("identity_id", Integer, ForeignKey("user_identities.id", ondelete="CASCADE"), primary_key=True, comment='已读用户身份ID'),
    Column("read_at", DateTime, default=datetime.now, comment='已读时间'),
    comment='消息已读状态关联表，用于跟踪哪个用户身份读取了哪条消息'
)

# 知识库用户权限关联表
knowledge_base_users = Table(
    "knowledge_base_users",
    Base.metadata,
    Column("knowledge_base_id", Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), primary_key=True, comment='知识库ID'),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment='用户ID'),
    Column("permission", Enum(PermissionType), nullable=False, comment='用户对知识库的权限级别'),
    Column("created_at", DateTime, nullable=False, default=datetime.now, comment='权限创建时间'),
    comment='知识库用户权限关联表，用于管理用户对知识库的访问权限'
) 