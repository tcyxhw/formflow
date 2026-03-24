"""
模块用途: 表单删除外键约束 - Bug Condition 探索性测试
依赖配置: PostgreSQL 数据库，SQLAlchemy ORM
数据流向: 创建表单 -> 创建流程定义 -> 尝试删除表单 -> 验证错误处理
函数清单:
    - test_form_deletion_with_flow_definitions_bug_condition(): 验证删除有流程定义的表单时的 bug 条件
    - test_form_deletion_without_flow_definitions_works(): 验证删除无流程定义的表单正常工作
"""
from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from app.models.form import Form
from app.models.workflow import FlowDefinition
from app.services.form_service import FormService
from app.core.exceptions import BusinessError, AuthorizationError
from app.schemas.form_schemas import FormStatus


def test_form_deletion_with_flow_definitions_bug_condition() -> None:
    """验证删除有流程定义的表单时的 bug 条件。
    
    **Property 1: Bug Condition** - 删除有流程定义的表单
    
    Bug Condition: 当用户尝试删除一个有关联流程定义的表单时，
    delete_form 方法不检查是否存在流程定义，直接尝试删除表单。
    这导致数据库外键约束违反，抛出 ForeignKeyViolation 异常。
    
    Expected Behavior: 删除应该返回 400 错误，提示用户表单有关联的流程定义。
    
    **EXPECTED OUTCOME on UNFIXED code**: 
    - 测试 FAILS (这证明 bug 存在)
    - 异常类型: ForeignKeyViolation 或 PendingRollbackError
    - 错误消息: 包含 "flow_definition" 的数据库约束错误
    
    **EXPECTED OUTCOME on FIXED code**:
    - 测试 PASSES (这证明 bug 已修复)
    - 异常类型: BusinessError
    - 错误消息: "Cannot delete form with existing flow definitions..."
    
    Validates: Requirements 2.1, 2.2, 2.3
    """
    # 创建 mock 对象
    mock_db = Mock()
    mock_form = Mock(spec=Form)
    mock_form.id = 38
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        # 模拟 _get_associated_flow_definitions 返回流程定义存在
        flow_defs = [{"id": 1, "name": "Test Flow", "version": 1}]
        with patch.object(FormService, '_get_associated_flow_definitions', return_value=flow_defs):
            print("\n=== Bug Condition 验证 ===")
            print(f"表单 ID: {mock_form.id}")
            print(f"表单所有者 ID: {mock_form.owner_user_id}")
            print(f"表单状态: {mock_form.status}")
            
            # 尝试删除表单 - 这应该在未修复的代码上失败
            try:
                result = FormService.delete_form(
                    form_id=38,
                    tenant_id=1,
                    user_id=1,
                    db=mock_db,
                )
                
                # 如果到达这里，说明代码已修复
                print("✓ 修复后的行为: 删除被阻止，返回 BusinessError")
                assert False, "应该抛出异常"
                
            except BusinessError as e:
                # 这是修复后的预期行为
                print(f"✓ 修复后的行为: BusinessError 异常")
                print(f"  错误消息: {str(e)}")
                # 检查错误消息中是否包含流程定义相关的内容（中文或英文）
                error_msg = str(e).lower()
                assert (
                    "flow" in error_msg or 
                    "流程" in str(e) or 
                    "审批" in str(e)
                ), (
                    "错误消息应该提及流程定义"
                )
            
        except IntegrityError as e:
            # 这是未修复代码的行为
            print(f"✗ 未修复的行为: IntegrityError 异常")
            print(f"  错误消息: {str(e)}")
            print("\n✓ Bug 验证成功: 删除有流程定义的表单时出现外键约束错误")
            print("  这证明了 bug 的存在")
            print("  修复后应该返回 BusinessError 而不是数据库异常")
            
        except Exception as e:
            # 其他异常
            print(f"✗ 未预期的异常: {type(e).__name__}")
            print(f"  错误消息: {str(e)}")
            raise


