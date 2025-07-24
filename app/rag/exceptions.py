"""RAG异常类"""
from typing import Optional, Dict, Any


class RAGException(Exception):
    """RAG异常基类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化异常
        
        Args:
            message: 错误信息
            details: 详细信息
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DocumentProcessingException(RAGException):
    """文档处理异常"""
    
    def __init__(
        self,
        message: str,
        document_id: Optional[int] = None,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            document_id: 文档ID
            file_path: 文件路径
            details: 详细信息
        """
        self.document_id = document_id
        self.file_path = file_path
        super().__init__(message, details)


class EmbeddingException(RAGException):
    """向量化异常"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        text_length: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            model_name: 模型名称
            text_length: 文本长度
            details: 详细信息
        """
        self.model_name = model_name
        self.text_length = text_length
        super().__init__(message, details)


class IndexingException(RAGException):
    """索引异常"""
    
    def __init__(
        self,
        message: str,
        knowledge_base_id: Optional[int] = None,
        index_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            knowledge_base_id: 知识库ID
            index_type: 索引类型
            details: 详细信息
        """
        self.knowledge_base_id = knowledge_base_id
        self.index_type = index_type
        super().__init__(message, details)


class RetrievalException(RAGException):
    """检索异常"""
    
    def __init__(
        self,
        message: str,
        knowledge_base_id: Optional[int] = None,
        method: Optional[str] = None,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            knowledge_base_id: 知识库ID
            method: 检索方法
            query: 查询文本
            details: 详细信息
        """
        self.knowledge_base_id = knowledge_base_id
        self.method = method
        self.query = query
        super().__init__(message, details)


class RerankException(RAGException):
    """重排序异常"""
    
    def __init__(
        self,
        message: str,
        rerank_mode: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            rerank_mode: 重排序模式
            details: 详细信息
        """
        self.rerank_mode = rerank_mode
        super().__init__(message, details)


class TrainingException(RAGException):
    """训练异常"""
    
    def __init__(
        self,
        message: str,
        knowledge_base_id: Optional[int] = None,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            knowledge_base_id: 知识库ID
            stage: 训练阶段
            details: 详细信息
        """
        self.knowledge_base_id = knowledge_base_id
        self.stage = stage
        super().__init__(message, details)


class ConfigurationException(RAGException):
    """配置异常"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            config_key: 配置键
            details: 详细信息
        """
        self.config_key = config_key
        super().__init__(message, details)