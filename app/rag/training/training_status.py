"""训练状态枚举"""
from enum import Enum

class TrainingStatus(str, Enum):
    """训练状态枚举"""
    INIT = "init"           # 初始状态
    QUEUED = "queued"       # 排队中
    TRAINING = "training"   # 训练中
    TRAINED = "trained"     # 已训练
    FAILED = "failed"       # 训练失败