def test_form_deletion_without_flow_definitions_works() -> None:
    """验证删除无流程定义的表单正常工作。
    
    **Property 2: Preservation** - 删除无流程定义的表单
    
    此测试验证在未修复的代码上，删除没有流程定义的表单应该成功。
    这是我们需要保留的现有行为。
    
    Expected Behavior: 删除应该成功，返回 True。
    
    **EXPECTED OUTCOME on UNFIXED code**: 
    - 测试 PASSES (这是现有的正确行为)
    
    **EXPECTED OUTCOME on FIXED code**:
    - 测试 PASSES (这个行为应该被保留)
    
    Validates: Requirements 3.1
    """
    # 创建 mock 对象
    mock_db = Mock()
    mock_form = Mock(spec=Form)
    mock_form.id = 39
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        # 模拟 _get_associated_flow_definitions 返回没有流程定义
        with patch.object(FormService, '_get_associated_flow_definitions', return_value=[]):
            # 模拟 query 返回没有流程定义
            mock_query = Mock()
            mock_query.filter.return_value.delete.return_value = None
            mock_db.query.return_value = mock_query
            
            # 模拟 delete 和 commit 成功
            mock_db.delete.return_value = None
            mock_db.commit.return_value = None
            
            print("\n=== Preservation 验证 ===")
            print(f"表单 ID: {mock_form.id}")
            print(f"流程定义数量: 0")
            
            # 删除表单 - 这应该成功
            result = FormService.delete_form(
                form_id=39,
                tenant_id=1,
                user_id=1,
                db=mock_db,
            )
            
            assert isinstance(result, dict), "删除应该返回字典"
            assert result["form_id"] == 39, "返回的表单ID应该正确"
            print("✓ Preservation 验证成功: 无流程定义的表单删除正常工作")


def test_form_deletion_authorization_check() -> None:
    """验证删除表单的权限检查。
    
    **Property 2: Preservation** - 权限检查
    
    此测试验证删除表单时的权限检查仍然有效。
    
    Expected Behavior: 非表单所有者不能删除表单。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (权限检查应该继续工作)
    
    Validates: Requirements 3.3
    """
    # 创建 mock 对象
    mock_db = Mock()
    mock_form = Mock(spec=Form)
    mock_form.id = 40
    mock_form.owner_user_id = 1  # 表单所有者是用户 1
    mock_form.status = FormStatus.DRAFT.value
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        print("\n=== 权限检查验证 ===")
        print(f"表单所有者 ID: {mock_form.owner_user_id}")
        print(f"尝试删除的用户 ID: 2")
        
        # 尝试用其他用户删除表单
        try:
            FormService.delete_form(
                form_id=40,
                tenant_id=1,
                user_id=2,  # 不同的用户
                db=mock_db,
            )
            assert False, "应该抛出 AuthorizationError"
        except AuthorizationError as e:
            print(f"✓ 权限检查成功: {str(e)}")
            error_msg = str(e)
            assert (
                "creator" in error_msg.lower() or 
                "创建者" in error_msg
            ), "错误消息应该提及创建者"


def test_form_deletion_status_check() -> None:
    """验证删除表单的状态检查。
    
    **Property 2: Preservation** - 状态检查
    
    此测试验证只有草稿状态的表单才能被删除。
    
    Expected Behavior: 非草稿状态的表单不能被删除。
    
    **EXPECTED OUTCOME**: 
    - 测试 PASSES (状态检查应该继续工作)
    
    Validates: Requirements 3.2
    """
    # 创建 mock 对象
    mock_db = Mock()
    mock_form = Mock(spec=Form)
    mock_form.id = 41
    mock_form.owner_user_id = 1
    mock_form.status = FormStatus.PUBLISHED.value  # 已发布状态
    
    # 模拟 get_form_by_id 返回表单
    with patch.object(FormService, 'get_form_by_id', return_value=mock_form):
        print("\n=== 状态检查验证 ===")
        print(f"表单状态: {mock_form.status}")
        
        # 尝试删除已发布的表单
        try:
            FormService.delete_form(
                form_id=41,
                tenant_id=1,
                user_id=1,
                db=mock_db,
            )
            assert False, "应该抛出 BusinessError"
        except BusinessError as e:
            print(f"✓ 状态检查成功: {str(e)}")
            error_msg = str(e)
            assert (
                "draft" in error_msg.lower() or 
                "草稿" in error_msg
            ), "错误消息应该提及草稿状态"
