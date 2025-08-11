from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.chat import Chat
from app.models.knowledge_base import KnowledgeBase
from app.services.knowledge_base import KnowledgeBaseService
from app.services.chat import ChatService
from app.core.logger import Logger
from app.schemas.identity import UserContext, UserType

class ChatAIService:
    """AI 聊天服务
    
    处理与知识库的 AI 对话功能，包括：
    1. 上下文管理
    2. 知识库查询
    3. 响应生成
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.kb_service = KnowledgeBaseService(db)
        self.chat_service = ChatService(db)
        
    async def _get_chat_context(self, chat_id: int, context_window: int = 5) -> str:
        """获取聊天上下文
        
        Args:
            chat_id: 聊天ID
            context_window: 上下文窗口大小，默认获取最近5条消息
            
        Returns:
            str: 格式化的上下文字符串
        """
        chat = await self.db.execute(
            select(Chat).filter(Chat.id == chat_id)
        )
        chat = chat.scalar_one_or_none()
        
        if not chat or not chat.messages:
            return ""
            
        # 获取最近的消息
        recent_messages = sorted(chat.messages[-context_window:], key=lambda x: x.created_at)
        
        # 构建上下文字符串
        context = []
        for msg in recent_messages:
            role = "用户" if msg.message_type == "user" else "AI"
            context.append(f"{role}: {msg.content}")
            
        return "\n".join(context)
        
    async def _format_query(
        self,
        user_query: str,
        chat_id: int
    ) -> str:
        """格式化用户查询
        
        添加上下文信息,优化查询效果
        """
        # 获取最近的聊天记录作为上下文
        chat_context = await self.chat_service.get_chat_context(chat_id)
        
        # TODO: 根据聊天上下文优化查询
        return user_query
        
    async def generate_response(
        self,
        chat_id: int,
        user_query: str,
        kb_id: int,
        user_context: Optional[UserContext] = None,
        top_k: int = 5,
        search_method: str = "hybrid_search",
        use_rerank: bool = True,
        rerank_mode: str = "weighted_score"
    ) -> Dict[str, Any]:
        """生成AI回复
        
        Args:
            chat_id: 聊天会话ID
            user_query: 用户查询内容
            kb_id: 知识库ID
            user_context: 用户上下文信息
            top_k: 返回结果数量
            search_method: 搜索方法 (semantic_search, keyword_search, hybrid_search)
            use_rerank: 是否使用重排序
            rerank_mode: 重排序模式
            
        Returns:
            Dict[str, Any]: 包含回复内容和元数据的字典
        """
        try:
            # user_context 一定存在，且是三方用户
            
            # 格式化查询
            formatted_query = await self._format_query(user_query, chat_id)
            
            # 查询知识库
            query_result = await self.kb_service.query(
                kb_id=kb_id,
                user_context=user_context,
                query=formatted_query,
                top_k=top_k,
                method=search_method,
                use_rerank=use_rerank,
                rerank_mode=rerank_mode,
                skip_permission_check=True  # 系统查询跳过权限检查
            )
            
            # 生成回复
            response_content = await self._generate_response_content(
                query_result["results"],
                user_query
            )
            
            # 构建元数据
            metadata = {
                "kb_id": kb_id,
                "query": formatted_query,
                "top_k": top_k,
                "search_method": search_method,
                "use_rerank": use_rerank,
                "rerank_mode": rerank_mode,
                "results": query_result["results"],
                "generated_at": datetime.now()
            }
            
            return {
                "content": response_content,
                "metadata": metadata
            }
            
        except Exception as e:
            Logger.error(f"Failed to generate AI response: {str(e)}")
            raise
            
    async def _generate_response_content(
        self,
        search_results: list,
        user_query: str
    ) -> str:
        """根据搜索结果生成回复内容"""
        # TODO: 使用更智能的方式生成回复
        if not search_results:
            return "抱歉,我没有找到相关的信息。"
            
        # 简单示例:直接返回最相关的结果
        return search_results[0]["content"] 