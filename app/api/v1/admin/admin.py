from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.auth import get_current_admin_user
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.knowledge_base import KnowledgeBaseService
from app.core.response import APIResponse
from app.schemas.admin import AdminRegister
from app.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/register")
async def register_admin(
    admin_data: AdminRegister,
    db: Session = Depends(get_db)
):
    """管理员注册接口

    通过特殊的注册码创建管理员账户

    Args:
        admin_data (AdminRegister): 包含邮箱、密码和注册码的数据
        db (Session): 数据库会话对象

    Returns:
        APIResponse: 包含注册成功信息的响应对象

    Raises:
        HTTPException: 当注册码无效或邮箱已存在时抛出相应错误
    """
    if admin_data.register_code != settings.ADMIN_REGISTER_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid register code"
        )

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == admin_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建管理员用户
    user = User(
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return APIResponse.success(message="Admin user created successfully")

@router.post("/knowledge-bases")
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建新的知识库

    创建一个新的知识库记录，只有管理员用户可以执行此操作

    Args:
        kb (KnowledgeBaseCreate): 知识库创建模型，包含知识库的基本信息
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含创建成功的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.create(kb, current_user.id)
    return APIResponse.success(data=result)

@router.put("/knowledge-bases/{kb_id}")
async def update_knowledge_base(
    kb_id: int,
    kb: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新知识库信息

    更新指定ID的知识库信息，只有管理员用户可以执行此操作

    Args:
        kb_id (int): 要更新的知识库ID
        kb (KnowledgeBaseUpdate): 知识库更新模型，包含需要更新的字段
        db (Session): 数据库会话对象
        current_user: 当前登录的管理员用户

    Returns:
        APIResponse: 包含更新后的知识库信息的响应对象
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.update(kb_id, kb, current_user.id)
    return APIResponse.success(data=result)