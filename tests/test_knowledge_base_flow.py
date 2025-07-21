import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from app.models.database import AsyncSessionLocal, engine, Base
from app.models.knowledge_base import PermissionType
from .utils.test_state import TestState
from tests.utils.decorators import step_decorator
import pytest_asyncio
import asyncio
from tests.base.base_test import BaseTest
from tests.base.auth_steps import (
    step_create_admin,
    step_admin_login,
    step_create_normal_user,
    step_user_login,
    step_create_another_user,
    step_another_user_login
)
from tests.base.knowledge_base_steps import (
    step_create_knowledge_base,
    step_get_kb_members,
    step_add_member_to_kb,
    step_train_knowledge_base
)
from tests.base.document_steps import step_create_document


class TestKnowledgeBaseFlow(BaseTest):
    """知识库相关功能测试"""
    
    def get_test_name(self) -> str:
        return "knowledge_base_flow"
    
    @pytest.mark.asyncio
    async def test_full_flow(self, state, client):
        """完整的测试流程"""
        # 用户认证流程
        await self.run_step(step_create_admin, state, client)
        await self.run_step(step_admin_login, state, client)
        await self.run_step(step_create_normal_user, state, client)
        await self.run_step(step_user_login, state, client)
        await self.run_step(step_create_another_user, state, client)
        await self.run_step(step_another_user_login, state, client)
        
        # 知识库管理流程
        await self.run_step(step_create_knowledge_base, state, client)
        await self.run_step(step_get_kb_members, state, client)
        await self.run_step(step_add_member_to_kb, state, client)
        
        # 权限管理测试
        await self.run_step(self.step_update_member_permission, state, client)
        await self.run_step(self.step_test_member_access, state, client)
        await self.run_step(self.step_remove_member, state, client)
        
        # 文档管理
        await self.run_step(step_create_document, state, client)
    
    @step_decorator("update_member_permission")
    async def step_update_member_permission(self, state, client):
        """更新成员权限"""
        user_token = state.get_step_data("user_token")
        kb_id = state.get_step_data("kb_id")
        another_user_id = state.get_step_data("another_user_id")
        
        # 更新权限
        response = client.put(
            f"/api/v1/admin/knowledge-bases/{kb_id}/members/{another_user_id}",
            json={
                "permission": "admin"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        # 验证权限更新
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}/members",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        members = response.json()["data"]["members"]
        admin = next(m for m in members if m["id"] == another_user_id)
        assert admin["permission"] == "admin"
        return response.json()
    
    @step_decorator("test_member_access")
    async def step_test_member_access(self, state, client):
        """测试成员访问权限"""
        another_user_token = state.get_step_data("another_user_token")
        kb_id = state.get_step_data("kb_id")
        
        # 测试查看知识库详情
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}",
            headers={"Authorization": f"Bearer {another_user_token}"}
        )
        assert response.status_code == 200
        
        # 测试查看成员列表
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}/members",
            headers={"Authorization": f"Bearer {another_user_token}"}
        )
        assert response.status_code == 200
        return response.json()
    
    @step_decorator("remove_member")
    async def step_remove_member(self, state, client):
        """移除成员"""
        user_token = state.get_step_data("user_token")
        kb_id = state.get_step_data("kb_id")
        another_user_id = state.get_step_data("another_user_id")
        
        # 移除成员
        response = client.delete(
            f"/api/v1/admin/knowledge-bases/{kb_id}/members/{another_user_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        # 验证成员已移除
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}/members",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        members = response.json()["data"]["members"]
        assert len(members) == 1
        assert all(m["id"] != another_user_id for m in members)
        
        # 验证被移除成员无法访问
        another_user_token = state.get_step_data("another_user_token")
        response = client.get(
            f"/api/v1/admin/knowledge-bases/{kb_id}",
            headers={"Authorization": f"Bearer {another_user_token}"}
        )
        assert response.status_code == 403
        return response.json() 