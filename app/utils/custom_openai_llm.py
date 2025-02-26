from fast_graphrag._llm import OpenAILLMService
from fast_graphrag._utils import throttle_async_func_call

class CustomOpenAILLMService(OpenAILLMService):
    """自定义的 OpenAILLMService，重写限速部分"""

    @throttle_async_func_call(max_concurrent=10, stagger_time=0.01, waiting_time=0.01)
    async def send_message(self, *args, **kwargs):
        """发送消息的方法，使用自定义的限速"""
        return await super().send_message(*args, **kwargs) 