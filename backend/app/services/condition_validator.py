"""
模块用途: 条件表达式校验
依赖配置: 无外部依赖
数据流向: 条件树 + 表单字段 + 流程节点 -> 校验 -> 错误列表
函数清单:
    - validate_condition_tree(): 校验条件树
    - validate_rule(): 校验单条规则
    - validate_branches_config(): 校验分支配置
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConditionValidator:
    """条件表达式校验器"""

    FIELD_OPERATOR_MAP = {
        'TEXT': ['EQUALS', 'NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'NUMBER': ['EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'GREATER_EQUAL', 'LESS_THAN', 'LESS_EQUAL', 'BETWEEN', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'SINGLE_SELECT': ['EQUALS', 'NOT_EQUALS', 'IN', 'NOT_IN', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'MULTI_SELECT': ['HAS_ANY', 'HAS_ALL', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'DATE': ['EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'GREATER_EQUAL', 'LESS_THAN', 'LESS_EQUAL', 'BETWEEN', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'DATETIME': ['EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'GREATER_EQUAL', 'LESS_THAN', 'LESS_EQUAL', 'BETWEEN', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'USER': ['EQUALS', 'NOT_EQUALS', 'IN', 'IS_EMPTY', 'IS_NOT_EMPTY'],
        'DEPARTMENT': ['EQUALS', 'NOT_EQUALS', 'IN', 'IS_EMPTY', 'IS_NOT_EMPTY'],
    }

    @staticmethod
    def validate_condition_tree(
        condition: Optional[Dict[str, Any]],
        form_fields: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        校验条件树

        Args:
            condition: 条件树
            form_fields: 表单字段映射 {fieldKey: {type, ...}}

        Returns:
            错误列表（空列表表示校验通过）
        """
        errors = []

        if condition is None:
            return errors

        if condition.get('type') == 'RULE':
            errors.extend(ConditionValidator.validate_rule(condition, form_fields))
        elif condition.get('type') == 'GROUP':
            errors.extend(ConditionValidator.validate_group(condition, form_fields))
        else:
            errors.append(f"Unknown condition type: {condition.get('type')}")

        return errors

    @staticmethod
    def validate_rule(
        rule: Dict[str, Any],
        form_fields: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """校验单条规则"""
        errors = []

        field_key = rule.get('fieldKey')
        operator = rule.get('operator')
        value = rule.get('value')
        field_type = rule.get('fieldType')

        # 1. 检查 fieldKey
        if not field_key:
            errors.append("fieldKey 不能为空")
            return errors

        # 2. 检查 fieldKey 是否存在（允许系统字段）
        if field_key not in form_fields and not field_key.startswith('sys_'):
            errors.append(f"字段 {field_key} 不存在")
            return errors

        # 3. 检查 operator
        if not operator:
            errors.append(f"字段 {field_key} 的 operator 不能为空")
            return errors

        # 4. 检查 operator 和 fieldType 的映射关系
        if field_type not in ConditionValidator.FIELD_OPERATOR_MAP:
            errors.append(f"未知的字段类型: {field_type}")
            return errors

        allowed_operators = ConditionValidator.FIELD_OPERATOR_MAP[field_type]
        if operator not in allowed_operators:
            errors.append(f"字段类型 {field_type} 不支持运算符 {operator}")
            return errors

        # 5. 检查 value
        if operator not in ['IS_EMPTY', 'IS_NOT_EMPTY']:
            if value is None or value == '' or value == []:
                errors.append(f"字段 {field_key} 的值不能为空")

        # 6. 校验 fieldType 与表单字段配置里的一致性（任务2）
        if field_key in form_fields:
            config_field_type = form_fields[field_key].get('type')
            if config_field_type and config_field_type != field_type:
                errors.append(f"字段 {field_key} 的 fieldType ({field_type}) 与表单配置不一致 ({config_field_type})")

        return errors

    @staticmethod
    def validate_group(
        group: Dict[str, Any],
        form_fields: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """校验条件组"""
        errors = []

        logic = group.get('logic')
        children = group.get('children', [])

        # 1. 检查 logic
        if logic not in ['AND', 'OR']:
            errors.append(f"Unknown logic type: {logic}")

        # 2. 检查 children
        if not children:
            errors.append("条件组不能为空")
            return errors

        # 3. 递归校验子节点
        for i, child in enumerate(children):
            child_errors = ConditionValidator.validate_condition_tree(child, form_fields)
            errors.extend([f"子条件 {i}: {err}" for err in child_errors])

        return errors

    @staticmethod
    def validate_branches_config(
        config: Dict[str, Any],
        form_fields: Dict[str, Dict[str, Any]],
        node_ids: List[int]
    ) -> List[str]:
        """
        校验分支配置

        Args:
            config: 分支配置
            form_fields: 表单字段映射
            node_ids: 流程中所有节点的 ID

        Returns:
            错误列表
        """
        errors = []

        branches = config.get('branches', [])
        default_target_node_id = config.get('default_target_node_id')

        # 1. 检查分支数量
        if not branches:
            errors.append("至少需要一个分支")

        # 2. 检查每个分支
        for i, branch in enumerate(branches):
            # 检查 priority
            if 'priority' not in branch:
                errors.append(f"分支 {i} 缺少 priority")

            # 检查 target_node_id
            target_node_id = branch.get('target_node_id')
            if not target_node_id:
                errors.append(f"分支 {i} 的 target_node_id 不能为空")
            elif target_node_id not in node_ids:
                errors.append(f"分支 {i} 的目标节点 {target_node_id} 不存在")

            # 检查 condition
            condition = branch.get('condition')
            if condition:
                cond_errors = ConditionValidator.validate_condition_tree(condition, form_fields)
                errors.extend([f"分支 {i} 条件: {err}" for err in cond_errors])

        # 3. 检查默认目标节点
        if not default_target_node_id:
            errors.append("default_target_node_id 不能为空")
        elif default_target_node_id not in node_ids:
            errors.append(f"默认目标节点 {default_target_node_id} 不存在")

        return errors
