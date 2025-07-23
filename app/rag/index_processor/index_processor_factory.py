"""索引处理器工厂"""
from typing import Optional

from app.core.logger import Logger
from app.models.knowledge_base import KnowledgeBase
from app.rag.index_processor.index_processor_base import BaseIndexProcessor
from app.rag.index_processor.standard_index_processor import StandardIndexProcessor
from app.rag.index_processor.keyword_index_processor import KeywordIndexProcessor

class IndexProcessorFactory:
    """索引处理器工厂
    
    负责创建不同类型的索引处理器实例
    """
    
    @staticmethod
    def create_index_processor(knowledge_base: KnowledgeBase) -> BaseIndexProcessor:
        """创建索引处理器
        
        Args:
            knowledge_base: 知识库对象
            
        Returns:
            BaseIndexProcessor: 索引处理器实例
        """
        try:
            # 根据知识库的索引技术选择处理器
            if knowledge_base.indexing_technique == "economy":
                return KeywordIndexProcessor()
            else:  # high_quality
                return StandardIndexProcessor()
        except Exception as e:
            Logger.error(f"创建索引处理器失败: {str(e)}")
            # 默认使用标准索引处理器
            return StandardIndexProcessor()