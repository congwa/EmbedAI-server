from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class LLMUsageLog(Base):
    """LLM 使用日志模型
    
    用于记录每次与大语言模型交互的Token使用量和相关费用
    """
    __tablename__ = "llm_usage_logs"
    __table_args__ = {'comment': 'LLM使用日志表，记录Token使用和费用'}

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='关联的用户ID')
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True, comment='关联的知识库ID')
    
    # 模型和Token信息
    model_name = Column(String, nullable=False, comment='使用的LLM模型名称')
    prompt_tokens = Column(Integer, nullable=False, comment='输入的Token数')
    completion_tokens = Column(Integer, nullable=False, comment='输出的Token数')
    total_tokens = Column(Integer, nullable=False, comment='总Token数')
    
    # 费用信息
    cost = Column(Float, nullable=False, comment='本次调用的费用')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='记录创建时间')

    # 关系定义
    user = relationship("User", backref="llm_usage_logs")
    knowledge_base = relationship("KnowledgeBase", backref="llm_usage_logs")

    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, user_id={self.user_id}, kb_id={self.knowledge_base_id}, cost={self.cost})>"