from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime
import json

from app.core.config import settings, validate_prompt_config, validate_rag_config
from app.core.logger import Logger


class ConfigManager:
    """配置管理服务
    
    处理系统配置的读取、更新和验证
    支持配置热更新和配置历史记录
    """
    
    def __init__(self, db: AsyncSession):
        """初始化配置管理器
        
        Args:
            db (AsyncSession): 数据库会话对象
        """
        self.db = db
        self._config_cache = {}
        self._last_update = {}
    
    async def get_prompt_config(self) -> Dict[str, Any]:
        """获取提示词管理配置
        
        Returns:
            Dict[str, Any]: 提示词配置
        """
        try:
            Logger.info("获取提示词管理配置")
            
            config = settings.PROMPT_CONFIG
            
            # 添加运行时信息
            config.update({
                "last_updated": self._last_update.get("prompt", None),
                "cache_status": "active" if "prompt" in self._config_cache else "empty"
            })
            
            return config
            
        except Exception as e:
            Logger.error(f"获取提示词配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置失败: {str(e)}"
            )
    
    async def get_rag_config(self) -> Dict[str, Any]:
        """获取RAG配置
        
        Returns:
            Dict[str, Any]: RAG配置
        """
        try:
            Logger.info("获取RAG配置")
            
            config = settings.RAG_CONFIG
            
            # 添加运行时信息
            config.update({
                "last_updated": self._last_update.get("rag", None),
                "cache_status": "active" if "rag" in self._config_cache else "empty"
            })
            
            return config
            
        except Exception as e:
            Logger.error(f"获取RAG配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置失败: {str(e)}"
            )
    
    async def update_prompt_config(
        self, 
        config_updates: Dict[str, Any], 
        user_id: int
    ) -> Dict[str, Any]:
        """更新提示词管理配置
        
        Args:
            config_updates: 配置更新数据
            user_id: 操作用户ID
            
        Returns:
            Dict[str, Any]: 更新后的配置
        """
        try:
            Logger.info(f"用户 {user_id} 更新提示词管理配置")
            
            # 获取当前配置
            current_config = settings.PROMPT_CONFIG.copy()
            
            # 应用更新
            for key, value in config_updates.items():
                if key in current_config:
                    current_config[key] = value
                else:
                    Logger.warning(f"忽略未知的配置项: {key}")
            
            # 验证更新后的配置
            validated_config = self._validate_prompt_config_update(current_config)
            
            # 更新缓存
            self._config_cache["prompt"] = validated_config
            self._last_update["prompt"] = datetime.now().isoformat()
            
            # 记录配置变更
            await self._log_config_change(
                config_type="prompt",
                old_config=settings.PROMPT_CONFIG,
                new_config=validated_config,
                user_id=user_id
            )
            
            Logger.info("提示词配置更新成功")
            return validated_config
            
        except Exception as e:
            Logger.error(f"更新提示词配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新配置失败: {str(e)}"
            )
    
    async def reset_prompt_config(self, user_id: int) -> Dict[str, Any]:
        """重置提示词配置为默认值
        
        Args:
            user_id: 操作用户ID
            
        Returns:
            Dict[str, Any]: 重置后的配置
        """
        try:
            Logger.info(f"用户 {user_id} 重置提示词配置")
            
            # 获取默认配置
            default_config = validate_prompt_config(settings)
            
            # 清除缓存
            if "prompt" in self._config_cache:
                del self._config_cache["prompt"]
            
            self._last_update["prompt"] = datetime.now().isoformat()
            
            # 记录配置重置
            await self._log_config_change(
                config_type="prompt",
                old_config=settings.PROMPT_CONFIG,
                new_config=default_config,
                user_id=user_id,
                action="reset"
            )
            
            Logger.info("提示词配置重置成功")
            return default_config
            
        except Exception as e:
            Logger.error(f"重置提示词配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"重置配置失败: {str(e)}"
            )
    
    async def update_rag_config(
        self, 
        config_updates: Dict[str, Any], 
        user_id: int
    ) -> Dict[str, Any]:
        """更新RAG配置
        
        Args:
            config_updates: 配置更新数据
            user_id: 操作用户ID
            
        Returns:
            Dict[str, Any]: 更新后的配置
        """
        try:
            Logger.info(f"用户 {user_id} 更新RAG配置")
            
            # 获取当前配置
            current_config = settings.RAG_CONFIG.copy()
            
            # 应用更新
            for key, value in config_updates.items():
                if key in current_config:
                    current_config[key] = value
                else:
                    Logger.warning(f"忽略未知的配置项: {key}")
            
            # 验证更新后的配置
            validated_config = self._validate_rag_config_update(current_config)
            
            # 更新缓存
            self._config_cache["rag"] = validated_config
            self._last_update["rag"] = datetime.now().isoformat()
            
            # 记录配置变更
            await self._log_config_change(
                config_type="rag",
                old_config=settings.RAG_CONFIG,
                new_config=validated_config,
                user_id=user_id
            )
            
            Logger.info("RAG配置更新成功")
            return validated_config
            
        except Exception as e:
            Logger.error(f"更新RAG配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新配置失败: {str(e)}"
            )
    
    async def reset_rag_config(self, user_id: int) -> Dict[str, Any]:
        """重置RAG配置为默认值
        
        Args:
            user_id: 操作用户ID
            
        Returns:
            Dict[str, Any]: 重置后的配置
        """
        try:
            Logger.info(f"用户 {user_id} 重置RAG配置")
            
            # 获取默认配置
            default_config = validate_rag_config(settings)
            
            # 清除缓存
            if "rag" in self._config_cache:
                del self._config_cache["rag"]
            
            self._last_update["rag"] = datetime.now().isoformat()
            
            # 记录配置重置
            await self._log_config_change(
                config_type="rag",
                old_config=settings.RAG_CONFIG,
                new_config=default_config,
                user_id=user_id,
                action="reset"
            )
            
            Logger.info("RAG配置重置成功")
            return default_config
            
        except Exception as e:
            Logger.error(f"重置RAG配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"重置配置失败: {str(e)}"
            )
    
    async def get_config_history(
        self, 
        config_type: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取配置变更历史
        
        Args:
            config_type: 配置类型 (prompt, rag)
            limit: 返回记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 配置变更历史
        """
        try:
            Logger.info(f"获取 {config_type} 配置变更历史")
            
            # 这里可以从数据库或日志文件中获取历史记录
            # 目前返回模拟数据
            history = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": 1,
                    "action": "update",
                    "changes": {"max_length": 50000},
                    "version": "1.0.0"
                }
            ]
            
            return history[:limit]
            
        except Exception as e:
            Logger.error(f"获取配置历史失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置历史失败: {str(e)}"
            )
    
    async def validate_config(
        self, 
        config_type: str, 
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证配置数据
        
        Args:
            config_type: 配置类型
            config_data: 配置数据
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            Logger.info(f"验证 {config_type} 配置")
            
            if config_type == "prompt":
                validated = self._validate_prompt_config_update(config_data)
                return {
                    "valid": True,
                    "validated_config": validated,
                    "errors": [],
                    "warnings": []
                }
            elif config_type == "rag":
                validated = self._validate_rag_config_update(config_data)
                return {
                    "valid": True,
                    "validated_config": validated,
                    "errors": [],
                    "warnings": []
                }
            else:
                return {
                    "valid": False,
                    "errors": [f"不支持的配置类型: {config_type}"],
                    "warnings": []
                }
                
        except Exception as e:
            Logger.error(f"配置验证失败: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    def _validate_prompt_config_update(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证提示词配置更新
        
        Args:
            config: 配置数据
            
        Returns:
            Dict[str, Any]: 验证后的配置
        """
        validated = {}
        
        # 验证各个配置项
        if "max_length" in config:
            max_length = config["max_length"]
            if not isinstance(max_length, int) or max_length < 100 or max_length > 100000:
                raise ValueError("max_length 必须是100-100000之间的整数")
            validated["max_length"] = max_length
        
        if "max_variables" in config:
            max_variables = config["max_variables"]
            if not isinstance(max_variables, int) or max_variables < 1 or max_variables > 100:
                raise ValueError("max_variables 必须是1-100之间的整数")
            validated["max_variables"] = max_variables
        
        if "version_limit" in config:
            version_limit = config["version_limit"]
            if not isinstance(version_limit, int) or version_limit < 10 or version_limit > 1000:
                raise ValueError("version_limit 必须是10-1000之间的整数")
            validated["version_limit"] = version_limit
        
        if "cache_ttl" in config:
            cache_ttl = config["cache_ttl"]
            if not isinstance(cache_ttl, int) or cache_ttl < 60 or cache_ttl > 86400:
                raise ValueError("cache_ttl 必须是60-86400之间的整数")
            validated["cache_ttl"] = cache_ttl
        
        if "retention_days" in config:
            retention_days = config["retention_days"]
            if not isinstance(retention_days, int) or retention_days < 7 or retention_days > 365:
                raise ValueError("retention_days 必须是7-365之间的整数")
            validated["retention_days"] = retention_days
        
        if "enable_analytics" in config:
            enable_analytics = config["enable_analytics"]
            if not isinstance(enable_analytics, bool):
                raise ValueError("enable_analytics 必须是布尔值")
            validated["enable_analytics"] = enable_analytics
        
        if "enable_auto_optimization" in config:
            enable_auto_optimization = config["enable_auto_optimization"]
            if not isinstance(enable_auto_optimization, bool):
                raise ValueError("enable_auto_optimization 必须是布尔值")
            validated["enable_auto_optimization"] = enable_auto_optimization
        
        return validated
    
    def _validate_rag_config_update(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证RAG配置更新
        
        Args:
            config: 配置数据
            
        Returns:
            Dict[str, Any]: 验证后的配置
        """
        validated = {}
        
        # 验证分块大小
        if "chunk_size" in config:
            chunk_size = config["chunk_size"]
            if not isinstance(chunk_size, int) or chunk_size < 100 or chunk_size > 10000:
                raise ValueError("chunk_size 必须是100-10000之间的整数")
            validated["chunk_size"] = chunk_size
        
        # 验证分块重叠大小
        if "chunk_overlap" in config:
            chunk_overlap = config["chunk_overlap"]
            if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
                raise ValueError("chunk_overlap 必须是非负整数")
            # 如果有chunk_size，检查重叠不能超过一半
            chunk_size = config.get("chunk_size", validated.get("chunk_size", 1000))
            if chunk_overlap > chunk_size // 2:
                raise ValueError("chunk_overlap 不能超过chunk_size的一半")
            validated["chunk_overlap"] = chunk_overlap
        
        # 验证向量存储类型
        if "vector_store_type" in config:
            vector_store_type = config["vector_store_type"]
            supported_types = ["chroma", "qdrant", "milvus", "pgvector"]
            if vector_store_type not in supported_types:
                raise ValueError(f"vector_store_type 必须是以下之一: {', '.join(supported_types)}")
            validated["vector_store_type"] = vector_store_type
        
        # 验证批处理大小
        if "batch_size" in config:
            batch_size = config["batch_size"]
            if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 1000:
                raise ValueError("batch_size 必须是1-1000之间的整数")
            validated["batch_size"] = batch_size
        
        # 验证重排序模型
        if "rerank_model" in config:
            rerank_model = config["rerank_model"]
            if not isinstance(rerank_model, str) or not rerank_model.strip():
                raise ValueError("rerank_model 必须是非空字符串")
            validated["rerank_model"] = rerank_model.strip()
        
        # 验证检索方法
        if "retrieval_method" in config:
            retrieval_method = config["retrieval_method"]
            supported_methods = ["semantic_search", "keyword_search", "hybrid_search"]
            if retrieval_method not in supported_methods:
                raise ValueError(f"retrieval_method 必须是以下之一: {', '.join(supported_methods)}")
            validated["retrieval_method"] = retrieval_method
        
        # 验证是否使用重排序
        if "use_rerank" in config:
            use_rerank = config["use_rerank"]
            if not isinstance(use_rerank, bool):
                raise ValueError("use_rerank 必须是布尔值")
            validated["use_rerank"] = use_rerank
        
        return validated
    
    async def _log_config_change(
        self,
        config_type: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        user_id: int,
        action: str = "update"
    ) -> None:
        """记录配置变更日志
        
        Args:
            config_type: 配置类型
            old_config: 旧配置
            new_config: 新配置
            user_id: 操作用户ID
            action: 操作类型
        """
        try:
            # 计算配置差异
            changes = {}
            for key, new_value in new_config.items():
                old_value = old_config.get(key)
                if old_value != new_value:
                    changes[key] = {
                        "old": old_value,
                        "new": new_value
                    }
            
            # 记录日志
            Logger.info(
                f"配置变更记录: type={config_type}, action={action}, "
                f"user_id={user_id}, changes={json.dumps(changes, ensure_ascii=False)}"
            )
            
            # 这里可以将变更记录保存到数据库
            # 目前只记录到日志
            
        except Exception as e:
            Logger.error(f"记录配置变更失败: {str(e)}")
            # 不抛出异常，避免影响主流程