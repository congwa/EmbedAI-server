from pydantic import BaseModel
from typing import Any

class CustomBaseModel(BaseModel):
    """自定义基础模型类
    
    继承自 Pydantic 的 BaseModel，默认使用 json 模式进行序列化
    """
    def model_dump(self, **kwargs) -> dict[str, Any]:
        # 如果没有指定 mode，则默认使用 'json'
        if 'mode' not in kwargs:
            kwargs['mode'] = 'json'
        return super().model_dump(**kwargs)
        
    class Config:
        from_attributes = True  # 允许从 ORM 模型创建 