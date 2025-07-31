from app.core.config import settings
from app.core.logger import Logger

class CostCalculator:
    """费用计算器
    
    根据模型和Token使用量计算费用
    """
    
    def __init__(self):
        self.pricing = settings.MODEL_PRICING

    def calculate_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """计算费用
        
        Args:
            model_name: 模型名称
            prompt_tokens: 输入Token数
            completion_tokens: 输出Token数
            
        Returns:
            float: 计算出的费用
        """
        if model_name not in self.pricing:
            Logger.warning(f"模型 '{model_name}' 的定价信息未找到，费用将记为0。")
            return 0.0
            
        model_pricing = self.pricing[model_name]
        prompt_cost = (prompt_tokens / 1000) * model_pricing.get("prompt", 0)
        completion_cost = (completion_tokens / 1000) * model_pricing.get("completion", 0)
        
        total_cost = prompt_cost + completion_cost
        
        Logger.info(f"费用计算: 模型='{model_name}', 输入Tokens={prompt_tokens}, 输出Tokens={completion_tokens}, 总费用=${total_cost:.6f}")
        
        return total_cost

# 创建一个单例
cost_calculator = CostCalculator()