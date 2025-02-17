from fastapi import APIRouter
from app.api.v1.admin import knowledge_base as admin_kb
from app.api.v1.client import knowledge_base as client_kb
from . import api_router

v1_router = APIRouter()
v1_router.include_router(api_router)

api_router.include_router(admin_kb.router, prefix="/admin/knowledge-bases", tags=["admin"])
api_router.include_router(client_kb.router, prefix="/client", tags=["client"]) 