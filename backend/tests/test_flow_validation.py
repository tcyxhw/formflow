"""
Test suite for flow validation methods.

Tests the 9 validation rules for flow structure:
1. Single start node
2. At least one end node
3. At least one approval node
4. Non-end nodes have outgoing edges
5. Non-start nodes have incoming edges
6. Condition nodes have two branches
7. Approval nodes have approver config
8. Reachability from start to end
9. No dead cycles
"""
import pytest
from app.core.exceptions import BusinessError
from app.services.flow_service import FlowService


class TestFlowValidation:
    """Test flow validation methods."""

    def test_validate_single_start_node_success(self):
        """Test validation passes with exactly one start node."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        # Should not raise
        FlowService._validate_single_start_node(nodes)

    def test_validate_single_start_node_no_start(self):
        """Test validation fails with no start node."""
        nodes = [
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        with pytest.raises(BusinessError, match="流程必须有一个开始节点"):
            FlowService._validate_single_start_node(nodes)

    def test_validate_single_start_node_multiple_starts(self):
        """Test validation fails with multiple start nodes."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始1"},
            {"id": "start_2", "type": "start", "name": "开始2"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        with pytest.raises(BusinessError, match="流程只能有一个开始节点"):
            FlowService._validate_single_start_node(nodes)

    def test_validate_at_least_one_end_node_success(self):
        """Test validation passes with at least one end node."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        # Should not raise
        FlowService._validate_at_least_one_end_node(nodes)

    def test_validate_at_least_one_end_node_no_end(self):
        """Test validation fails with no end node."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
        ]
        with pytest.raises(BusinessError, match="流程必须至少有一个结束节点"):
            FlowService._validate_at_least_one_end_node(nodes)

    def test_validate_at_least_one_approval_node_success(self):
        """Test validation passes with at least one approval node."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        # Should not raise
        FlowService._validate_at_least_one_approval_node(nodes)

    def test_validate_at_least_one_approval_node_no_approval(self):
        """Test validation fails with no approval node."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        with pytest.raises(BusinessError, match="流程必须至少有一个审批节点"):
            FlowService._validate_at_least_one_approval_node(nodes)

    def test_validate_node_edges_success(self):
        """Test validation passes with proper edges."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
        ]
        # Should not raise
        FlowService._validate_node_edges(nodes, routes)

    def test_validate_node_edges_missing_outgoing(self):
        """Test validation fails when non-end node has no outgoing edge."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            # approval_1 has no outgoing edge
        ]
        with pytest.raises(BusinessError, match="节点必须有出边"):
            FlowService._validate_node_edges(nodes, routes)

    def test_validate_node_edges_missing_incoming(self):
        """Test validation fails when non-start node has no incoming edge."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "approval_2", "type": "approval", "name": "审批2"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
            # approval_2 has no incoming edge but has outgoing edge
            {"from_node_id": "approval_2", "to_node_id": "end_1"},
        ]
        with pytest.raises(BusinessError, match="节点必须有入边"):
            FlowService._validate_node_edges(nodes, routes)

    def test_validate_condition_node_branches_success(self):
        """Test validation passes with condition node having two branches."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "condition_1", "type": "condition", "name": "条件"},
            {"id": "approval_1", "type": "approval", "name": "审批1"},
            {"id": "approval_2", "type": "approval", "name": "审批2"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "condition_1"},
            {"from_node_id": "condition_1", "to_node_id": "approval_1"},
            {"from_node_id": "condition_1", "to_node_id": "approval_2"},
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
            {"from_node_id": "approval_2", "to_node_id": "end_1"},
        ]
        # Should not raise
        FlowService._validate_condition_node_branches(nodes, routes)

    def test_validate_condition_node_branches_insufficient(self):
        """Test validation fails with condition node having only one branch."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "condition_1", "type": "condition", "name": "条件"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "condition_1"},
            {"from_node_id": "condition_1", "to_node_id": "approval_1"},
            # Only one branch
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
        ]
        with pytest.raises(BusinessError, match="必须至少有两条分支"):
            FlowService._validate_condition_node_branches(nodes, routes)

    def test_validate_approval_node_config_success(self):
        """Test validation passes with approval node having config."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {
                "id": "approval_1",
                "type": "approval",
                "name": "审批",
                "config": {"approver_type": "user", "approver_ids": [1, 2]},
            },
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        # Should not raise
        FlowService._validate_approval_node_config(nodes)

    def test_validate_approval_node_config_missing_approver_type(self):
        """Test validation fails when approval node missing approver_type."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {
                "id": "approval_1",
                "type": "approval",
                "name": "审批",
                "config": {"approver_ids": [1, 2]},
            },
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        with pytest.raises(BusinessError, match="必须配置审批人"):
            FlowService._validate_approval_node_config(nodes)

    def test_validate_approval_node_config_missing_approver_ids(self):
        """Test validation fails when approval node missing approver_ids."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {
                "id": "approval_1",
                "type": "approval",
                "name": "审批",
                "config": {"approver_type": "user"},
            },
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        with pytest.raises(BusinessError, match="必须配置审批人"):
            FlowService._validate_approval_node_config(nodes)

    def test_validate_reachability_success(self):
        """Test validation passes when end node is reachable."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
        ]
        # Should not raise
        FlowService._validate_reachability(nodes, routes)

    def test_validate_reachability_unreachable_end(self):
        """Test validation fails when end node is unreachable."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            # end_1 is not reachable
        ]
        with pytest.raises(BusinessError, match="流程不可达"):
            FlowService._validate_reachability(nodes, routes)

    def test_validate_no_dead_cycles_success(self):
        """Test validation passes with no dead cycles."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
        ]
        # Should not raise
        FlowService._validate_no_dead_cycles(nodes, routes)

    def test_validate_no_dead_cycles_with_dead_cycle(self):
        """Test validation fails with dead cycle."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {"id": "approval_1", "type": "approval", "name": "审批1"},
            {"id": "approval_2", "type": "approval", "name": "审批2"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            {"from_node_id": "approval_1", "to_node_id": "approval_2"},
            {"from_node_id": "approval_2", "to_node_id": "approval_1"},  # Cycle
            {"from_node_id": "approval_2", "to_node_id": "end_1"},
        ]
        with pytest.raises(BusinessError, match="流程存在死循环"):
            FlowService._validate_no_dead_cycles(nodes, routes)

    def test_validate_flow_structure_all_pass(self):
        """Test _validate_flow_structure with all validations passing."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {
                "id": "approval_1",
                "type": "approval",
                "name": "审批",
                "config": {"approver_type": "user", "approver_ids": [1]},
            },
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = [
            {"from_node_id": "start_1", "to_node_id": "approval_1"},
            {"from_node_id": "approval_1", "to_node_id": "end_1"},
        ]
        # Should not raise
        FlowService._validate_flow_structure(nodes, routes)

    def test_validate_flow_structure_fails_on_first_error(self):
        """Test _validate_flow_structure stops on first validation error."""
        nodes = [
            # No start node - will fail first validation
            {"id": "approval_1", "type": "approval", "name": "审批"},
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        routes = []
        with pytest.raises(BusinessError, match="流程必须有一个开始节点"):
            FlowService._validate_flow_structure(nodes, routes)

    # ==================== 条件节点配置校验测试 ====================

    def test_validate_condition_node_config_success(self):
        """Test validation passes with valid condition node config."""
        nodes = [
            {"id": "start_1", "type": "start", "name": "开始"},
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                "label": "大额",
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "approval_1",
                            },
                            {
                                "priority": 2,
                                "label": "小额",
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "LESS_EQUAL",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "approval_2",
                            },
                        ],
                        "default_target_node_id": "approval_2",
                    }
                },
            },
            {
                "id": "approval_1",
                "type": "approval",
                "name": "大额审批",
                "config": {"approver_type": "user", "approver_ids": [1]},
            },
            {
                "id": "approval_2",
                "type": "approval",
                "name": "小额审批",
                "config": {"approver_type": "user", "approver_ids": [2]},
            },
            {"id": "end_1", "type": "end", "name": "结束"},
        ]
        # Should not raise
        FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_missing_condition_branches(self):
        """Test validation fails when condition_branches is missing."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {},  # Missing condition_branches
            },
        ]
        with pytest.raises(BusinessError, match="必须配置 condition_branches"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_missing_branches_array(self):
        """Test validation fails when branches array is missing."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        # Missing branches array
                        "default_target_node_id": "approval_1",
                    }
                },
            },
        ]
        with pytest.raises(BusinessError, match="必须包含 branches 数组"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_insufficient_branches(self):
        """Test validation fails when branches count < 2."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "approval_1",
                            }
                        ],
                        "default_target_node_id": "approval_1",
                    }
                },
            },
        ]
        with pytest.raises(BusinessError, match="branches 数组长度必须 >= 2"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_missing_priority(self):
        """Test validation fails when branch missing priority."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                # Missing priority
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "approval_1",
                            },
                            {
                                "priority": 2,
                                "condition": None,
                                "target_node_id": "approval_2",
                            },
                        ],
                        "default_target_node_id": "approval_2",
                    }
                },
            },
        ]
        with pytest.raises(BusinessError, match="缺少 priority 字段"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_missing_condition(self):
        """Test validation fails when branch missing condition."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                # Missing condition
                                "target_node_id": "approval_1",
                            },
                            {
                                "priority": 2,
                                "condition": None,
                                "target_node_id": "approval_2",
                            },
                        ],
                        "default_target_node_id": "approval_2",
                    }
                },
            },
        ]
        with pytest.raises(BusinessError, match="缺少 condition 字段"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_missing_target_node_id(self):
        """Test validation fails when branch missing target_node_id."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                # Missing target_node_id
                            },
                            {
                                "priority": 2,
                                "condition": None,
                                "target_node_id": "approval_2",
                            },
                        ],
                        "default_target_node_id": "approval_2",
                    }
                },
            },
        ]
        with pytest.raises(BusinessError, match="缺少 target_node_id 字段"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_invalid_target_node_id(self):
        """Test validation fails when target_node_id doesn't exist."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "nonexistent_node",
                            },
                            {
                                "priority": 2,
                                "condition": None,
                                "target_node_id": "approval_2",
                            },
                        ],
                        "default_target_node_id": "approval_2",
                    }
                },
            },
        ]
        with pytest.raises(BusinessError, match="target_node_id.*不存在"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_missing_default_target(self):
        """Test validation fails when default_target_node_id is missing."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "approval_1",
                            },
                            {
                                "priority": 2,
                                "condition": None,
                                "target_node_id": "approval_2",
                            },
                        ],
                        # Missing default_target_node_id
                    }
                },
            },
            {"id": "approval_1", "type": "approval", "name": "审批1"},
            {"id": "approval_2", "type": "approval", "name": "审批2"},
        ]
        with pytest.raises(BusinessError, match="必须配置 default_target_node_id"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_node_config_invalid_default_target(self):
        """Test validation fails when default_target_node_id doesn't exist."""
        nodes = [
            {
                "id": "condition_1",
                "type": "condition",
                "name": "条件分支",
                "config": {
                    "condition_branches": {
                        "branches": [
                            {
                                "priority": 1,
                                "condition": {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                "target_node_id": "approval_1",
                            },
                            {
                                "priority": 2,
                                "condition": None,
                                "target_node_id": "approval_2",
                            },
                        ],
                        "default_target_node_id": "nonexistent_node",
                    }
                },
            },
            {"id": "approval_1", "type": "approval", "name": "审批1"},
            {"id": "approval_2", "type": "approval", "name": "审批2"},
        ]
        with pytest.raises(BusinessError, match="default_target_node_id.*不存在"):
            FlowService._validate_condition_node_config(nodes)

    def test_validate_condition_expression_rule_success(self):
        """Test condition expression validation passes for valid RULE."""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "GREATER_THAN",
            "value": 5000,
            "fieldType": "NUMBER",
        }
        # Should not raise
        FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_group_success(self):
        """Test condition expression validation passes for valid GROUP."""
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": [
                {
                    "type": "RULE",
                    "fieldKey": "amount",
                    "operator": "GREATER_THAN",
                    "value": 5000,
                    "fieldType": "NUMBER",
                },
                {
                    "type": "RULE",
                    "fieldKey": "department",
                    "operator": "EQUALS",
                    "value": "Finance",
                    "fieldType": "TEXT",
                },
            ],
        }
        # Should not raise
        FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_rule_missing_fieldkey(self):
        """Test validation fails when RULE missing fieldKey."""
        condition = {
            "type": "RULE",
            # Missing fieldKey
            "operator": "GREATER_THAN",
            "value": 5000,
        }
        with pytest.raises(ValueError, match="fieldKey"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_rule_missing_operator(self):
        """Test validation fails when RULE missing operator."""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            # Missing operator
            "value": 5000,
        }
        with pytest.raises(ValueError, match="operator"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_rule_missing_value(self):
        """Test validation fails when RULE missing value."""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "GREATER_THAN",
            # Missing value
        }
        with pytest.raises(ValueError, match="value"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_unsupported_operator(self):
        """Test validation fails with unsupported operator."""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "UNSUPPORTED_OP",
            "value": 5000,
        }
        with pytest.raises(ValueError, match="不支持的运算符"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_group_missing_logic(self):
        """Test validation fails when GROUP missing logic."""
        condition = {
            "type": "GROUP",
            # Missing logic
            "children": [],
        }
        with pytest.raises(ValueError, match="logic"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_group_missing_children(self):
        """Test validation fails when GROUP missing children."""
        condition = {
            "type": "GROUP",
            "logic": "AND",
            # Missing children
        }
        with pytest.raises(ValueError, match="children"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_group_invalid_logic(self):
        """Test validation fails with invalid logic operator."""
        condition = {
            "type": "GROUP",
            "logic": "INVALID",
            "children": [],
        }
        with pytest.raises(ValueError, match="逻辑运算符"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_nested_success(self):
        """Test validation passes for nested condition groups."""
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": [
                {
                    "type": "RULE",
                    "fieldKey": "amount",
                    "operator": "GREATER_THAN",
                    "value": 5000,
                    "fieldType": "NUMBER",
                },
                {
                    "type": "GROUP",
                    "logic": "OR",
                    "children": [
                        {
                            "type": "RULE",
                            "fieldKey": "department",
                            "operator": "EQUALS",
                            "value": "Finance",
                            "fieldType": "TEXT",
                        },
                        {
                            "type": "RULE",
                            "fieldKey": "department",
                            "operator": "EQUALS",
                            "value": "HR",
                            "fieldType": "TEXT",
                        },
                    ],
                },
            ],
        }
        # Should not raise
        FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_invalid_type(self):
        """Test validation fails with invalid condition type."""
        condition = {
            "type": "INVALID_TYPE",
            "fieldKey": "amount",
            "operator": "GREATER_THAN",
            "value": 5000,
        }
        with pytest.raises(ValueError, match="不支持的条件类型"):
            FlowService._validate_condition_expression(condition)

    def test_validate_condition_expression_none(self):
        """Test validation passes for None condition."""
        # Should not raise
        FlowService._validate_condition_expression(None)

    def test_validate_condition_expression_invalid_format(self):
        """Test validation fails when condition is not a dict."""
        condition = "invalid"
        with pytest.raises(ValueError, match="必须是字典类型"):
            FlowService._validate_condition_expression(condition)
