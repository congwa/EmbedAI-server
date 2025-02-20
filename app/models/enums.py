from enum import Enum

class PermissionType(str, Enum):
    """权限类型枚举
    
    定义用户对知识库的权限级别
    - VIEWER: 只读权限，可以查看和搜索
    - EDITOR: 编辑权限，可以添加和修改文档
    - ADMIN: 管理权限，可以管理成员和设置
    - OWNER: 所有者权限，完全控制权限
    """
    VIEWER = "viewer"  # 查看者权限
    EDITOR = "editor"  # 编辑者权限
    ADMIN = "admin"    # 管理员权限
    OWNER = "owner"    # 所有者权限

    @classmethod
    def get_permission_level(cls, permission_type: 'PermissionType') -> int:
        """获取权限级别值
        
        Args:
            permission_type: 权限类型
            
        Returns:
            int: 权限级别值，数值越大权限越高
        """
        permission_levels = {
            cls.VIEWER: 0,
            cls.EDITOR: 1,
            cls.ADMIN: 2,
            cls.OWNER: 3
        }
        return permission_levels.get(permission_type, -1)

    @classmethod
    def check_permission_level(cls, current: 'PermissionType', required: 'PermissionType') -> bool:
        """检查权限等级是否满足要求"""
        return cls.get_permission_level(current) >= cls.get_permission_level(required)

    @classmethod
    def get_allowed_operations(cls, permission: 'PermissionType') -> set:
        """获取权限允许的操作"""
        viewer_ops = {'view_kb', 'query_kb', 'view_members'}
        editor_ops = {*viewer_ops, 'add_document', 'edit_document', 'delete_document', 'train_kb'}
        admin_ops = {*editor_ops, 'add_member', 'update_member', 'remove_member', 'update_kb'}
        owner_ops = {*admin_ops, 'delete_kb', 'transfer_ownership'}
        
        permission_ops = {
            cls.VIEWER: viewer_ops,
            cls.EDITOR: editor_ops,
            cls.ADMIN: admin_ops,
            cls.OWNER: owner_ops
        }
        return permission_ops[permission]

    @classmethod
    def can_perform_operation(cls, permission: 'PermissionType', operation: str) -> bool:
        """检查权限是否可以执行特定操作"""
        return operation in cls.get_allowed_operations(permission)

class TrainingStatus(str, Enum):
    """训练状态枚举
    
    定义知识库的训练状态
    - INIT: 初始状态，未开始训练
    - QUEUED: 已加入训练队列
    - TRAINING: 训练中
    - TRAINED: 训练完成
    - FAILED: 训练失败
    """
    INIT = "init"        # 初始状态
    QUEUED = "queued"    # 排队中
    TRAINING = "training"  # 训练中
    TRAINED = "trained"    # 训练完成
    FAILED = "failed"      # 训练失败

class ChatMode(str, Enum):
    """聊天模式枚举
    
    定义聊天会话的模式
    - AI: AI模式，使用知识库回答
    - HUMAN: 人工模式，管理员回答
    """
    AI = "ai"          # AI模式，使用知识库回答
    HUMAN = "human"    # 人工模式，管理员回答

class MessageType(str, Enum):
    """消息类型枚举
    
    定义聊天消息的类型
    - USER: 用户发送的消息
    - ASSISTANT: AI助手的回复
    - ADMIN: 管理员的回复
    - SYSTEM: 系统消息
    """
    USER = "user"          # 用户消息
    ASSISTANT = "assistant"  # AI助手消息
    ADMIN = "admin"        # 管理员消息
    SYSTEM = "system"      # 系统消息（如模式切换提示等） 