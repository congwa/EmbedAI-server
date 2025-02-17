from enum import Enum

class PermissionType(Enum):
    """权限类型"""
    OWNER = "owner"      # 所有者权限 完全控制权限
    ADMIN = "admin"      # 管理员权限 管理权限，可以管理其他用户的访问权限
    EDITOR = "editor"    # 编辑权限 编辑权限，可以添加/修改文档
    VIEWER = "viewer"    # 查看权限  查看权限，只能查看和使用

    @classmethod
    def get_permission_level(cls, permission: 'PermissionType') -> int:
        """获取权限等级"""
        permission_levels = {
            cls.VIEWER: 0,
            cls.EDITOR: 1,
            cls.ADMIN: 2,
            cls.OWNER: 3
        }
        return permission_levels[permission]

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

class TrainingStatus(Enum):
    """训练状态"""
    INIT = "init"
    QUEUED = "queued"
    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed" 