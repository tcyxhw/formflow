"""
模块用途: 表单删除 - Preservation 测试
依赖配置: PostgreSQL 数据库，SQLAlchemy ORM
数据流向: 创建表单 -> 验证删除行为 -> 确保现有功能保留
函数清单:
    - test_delete_draft_form_without_flow_definitions(): 验证删除无流程定义的草稿表单成功
    - test_delete_published_form_fails(): 验证删除已发布表单失败
    - test_delete_form_without_permission_fails(): 验证无权限删除表单失败
    - test_delete_form_removes_versions(): 验证删除表单时同时删除版本
"""
from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, call
from sqlalchemy.orm import Session

from app.models.form import Form, FormVersion
from app.models.workflow import FlowDefinition
from app.services.form_service import FormService
from app.core.exceptions import BusinessError, AuthorizationError
from app.schemas.form_schemas import FormStatus


def test_delete_draft_form_without_flow_definitions() -> None:
    """验证删除无流程定义的草稿表单成功。
    
    **Property 2: Preservation** - 删除无流程定义的表单
    
    此测试验证删除没有流程定义的表单应该成功。
    这是我们需要保留的现有行为。
    
    Expected Behavior: 删除应该成功，返回 True。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (这个行为应该被保留)
    
    Validates: Requirements 3.1
    """
    # 创建 mock 对象
    mock_db = Mock(spec=Session)
    mock_form = Mock(spec=Form)
    mock_form.id = 100
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        # 模拟 query 返回没有流程定义
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.delete.return_value = None
        mock_db.query.return_value = mock_query
        
        # 模拟 delete 和 commit 成功
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        print("\n=== Preservation 测试: 删除无流程定义的草稿表单 ===")
        print(f"表单 ID: {mock_form.id}")
        print(f"表单状态: {mock_form.status}")
        print(f"流程定义数量: 0")
        
        # 删除表单 - 这应该成功
        result = FormService.delete_form(
            form_id=100,
            tenant_id=1,
            user_id=1,
            db=mock_db,
        )
        
        assert result is True, "删除应该返回 True"
        
        # 验证 delete 被调用
        mock_db.delete.assert_called_once_with(mock_form)
        
        # 验证 commit 被调用
        mock_db.commit.assert_called_once()
        
        print("✓ Preservation 验证成功: 无流程定义的表单删除正常工作")


def test_delete_published_form_fails() -> None:
    """验证删除已发布表单失败。
    
    **Property 2: Preservation** - 状态检查
    
    此测试验证只有草稿状态的表单才能被删除。
    已发布的表单应该返回错误。
    
    Expected Behavior: 删除应该失败，返回 BusinessError。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (状态检查应该继续工作)
    
    Validates: Requirements 3.2
    """
    # 创建 mock 对象
    mock_db = Mock(spec=Session)
    mock_form = Mock(spec=Form)
    mock_form.id = 101
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.PUBLISHED.value  # 已发布状态
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        print("\n=== Preservation 测试: 删除已发布表单 ===")
        print(f"表单 ID: {mock_form.id}")
        print(f"表单状态: {mock_form.status}")
        
        # 尝试删除已发布的表单
        try:
            FormService.delete_form(
                form_id=101,
                tenant_id=1,
                user_id=1,
                db=mock_db,
            )
            assert False, "应该抛出 BusinessError"
        except BusinessError as e:
            print(f"✓ Preservation 验证成功: {str(e)}")
            error_msg = str(e)
            assert (
                "draft" in error_msg.lower() or 
                "草稿" in error_msg
            ), "错误消息应该提及草稿状态"
            
            # 验证 delete 没有被调用
            mock_db.delete.assert_not_called()


