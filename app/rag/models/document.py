"""文档模型，用于表示处理后的文档"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class Document(BaseModel):
    """文档模型，用于表示处理后的文档"""
    
    page_content: str = Field(..., description="文档内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    vector: Optional[List[float]] = Field(default=None, description="文档向量")
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Document(content={self.page_content[:50]}..., metadata={self.metadata})"