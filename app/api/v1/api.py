from fastapi import APIRouter
from app.api.v1.admin import knowledge_base as admin_kb
from app.api.v1.client import knowledge_base as client_kb

api_router = APIRouter()

api_router.include_router(admin_kb.router, prefix="/admin/knowledge-bases", tags=["admin"])
api_router.include_router(client_kb.router, prefix="/client", tags=["client"]) 