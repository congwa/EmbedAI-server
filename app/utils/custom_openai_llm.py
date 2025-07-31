from fast_graphrag._llm import OpenAILLMService
from fast_graphrag._utils import throttle_async_func_call
from sqlalchemy.orm import Session
from app.services.usage_service import UsageService
from app.core.logger import Logger

class CustomOpenAILLMService(OpenAILLMService):
    """自定义的 OpenAILLMService，重写限速部分并添加用量记录"""

    @throttle_async_func_call(max_concurrent=10, stagger_time=0.01, waiting_time=0.01)
    async def send_message(self, *args, **kwargs):
        """发送消息的方法，使用自定义的限速，并记录用量"""
        
        # 从kwargs中弹出db会话，避免传递给OpenAI API
        db: Session = kwargs.pop("db", None)
        
        # 调用父类的send_message
        response = await super().send_message(*args, **kwargs)
        
        # 记录用量
        if db and hasattr(response, 'usage'):
            try:
                usage_service = UsageService(db)
                await usage_service.record_usage(
                    model_name=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens
                )
            except Exception as e:
                Logger.error(f"在send_message中记录用量失败: {str(e)}")
        
        return response