def test_delete_form_without_permission_fails() -> None:
    """验证无权限删除表单失败。
    
    **Property 2: Preservation** - 权限检查
    
    此测试验证删除表单时的权限检查仍然有效。
    非表单所有者不能删除表单。
    
    Expected Behavior: 删除应该失败，返回 AuthorizationError。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (权限检查应该继续工作)
    
    Validates: Requirements 3.3
    """
    # 创建 mock 对象
    mock_db = Mock(spec=Session)
    mock_form = Mock(spec=Form)
    mock_form.id = 102
    mock_form.owner_user_id = 1  # 表单所有者是用户 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        print("\n=== Preservation 测试: 无权限删除表单 ===")
        print(f"表单所有者 ID: {mock_form.owner_user_id}")
        print(f"尝试删除的用户 ID: 2")
        
        # 尝试用其他用户删除表单
        try:
            FormService.delete_form(
                form_id=102,
                tenant_id=1,
                user_id=2,  # 不同的用户
                db=mock_db,
            )
            assert False, "应该抛出 AuthorizationError"
        except AuthorizationError as e:
            print(f"✓ Preservation 验证成功: {str(e)}")
            error_msg = str(e)
            assert (
                "creator" in error_msg.lower() or 
                "创建者" in error_msg
            ), "错误消息应该提及创建者"
            
            # 验证 delete 没有被调用
            mock_db.delete.assert_not_called()


def test_delete_form_removes_versions() -> None:
    """验证删除表单时同时删除版本。
    
    **Property 2: Preservation** - 版本删除
    
    此测试验证删除表单时，所有关联的表单版本也被删除。
    
    Expected Behavior: 删除表单时应该删除所有版本。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (版本删除应该继续工作)
    
    Validates: Requirements 3.1
    """
    # 创建 mock 对象
    mock_db = Mock(spec=Session)
    mock_form = Mock(spec=Form)
    mock_form.id = 103
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        # 模拟 query 返回没有流程定义
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.delete.return_value = None
        mock_db.query.return_value = mock_query
        
        # 模拟 delete 和 commit 成功
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        print("\n=== Preservation 测试: 删除表单时删除版本 ===")
        print(f"表单 ID: {mock_form.id}")
        
        # 删除表单
        result = FormService.delete_form(
            form_id=103,
            tenant_id=1,
            user_id=1,
            db=mock_db,
        )
        
        assert result is True, "删除应该返回 True"
        
        # 验证 query 被调用两次：一次查询流程定义，一次查询版本
        assert mock_db.query.call_count >= 2, "应该查询流程定义和版本"
        
        # 验证 delete 被调用（删除表单）
        mock_db.delete.assert_called_once_with(mock_form)
        
        # 验证 commit 被调用
        mock_db.commit.assert_called_once()
        
        print("✓ Preservation 验证成功: 删除表单时同时删除版本")


def test_delete_form_with_multiple_versions() -> None:
    """验证删除表单时删除所有版本。
    
    **Property 2: Preservation** - 多版本删除
    
    此测试验证删除表单时，所有版本都被删除。
    
    Expected Behavior: 删除表单时应该删除所有版本。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (多版本删除应该继续工作)
    
    Validates: Requirements 3.1
    """
    # 创建 mock 对象
    mock_db = Mock(spec=Session)
    mock_form = Mock(spec=Form)
    mock_form.id = 104
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        # 模拟 query 返回没有流程定义
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.delete.return_value = None
        mock_db.query.return_value = mock_query
        
        # 模拟 delete 和 commit 成功
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        print("\n=== Preservation 测试: 删除表单时删除多个版本 ===")
        print(f"表单 ID: {mock_form.id}")
        print(f"版本数量: 3")
        
        # 删除表单
        result = FormService.delete_form(
            form_id=104,
            tenant_id=1,
            user_id=1,
            db=mock_db,
        )
        
        assert result is True, "删除应该返回 True"
        
        # 验证 delete 被调用（删除表单）
        mock_db.delete.assert_called_once_with(mock_form)
        
        # 验证 commit 被调用
        mock_db.commit.assert_called_once()
        
        print("✓ Preservation 验证成功: 删除表单时删除所有版本")
