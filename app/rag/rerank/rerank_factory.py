"""重排序工厂类"""
from typing import Any, Optional, Dict

from app.core.logger import Logger
from app.rag.rerank.rerank_base import BaseRerankRunner
from app.rag.rerank.rerank_model import RerankModelRunner
from app.rag.rerank.weight_rerank import WeightRerankRunner
from app.rag.rerank.rerank_type import RerankMode
from app.rag.rerank.entity.weight import Weights
from app.rag.embedding.cached_embedding import CacheEmbedding


class RerankRunnerFactory:
    """重排序运行器工厂类"""
    
    @staticmethod
    def get_default_weights(model_name: Optional[str] = None, model_provider: Optional[str] = None) -> Weights:
        """
        获取默认权重配置
        
        Args:
            model_name: 模型名称
            model_provider: 模型提供商
            
        Returns:
            默认权重配置
        """
        return Weights(
            vector_setting=VectorSetting(
                vector_weight=0.7,
                model_name=model_name,
                model_provider=model_provider
            ),
            keyword_setting=KeywordSetting(
                keyword_weight=0.3,
                k1=1.5,
                b=0.75
            )
        )
    
    @staticmethod
    def create_rerank_runner(
        rerank_mode: str, 
        user_id: Optional[str] = None,
        model_instance: Optional[Any] = None,
        weights: Optional[Weights] = None,
        embedding_engine: Optional[CacheEmbedding] = None
    ) -> BaseRerankRunner:
        """
        创建重排序运行器
        
        Args:
            rerank_mode: 重排序模式
            user_id: 用户ID
            model_instance: 模型实例（用于模型重排序）
            weights: 权重配置（用于加权重排序）
            embedding_engine: 向量引擎（用于加权重排序）
            
        Returns:
            重排序运行器
        """
        try:
            if rerank_mode == RerankMode.RERANKING_MODEL:
                if not model_instance:
                    raise ValueError("模型重排序需要提供模型实例")
                return RerankModelRunner(model_instance)
            elif rerank_mode == RerankMode.WEIGHTED_SCORE:
                if not user_id:
                    raise ValueError("加权重排序需要提供用户ID")
                if not weights:
                    # 使用默认权重配置
                    model_name = None
                    model_provider = None
                    if embedding_engine:
                        model_name = getattr(embedding_engine, "model_name", None)
                        model_provider = getattr(embedding_engine, "model_provider", None)
                    weights = RerankRunnerFactory.get_default_weights(model_name, model_provider)
                if not embedding_engine:
                    raise ValueError("加权重排序需要提供向量引擎")
                return WeightRerankRunner(user_id, weights, embedding_engine)
            else:
                raise ValueError(f"不支持的重排序模式: {rerank_mode}")
        except Exception as e:
            Logger.error(f"创建重排序运行器失败: {str(e)}")
            raise 