from fastapi import APIRouter
from .admin import router as admin_router
from .auth import router as auth_router
from .knowledge_base import router as kb_router
from .document import router as document_router

router = APIRouter()

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(kb_router)
router.include_router(document_router)