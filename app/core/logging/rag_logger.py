"""
RAG相关日志记录模块
"""
from typing import Dict, Any, List
from .base_logger import BaseLogger


class RAGLogger(BaseLogger):
    """RAG相关日志记录器"""

    @classmethod
    def rag_operation(cls, operation: str, kb_id: int = None, **kwargs):
        """记录RAG操作日志

        Args:
            operation: 操作类型
            kb_id: 知识库ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        cls.info(
            f"RAG操作: {operation}{kb_info}",
            rag_operation_type=operation,
            kb_id=kb_id,
            **kwargs
        )

    @classmethod
    def rag_api_request(
        cls,
        endpoint: str,
        method: str = "POST",
        kb_id: int = None,
        user_id: int = None,
        params: Dict = None,
        **kwargs,
    ):
        """记录RAG API请求日志

        Args:
            endpoint: API端点
            method: HTTP方法
            kb_id: 知识库ID
            user_id: 用户ID
            params: 请求参数
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        user_info = f" - 用户ID: {user_id}" if user_id else ""
        params_info = f" - 参数: {params}" if params else ""
        
        cls.info(
            f"RAG API请求: {method} {endpoint}{kb_info}{user_info}{params_info}",
            rag_operation_type="api_request",
            api_endpoint=endpoint,
            api_method=method,
            kb_id=kb_id,
            user_id=user_id,
            api_params=params,
            **kwargs
        )

    @classmethod
    def rag_api_response(
        cls,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
        process_time: float = 0.0,
        kb_id: int = None,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG API响应日志

        Args:
            endpoint: API端点
            method: HTTP方法
            status_code: 响应状态码
            process_time: 处理时间(秒)
            kb_id: 知识库ID
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        status_text = "成功" if 200 <= status_code < 300 else "失败"
        level = cls.info if 200 <= status_code < 300 else cls.error
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        result_info = f" - 结果: {result_summary}" if result_summary else ""
        
        level(
            f"RAG API响应: {method} {endpoint} - 状态码: {status_code} - {status_text} - 耗时: {process_time:.3f}秒{kb_info}{result_info}",
            rag_operation_type="api_response",
            api_endpoint=endpoint,
            api_method=method,
            status_code=status_code,
            process_time=process_time,
            kb_id=kb_id,
            result_summary=result_summary,
            **kwargs
        )

    @classmethod
    def rag_api_error(
        cls,
        endpoint: str,
        method: str = "POST",
        error: str = "",
        kb_id: int = None,
        user_id: int = None,
        **kwargs,
    ):
        """记录RAG API错误日志

        Args:
            endpoint: API端点
            method: HTTP方法
            error: 错误信息
            kb_id: 知识库ID
            user_id: 用户ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        user_info = f" - 用户ID: {user_id}" if user_id else ""
        
        cls.error(
            f"RAG API错误: {method} {endpoint} - 错误: {error}{kb_info}{user_info}",
            rag_operation_type="api_error",
            api_endpoint=endpoint,
            api_method=method,
            error_message=error,
            kb_id=kb_id,
            user_id=user_id,
            **kwargs
        )

    @classmethod
    def rag_training_start(
        cls, kb_id: int, document_count: int, config: Dict = None, **kwargs
    ):
        """记录RAG训练开始日志

        Args:
            kb_id: 知识库ID
            document_count: 文档数量
            config: 训练配置
            **kwargs: 额外的日志字段
        """
        config_info = f" - 配置: {config}" if config else ""
        cls.info(
            f"RAG训练开始: 知识库ID {kb_id} - 文档数量: {document_count}{config_info}",
            rag_operation_type="training_start",
            kb_id=kb_id,
            document_count=document_count,
            training_config=config,
            **kwargs
        )

    @classmethod
    def rag_training_complete(
        cls,
        kb_id: int,
        success: bool,
        duration: float,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG训练完成日志

        Args:
            kb_id: 知识库ID
            success: 是否成功
            duration: 训练耗时(秒)
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        result_info = f" - 结果: {result_summary}" if result_summary else ""
        
        level(
            f"RAG训练{status}: 知识库ID {kb_id} - 耗时: {duration:.2f}秒{result_info}",
            rag_operation_type="training_complete",
            kb_id=kb_id,
            training_success=success,
            training_duration=duration,
            result_summary=result_summary,
            **kwargs
        )

    @classmethod
    def rag_document_processing_start(
        cls, kb_id: int, document_count: int, config: Dict = None, **kwargs
    ):
        """记录RAG文档处理开始日志

        Args:
            kb_id: 知识库ID
            document_count: 文档数量
            config: 处理配置
            **kwargs: 额外的日志字段
        """
        config_info = f" - 配置: {config}" if config else ""
        cls.info(
            f"RAG文档处理开始: 知识库ID {kb_id} - 文档数量: {document_count}{config_info}",
            rag_operation_type="document_processing_start",
            kb_id=kb_id,
            document_count=document_count,
            processing_config=config,
            **kwargs
        )

    @classmethod
    def rag_document_start(
        cls,
        kb_id: int,
        document_id: int,
        document_title: str = "",
        progress: Dict = None,
        **kwargs,
    ):
        """记录RAG单个文档处理开始日志

        Args:
            kb_id: 知识库ID
            document_id: 文档ID
            document_title: 文档标题
            progress: 进度信息
            **kwargs: 额外的日志字段
        """
        title_info = f" - 标题: {document_title}" if document_title else ""
        progress_info = f" - 进度: {progress}" if progress else ""
        
        cls.debug(
            f"RAG文档处理开始: 知识库ID {kb_id} - 文档ID {document_id}{title_info}{progress_info}",
            rag_operation_type="document_start",
            kb_id=kb_id,
            document_id=document_id,
            document_title=document_title,
            progress=progress,
            **kwargs
        )

    @classmethod
    def rag_document_error(
        cls,
        kb_id: int,
        document_id: int,
        stage: str,
        error: str,
        progress: Dict = None,
        **kwargs,
    ):
        """记录RAG文档处理错误日志

        Args:
            kb_id: 知识库ID
            document_id: 文档ID
            stage: 处理阶段
            error: 错误信息
            progress: 进度信息
            **kwargs: 额外的日志字段
        """
        progress_info = f" - 进度: {progress}" if progress else ""
        
        cls.error(
            f"RAG文档处理错误: 知识库ID {kb_id} - 文档ID {document_id} - 阶段: {stage} - 错误: {error}{progress_info}",
            rag_operation_type="document_error",
            kb_id=kb_id,
            document_id=document_id,
            processing_stage=stage,
            error_message=error,
            progress=progress,
            **kwargs
        )

    @classmethod
    def rag_extraction_start(
        cls, document_id: int, file_path: str, file_type: str = "", **kwargs
    ):
        """记录RAG文档提取开始日志

        Args:
            document_id: 文档ID
            file_path: 文件路径
            file_type: 文件类型
            **kwargs: 额外的日志字段
        """
        type_info = f" - 类型: {file_type}" if file_type else ""
        cls.debug(
            f"RAG文档提取开始: 文档ID {document_id} - 文件: {file_path}{type_info}",
            rag_operation_type="extraction_start",
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
            **kwargs
        )

    @classmethod
    def rag_extraction_success(
        cls, document_id: int, content_length: int, extraction_time: float, **kwargs
    ):
        """记录RAG文档提取成功日志

        Args:
            document_id: 文档ID
            content_length: 内容长度
            extraction_time: 提取耗时(秒)
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文档提取成功: 文档ID {document_id} - 内容长度: {content_length} - 耗时: {extraction_time:.3f}秒",
            rag_operation_type="extraction_success",
            document_id=document_id,
            content_length=content_length,
            extraction_time=extraction_time,
            **kwargs
        )

    @classmethod
    def rag_chunking_start(
        cls, document_id: int, content_length: int, chunk_size: int, **kwargs
    ):
        """记录RAG文本分块开始日志

        Args:
            document_id: 文档ID
            content_length: 内容长度
            chunk_size: 分块大小
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文本分块开始: 文档ID {document_id} - 内容长度: {content_length} - 分块大小: {chunk_size}",
            rag_operation_type="chunking_start",
            document_id=document_id,
            content_length=content_length,
            chunk_size=chunk_size,
            **kwargs
        )

    @classmethod
    def rag_chunking_success(
        cls, document_id: int, chunk_count: int, chunking_time: float, **kwargs
    ):
        """记录RAG文本分块成功日志

        Args:
            document_id: 文档ID
            chunk_count: 分块数量
            chunking_time: 分块耗时(秒)
            **kwargs: 额外的日志字段
        """
        cls.debug(
            f"RAG文本分块成功: 文档ID {document_id} - 分块数量: {chunk_count} - 耗时: {chunking_time:.3f}秒",
            rag_operation_type="chunking_success",
            document_id=document_id,
            chunk_count=chunk_count,
            chunking_time=chunking_time,
            **kwargs
        )

    @classmethod
    def rag_embedding_start(
        cls,
        document_id: int = None,
        chunk_count: int = 0,
        model: str = "",
        batch_size: int = 0,
        **kwargs,
    ):
        """记录RAG向量化开始日志

        Args:
            document_id: 文档ID
            chunk_count: 分块数量
            model: 向量化模型
            batch_size: 批处理大小
            **kwargs: 额外的日志字段
        """
        doc_info = f" - 文档ID: {document_id}" if document_id else ""
        model_info = f" - 模型: {model}" if model else ""
        batch_info = f" - 批大小: {batch_size}" if batch_size > 0 else ""
        
        cls.debug(
            f"RAG向量化开始: 分块数量: {chunk_count}{doc_info}{model_info}{batch_info}",
            rag_operation_type="embedding_start",
            document_id=document_id,
            chunk_count=chunk_count,
            embedding_model=model,
            batch_size=batch_size,
            **kwargs
        )

    @classmethod
    def rag_embedding_batch(
        cls,
        batch_num: int,
        total_batches: int,
        batch_size: int,
        model: str = "",
        progress: Dict = None,
        **kwargs,
    ):
        """记录RAG向量化批处理日志

        Args:
            batch_num: 当前批次号
            total_batches: 总批次数
            batch_size: 批处理大小
            model: 向量化模型
            progress: 进度信息
            **kwargs: 额外的日志字段
        """
        progress_percent = (batch_num / total_batches * 100) if total_batches > 0 else 0
        model_info = f" - 模型: {model}" if model else ""
        progress_info = f" - 进度详情: {progress}" if progress else ""
        
        cls.debug(
            f"RAG向量化批处理: 批次 {batch_num}/{total_batches} - 批大小: {batch_size} - 进度: {progress_percent:.1f}%{model_info}{progress_info}",
            rag_operation_type="embedding_batch",
            batch_num=batch_num,
            total_batches=total_batches,
            batch_size=batch_size,
            progress_percent=progress_percent,
            embedding_model=model,
            progress=progress,
            **kwargs
        )

    @classmethod
    def rag_embedding_success(
        cls,
        document_id: int = None,
        embedding_count: int = 0,
        embedding_time: float = 0.0,
        model: str = "",
        **kwargs,
    ):
        """记录RAG向量化成功日志

        Args:
            document_id: 文档ID
            embedding_count: 向量数量
            embedding_time: 向量化耗时(秒)
            model: 向量化模型
            **kwargs: 额外的日志字段
        """
        doc_info = f" - 文档ID: {document_id}" if document_id else ""
        model_info = f" - 模型: {model}" if model else ""
        
        cls.debug(
            f"RAG向量化成功: 向量数量: {embedding_count} - 耗时: {embedding_time:.3f}秒{doc_info}{model_info}",
            rag_operation_type="embedding_success",
            document_id=document_id,
            embedding_count=embedding_count,
            embedding_time=embedding_time,
            embedding_model=model,
            **kwargs
        )

    @classmethod
    def rag_query_start(
        cls,
        kb_id: int,
        query: str,
        method: str = "",
        params: Dict = None,
        user_id: int = None,
        **kwargs,
    ):
        """记录RAG查询开始日志

        Args:
            kb_id: 知识库ID
            query: 查询内容
            method: 检索方法
            params: 查询参数
            user_id: 用户ID
            **kwargs: 额外的日志字段
        """
        method_info = f" - 方法: {method}" if method else ""
        user_info = f" - 用户ID: {user_id}" if user_id else ""
        params_info = f" - 参数: {params}" if params else ""
        query_preview = query[:100] + "..." if len(query) > 100 else query
        
        cls.info(
            f"RAG查询开始: 知识库ID {kb_id} - 查询: {query_preview}{method_info}{user_info}{params_info}",
            rag_operation_type="query_start",
            kb_id=kb_id,
            query=query,
            retrieval_method=method,
            query_params=params,
            user_id=user_id,
            **kwargs
        )

    @classmethod
    def rag_query_complete(
        cls,
        kb_id: int,
        query: str,
        success: bool,
        duration: float,
        result_count: int = 0,
        **kwargs,
    ):
        """记录RAG查询完成日志

        Args:
            kb_id: 知识库ID
            query: 查询内容
            success: 是否成功
            duration: 查询耗时(秒)
            result_count: 结果数量
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        query_preview = query[:100] + "..." if len(query) > 100 else query
        
        level(
            f"RAG查询{status}: 知识库ID {kb_id} - 查询: {query_preview} - 耗时: {duration:.3f}秒 - 结果数量: {result_count}",
            rag_operation_type="query_complete",
            kb_id=kb_id,
            query=query,
            query_success=success,
            query_duration=duration,
            result_count=result_count,
            **kwargs
        )

    @classmethod
    def rag_retrieval_result(
        cls,
        kb_id: int,
        query: str,
        result_count: int,
        scores: List[float] = None,
        method: str = "",
        **kwargs,
    ):
        """记录RAG检索结果日志

        Args:
            kb_id: 知识库ID
            query: 查询内容
            result_count: 结果数量
            scores: 相关性分数列表
            method: 检索方法
            **kwargs: 额外的日志字段
        """
        method_info = f" - 方法: {method}" if method else ""
        scores_info = ""
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            scores_info = f" - 平均分数: {avg_score:.3f} - 最高分数: {max_score:.3f}"
        
        query_preview = query[:100] + "..." if len(query) > 100 else query
        
        cls.debug(
            f"RAG检索结果: 知识库ID {kb_id} - 查询: {query_preview} - 结果数量: {result_count}{method_info}{scores_info}",
            rag_operation_type="retrieval_result",
            kb_id=kb_id,
            query=query,
            result_count=result_count,
            retrieval_scores=scores,
            retrieval_method=method,
            **kwargs
        )

    @classmethod
    def rag_permission_check(
        cls,
        kb_id: int,
        user_id: int,
        required_permission: str,
        granted: bool = True,
        **kwargs,
    ):
        """记录RAG权限检查日志

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            required_permission: 所需权限
            granted: 是否授权
            **kwargs: 额外的日志字段
        """
        status = "通过" if granted else "拒绝"
        level = cls.debug if granted else cls.warning
        
        level(
            f"RAG权限检查: 知识库ID {kb_id} - 用户ID {user_id} - 权限: {required_permission} - 结果: {status}",
            rag_operation_type="permission_check",
            kb_id=kb_id,
            user_id=user_id,
            required_permission=required_permission,
            permission_granted=granted,
            **kwargs
        )

    @classmethod
    def rag_service_start(
        cls, service: str, method: str, kb_id: int = None, user_id: int = None, **kwargs
    ):
        """记录RAG服务调用开始日志

        Args:
            service: 服务名称
            method: 方法名称
            kb_id: 知识库ID
            user_id: 用户ID
            **kwargs: 额外的日志字段
        """
        kb_info = f" - 知识库ID: {kb_id}" if kb_id else ""
        user_info = f" - 用户ID: {user_id}" if user_id else ""
        
        cls.debug(
            f"RAG服务调用开始: {service}.{method}{kb_info}{user_info}",
            rag_operation_type="service_start",
            service_name=service,
            service_method=method,
            kb_id=kb_id,
            user_id=user_id,
            **kwargs
        )

    @classmethod
    def rag_service_success(
        cls,
        service: str,
        method: str,
        duration: float = 0.0,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG服务调用成功日志

        Args:
            service: 服务名称
            method: 方法名称
            duration: 执行耗时(秒)
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        result_info = f" - 结果: {result_summary}" if result_summary else ""
        
        cls.debug(
            f"RAG服务调用成功: {service}.{method} - 耗时: {duration:.3f}秒{result_info}",
            rag_operation_type="service_success",
            service_name=service,
            service_method=method,
            service_duration=duration,
            result_summary=result_summary,
            **kwargs
        )

    @classmethod
    def rag_service_error(
        cls, service: str, method: str, error: str, duration: float = 0.0, **kwargs
    ):
        """记录RAG服务调用错误日志

        Args:
            service: 服务名称
            method: 方法名称
            error: 错误信息
            duration: 执行耗时(秒)
            **kwargs: 额外的日志字段
        """
        cls.error(
            f"RAG服务调用错误: {service}.{method} - 错误: {error} - 耗时: {duration:.3f}秒",
            rag_operation_type="service_error",
            service_name=service,
            service_method=method,
            error_message=error,
            service_duration=duration,
            **kwargs
        )

    @classmethod
    def rag_document_processing_complete(
        cls,
        kb_id: int,
        success: bool,
        duration: float,
        processed_count: int = 0,
        failed_count: int = 0,
        result_summary: Dict = None,
        **kwargs,
    ):
        """记录RAG文档处理完成日志

        Args:
            kb_id: 知识库ID
            success: 是否成功
            duration: 处理耗时(秒)
            processed_count: 成功处理的文档数量
            failed_count: 处理失败的文档数量
            result_summary: 结果摘要
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        result_info = f" - 结果: {result_summary}" if result_summary else ""
        
        level(
            f"RAG文档处理{status}: 知识库ID {kb_id} - 耗时: {duration:.2f}秒 - 成功: {processed_count} - 失败: {failed_count}{result_info}",
            rag_operation_type="document_processing_complete",
            kb_id=kb_id,
            processing_success=success,
            processing_duration=duration,
            processed_count=processed_count,
            failed_count=failed_count,
            result_summary=result_summary,
            **kwargs
        )

    @classmethod
    def rag_document_complete(
        cls,
        kb_id: int,
        document_id: int,
        success: bool,
        duration: float,
        stages_completed: List[str] = None,
        error: str = "",
        **kwargs,
    ):
        """记录RAG单个文档处理完成日志

        Args:
            kb_id: 知识库ID
            document_id: 文档ID
            success: 是否成功
            duration: 处理耗时(秒)
            stages_completed: 完成的处理阶段列表
            error: 错误信息（如果失败）
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.debug if success else cls.error
        stages_info = f" - 完成阶段: {stages_completed}" if stages_completed else ""
        error_info = f" - 错误: {error}" if error else ""
        
        level(
            f"RAG文档处理{status}: 知识库ID {kb_id} - 文档ID {document_id} - 耗时: {duration:.3f}秒{stages_info}{error_info}",
            rag_operation_type="document_complete",
            kb_id=kb_id,
            document_id=document_id,
            document_success=success,
            document_duration=duration,
            stages_completed=stages_completed,
            error_message=error,
            **kwargs
        )

    @classmethod
    def rag_index_build_start(
        cls,
        kb_id: int,
        index_type: str,
        document_count: int = 0,
        config: Dict = None,
        **kwargs,
    ):
        """记录RAG索引构建开始日志

        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            document_count: 文档数量
            config: 索引配置
            **kwargs: 额外的日志字段
        """
        config_info = f" - 配置: {config}" if config else ""
        
        cls.info(
            f"RAG索引构建开始: 知识库ID {kb_id} - 索引类型: {index_type} - 文档数量: {document_count}{config_info}",
            rag_operation_type="index_build_start",
            kb_id=kb_id,
            index_type=index_type,
            document_count=document_count,
            index_config=config,
            **kwargs
        )

    @classmethod
    def rag_index_build_complete(
        cls,
        kb_id: int,
        index_type: str,
        success: bool,
        duration: float,
        index_size: int = 0,
        **kwargs,
    ):
        """记录RAG索引构建完成日志

        Args:
            kb_id: 知识库ID
            index_type: 索引类型
            success: 是否成功
            duration: 构建耗时(秒)
            index_size: 索引大小
            **kwargs: 额外的日志字段
        """
        status = "成功" if success else "失败"
        level = cls.info if success else cls.error
        size_info = f" - 索引大小: {index_size}" if index_size > 0 else ""
        
        level(
            f"RAG索引构建{status}: 知识库ID {kb_id} - 索引类型: {index_type} - 耗时: {duration:.2f}秒{size_info}",
            rag_operation_type="index_build_complete",
            kb_id=kb_id,
            index_type=index_type,
            build_success=success,
            build_duration=duration,
            index_size=index_size,
            **kwargs
        )
