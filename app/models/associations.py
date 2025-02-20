from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Table
from datetime import datetime
from .database import Base
from .enums import PermissionType

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