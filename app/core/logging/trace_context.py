"""
RAG链路追踪上下文管理模块
"""
import time
from typing import Optional, Dict, Any, List
from contextvars import ContextVar

# 创建上下文变量，用于存储请求跟踪信息
trace_context: ContextVar[Dict[str, Any]] = ContextVar("trace_context", default={})


class RAGTraceContext:
    """RAG链路追踪上下文管理器"""

    def __init__(self, trace_id: str):
        """初始化RAG追踪上下文

        Args:
            trace_id: 追踪ID
        """
        self.trace_id = trace_id
        self.kb_id: Optional[int] = None
        self.user_id: Optional[int] = None
        self.operation_type: Optional[str] = None  # 'training', 'query', 'management'
        self.start_time: float = time.time()
        self.stages: List[Dict[str, Any]] = []  # 记录各个阶段的信息
        self.performance_metrics: Dict[str, Any] = {}

    def set_kb_context(
        self, kb_id: int, user_id: int = None, operation_type: str = None
    ):
        """设置知识库上下文

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            operation_type: 操作类型
        """
        self.kb_id = kb_id
        self.user_id = user_id
        self.operation_type = operation_type

    def add_stage(self, stage_name: str, **kwargs):
        """添加处理阶段

        Args:
            stage_name: 阶段名称
            **kwargs: 阶段相关的额外信息
        """
        current_time = time.time()
        stage_info = {
            "stage": stage_name,
            "timestamp": current_time,
            "duration_from_start": current_time - self.start_time,
            **kwargs,
        }
        self.stages.append(stage_info)

    def update_performance_metrics(self, **metrics):
        """更新性能指标

        Args:
            **metrics: 性能指标键值对
        """
        self.performance_metrics.update(metrics)

    def get_total_duration(self) -> float:
        """获取总耗时

        Returns:
            float: 总耗时(秒)
        """
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 上下文信息字典
        """
        return {
            "trace_id": self.trace_id,
            "kb_id": self.kb_id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "start_time": self.start_time,
            "total_duration": self.get_total_duration(),
            "stages": self.stages,
            "performance_metrics": self.performance_metrics,
        }
