import pytest
from tests.base.base_test import BaseTest
from tests.base.auth_steps import (
    step_create_admin,
    step_admin_login,
    step_create_normal_user,
    step_user_login
)
from tests.base.knowledge_base_steps import step_create_knowledge_base
from tests.base.document_steps import (
    step_create_document,
    step_update_document,
    step_get_document,
    step_list_documents,
    step_soft_delete_document
)


class TestDocumentFlow(BaseTest):
    """文档管理相关功能测试"""
    
    def get_test_name(self) -> str:
        return "document_flow"
    
    @pytest.mark.asyncio
    async def test_document_flow(self, state, client):
        """测试文档管理流程"""
        # 设置测试数据
        await self.run_step(step_create_admin, state, client)
        await self.run_step(step_admin_login, state, client)
        await self.run_step(step_create_normal_user, state, client)
        await self.run_step(step_user_login, state, client)
        await self.run_step(step_create_knowledge_base, state, client)
        
        # 文档管理测试
        await self.run_step(step_create_document, state, client)
        await self.run_step(step_update_document, state, client)
        await self.run_step(step_get_document, state, client)
        await self.run_step(step_list_documents, state, client)
        await self.run_step(step_soft_delete_document, state, client)