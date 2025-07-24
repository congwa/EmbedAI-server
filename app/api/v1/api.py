from fastapi import APIRouter
from . import api_router

# 创建v1版本API路由器
v1_router = APIRouter()

# 包含主API路由器
v1_router.include_router(api_router) 