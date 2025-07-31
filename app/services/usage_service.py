from sqlalchemy.orm import Session
from app.models.llm_usage_log import LLMUsageLog
from app.utils.cost_calculator import cost_calculator
from app.core.context import get_context
from app.core.logger import Logger

class UsageService:
    """用量记录服务
    
    负责记录LLM的使用情况和费用
    """
    
    def __init__(self, db: Session):
        self.db = db

    async def record_usage(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """记录一次LLM调用
        
        Args:
            model_name: 使用的模型名称
            prompt_tokens: 输入Token数
            completion_tokens: 输出Token数
        """
        try:
            # 从上下文中获取user_id和kb_id
            context = get_context()
            user_id = context.get("user_id")
            kb_id = context.get("kb_id")
            
            # 计算总Token和费用
            total_tokens = prompt_tokens + completion_tokens
            cost = cost_calculator.calculate_cost(
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # 创建日志条目
            usage_log = LLMUsageLog(
                user_id=user_id,
                knowledge_base_id=kb_id,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost
            )
            
            self.db.add(usage_log)
            await self.db.commit()
            
            Logger.info(f"成功记录用量: user_id={user_id}, kb_id={kb_id}, model='{model_name}', cost=${cost:.6f}")
            
        except Exception as e:
            Logger.error(f"记录用量失败: {str(e)}")
            await self.db.rollback()
            # 即使记录失败，也不应该中断主流程，所以只记录错误