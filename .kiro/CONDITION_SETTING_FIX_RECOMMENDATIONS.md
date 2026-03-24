# 条件设置修复建议

## 修复方案详解

### 问题1: DATE/DATETIME 运算符缺失

**当前状态**:
```typescript
DATE: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
  { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
  { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
  { value: 'DATE_BEFORE_NOW', label: '早于当前时间X天', needsValue: true, valueType: 'SINGLE' },
  { value: 'DATE_AFTER_NOW', label: '晚于当前时间X天', needsValue: true, valueType: 'SINGLE' },
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**修复方案**:
```typescript
DATE: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },  // ✅ 新增
  { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
  { value: 'GREATER_EQUAL', label: '不早于', needsValue: true, valueType: 'SINGLE' },  // ✅ 新增
  { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
  { value: 'LESS_EQUAL', label: '不晚于', needsValue: true, valueType: 'SINGLE' },  // ✅ 新增
  { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  // 可选：保留业务扩展
  { value: 'DATE_BEFORE_NOW', label: '早于当前时间X天', needsValue: true, valueType: 'SINGLE' },
  { value: 'DATE_AFTER_NOW', label: '晚于当前时间X天', needsValue: true, valueType: 'SINGLE' },
]

DATETIME: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },  // ✅ 新增
  { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
  { value: 'GREATER_EQUAL', label: '不早于', needsValue: true, valueType: 'SINGLE' },  // ✅ 新增
  { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
  { value: 'LESS_EQUAL', label: '不晚于', needsValue: true, valueType: 'SINGLE' },  // ✅ 新增
  { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**文件**: `my-app/src/types/condition.ts`

---

### 问题2: SINGLE_SELECT 的 IN/NOT_IN valueType 错误

**当前状态**:
```typescript
SINGLE_SELECT: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'IN', label: '属于', needsValue: true, valueType: 'SINGLE' },  // ❌ 错误
  { value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'SINGLE' },  // ❌ 错误
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**修复方案**:

**步骤1**: 在 OperatorConfig 接口中扩展 valueType

```typescript
export interface OperatorConfig {
  value: Operator
  label: string
  needsValue: boolean
  valueType: 'SINGLE' | 'RANGE' | 'MULTI' | 'NONE'  // ✅ 新增 'MULTI'
}
```

**步骤2**: 更新 SINGLE_SELECT 映射

```typescript
SINGLE_SELECT: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'IN', label: '属于', needsValue: true, valueType: 'MULTI' },  // ✅ 改为 MULTI
  { value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'MULTI' },  // ✅ 改为 MULTI
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**步骤3**: 更新 MULTI_SELECT 映射

```typescript
MULTI_SELECT: [
  { value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'MULTI' },  // ✅ 改为 MULTI
  { value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'MULTI' },  // ✅ 改为 MULTI
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  // ❌ 移除 NOT_CONTAINS（设计中没有）
]
```

**文件**: `my-app/src/types/condition.ts`

---

### 问题3: MULTI_SELECT 多了 NOT_CONTAINS

**当前状态**:
```typescript
MULTI_SELECT: [
  { value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'SINGLE' },
  { value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_CONTAINS', label: '不包含', needsValue: true, valueType: 'SINGLE' },  // ❌ 多余
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**修复方案**: 移除 NOT_CONTAINS

```typescript
MULTI_SELECT: [
  { value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'MULTI' },
  { value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'MULTI' },
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**文件**: `my-app/src/types/condition.ts`

---

### 问题4: 后端 IN/NOT_IN/HAS_ANY/HAS_ALL 实现有缺陷

**当前实现**:
```python
elif operator == 'IN':
    if isinstance(right, list):
        return left in right
    return left == right

elif operator == 'NOT_IN':
    if isinstance(right, list):
        return left not in right
    return left != right

elif operator == 'HAS_ANY':
    if isinstance(left, list) and isinstance(right, list):
        return any(item in left for item in right)
    if isinstance(left, list):
        return right in left
    return False

elif operator == 'HAS_ALL':
    if isinstance(left, list) and isinstance(right, list):
        return all(item in left for item in right)
    if isinstance(left, list):
        return right in left
    return False
```

**修复方案**:
```python
elif operator == 'IN':
    # 确保 right 是列表
    if not isinstance(right, list):
        right = [right]
    return left in right

elif operator == 'NOT_IN':
    # 确保 right 是列表
    if not isinstance(right, list):
        right = [right]
    return left not in right

elif operator == 'HAS_ANY':
    # 确保两个都是列表
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return any(item in left for item in right)

elif operator == 'HAS_ALL':
    # 确保两个都是列表
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return all(item in left for item in right)
```

**文件**: `backend/app/services/condition_evaluator_v2.py`

---

### 问题5: 后端缺少 DATETIME 类型转换

**当前实现**:
```python
@staticmethod
def _convert_value(value: Any, field_type: Optional[str]) -> Any:
    if value is None:
        return None

    if field_type == 'NUMBER':
        # ...
    elif field_type == 'DATE':
        # ...
    elif field_type == 'MULTI_SELECT':
        # ...
    
    return value  # ❌ DATETIME 没有处理
```

**修复方案**:
```python
@staticmethod
def _convert_value(value: Any, field_type: Optional[str]) -> Any:
    if value is None:
        return None

    if field_type == 'NUMBER':
        try:
            if isinstance(value, (int, float)):
                return value
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert {value} to NUMBER")
            return value

    elif field_type == 'DATE':
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except (ValueError, TypeError):
                logger.warning(f"Failed to convert {value} to DATE")
                return value

    elif field_type == 'DATETIME':  # ✅ 新增
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                logger.warning(f"Failed to convert {value} to DATETIME")
                return value

    elif field_type == 'MULTI_SELECT':
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',')]
        return [value]

    # ✅ 新增：USER 和 DEPARTMENT 转换为字符串
    elif field_type in ('USER', 'DEPARTMENT'):
        return str(value)

    return value
```

**文件**: `backend/app/services/condition_evaluator_v2.py`

---

### 问题6: 前端校验规则不完整

**当前实现** (ConditionRule.vue):
```typescript
const needsValue = computed(() => {
  if (!rule.operator) return false
  return !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(rule.operator)
})
```

**修复方案**: 在 ValueInput.vue 中添加完整校验

```typescript
// ValueInput.vue 中添加校验函数
const validateValue = (value: any, operator: string, fieldType: string): string | null => {
  // 1. 检查是否需要值
  if (['IS_EMPTY', 'IS_NOT_EMPTY'].includes(operator)) {
    return null  // 这些运算符不需要值
  }

  // 2. 检查值是否为空
  if (value === null || value === undefined || value === '') {
    return '请输入值'
  }

  // 3. BETWEEN 运算符的特殊校验
  if (operator === 'BETWEEN') {
    if (!Array.isArray(value) || value.length !== 2) {
      return '请输入两个值'
    }
    if (value[0] === null || value[0] === undefined || value[1] === null || value[1] === undefined) {
      return '两个值都不能为空'
    }
    
    // 检查大小关系
    if (fieldType === 'NUMBER') {
      const min = parseFloat(value[0])
      const max = parseFloat(value[1])
      if (isNaN(min) || isNaN(max)) {
        return '请输入有效的数字'
      }
      if (min > max) {
        return '最小值不能大于最大值'
      }
    } else if (fieldType === 'DATE' || fieldType === 'DATETIME') {
      if (new Date(value[0]) > new Date(value[1])) {
        return '开始日期不能晚于结束日期'
      }
    }
    return null
  }

  // 4. IN/NOT_IN/HAS_ANY/HAS_ALL 的数组校验
  if (['IN', 'NOT_IN', 'HAS_ANY', 'HAS_ALL'].includes(operator)) {
    if (!Array.isArray(value) || value.length === 0) {
      return '至少选择一个值'
    }
    return null
  }

  // 5. NUMBER 类型的值校验
  if (fieldType === 'NUMBER') {
    const num = parseFloat(value)
    if (isNaN(num)) {
      return '请输入有效的数字'
    }
    return null
  }

  // 6. DATE 类型的值校验
  if (fieldType === 'DATE') {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    if (!dateRegex.test(value)) {
      return '请输入有效的日期格式 (YYYY-MM-DD)'
    }
    return null
  }

  // 7. DATETIME 类型的值校验
  if (fieldType === 'DATETIME') {
    try {
      new Date(value)
      return null
    } catch {
      return '请输入有效的日期时间'
    }
  }

  return null
}

// 在模板中使用
const validationError = computed(() => {
  return validateValue(modelValue, props.operator, props.fieldType)
})
```

**文件**: `my-app/src/components/flow-configurator/ValueInput.vue`

---

### 问题7: 后端系统字段实现不完整

**当前状态**: 前端定义了系统字段，但后端没有在条件评估时注入

**修复方案**: 在 condition_evaluator_v2.py 中添加系统字段注入

```python
@staticmethod
def evaluate(
    condition: Optional[Dict[str, Any]],
    data: Dict[str, Any],
    system_fields: Optional[Dict[str, Any]] = None  # ✅ 新增参数
) -> bool:
    """
    评估条件树

    Args:
        condition: 条件树（RULE 或 GROUP 节点）
        data: 提交数据（表单字段值）
        system_fields: 系统字段值（提交人、提交人部门、提交时间等）

    Returns:
        条件是否满足
    """
    if condition is None:
        return True

    # ✅ 合并系统字段和表单数据
    if system_fields:
        data = {**data, **system_fields}

    try:
        condition_type = condition.get('type')

        if condition_type == 'RULE':
            return ConditionEvaluatorV2._evaluate_rule(condition, data)
        elif condition_type == 'GROUP':
            return ConditionEvaluatorV2._evaluate_group(condition, data)
        else:
            logger.warning(f"Unknown condition type: {condition_type}")
            return False

    except Exception as e:
        logger.error(f"Error evaluating condition: {e}", exc_info=True)
        return False
```

**在流程引擎中调用**:
```python
# 在 process_service.py 或流程引擎中
system_fields = {
    'sys_submitter': submission.submitter_id,
    'sys_submitter_dept': submission.submitter_dept_id,
    'sys_submit_time': submission.created_at.isoformat(),
}

result = ConditionEvaluatorV2.evaluate(
    condition=branch.condition,
    data=submission.form_data,
    system_fields=system_fields
)
```

**文件**: `backend/app/services/condition_evaluator_v2.py`

---

### 问题8: 后端条件校验不完整

**修复方案**: 创建条件校验模块

**新文件**: `backend/app/services/condition_validator.py`

```python
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
from app.types.condition import OPERATOR_MAP


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

        # 2. 检查 fieldKey 是否存在
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
```

**文件**: `backend/app/services/condition_validator.py`

---

## 修复优先级和工作量估计

| 优先级 | 问题 | 工作量 | 预计时间 |
|--------|------|--------|---------|
| 🔴 高 | 1. DATE/DATETIME 运算符缺失 | 小 | 15分钟 |
| 🔴 高 | 2. SINGLE_SELECT valueType 错误 | 小 | 15分钟 |
| 🔴 高 | 3. MULTI_SELECT 多了 NOT_CONTAINS | 小 | 5分钟 |
| 🔴 高 | 4. 后端 IN/NOT_IN/HAS_ANY/HAS_ALL 缺陷 | 中 | 30分钟 |
| 🔴 高 | 5. 后端缺少 DATETIME 转换 | 小 | 15分钟 |
| 🟡 中 | 6. 前端校验规则不完整 | 中 | 45分钟 |
| 🟡 中 | 7. 后端系统字段实现不完整 | 中 | 30分钟 |
| 🟡 中 | 8. 后端条件校验不完整 | 大 | 1小时 |

**总计**: 约 3.5 小时

---

## 测试建议

### 前端测试

1. **运算符映射测试**
   - 选择 DATE 字段，验证运算符列表包含 NOT_EQUALS, GREATER_EQUAL, LESS_EQUAL
   - 选择 SINGLE_SELECT 字段，选择 IN 运算符，验证显示多选控件

2. **校验测试**
   - BETWEEN 运算符：输入两个值，验证大小关系校验
   - DATE 字段：输入无效日期格式，验证错误提示
   - NUMBER 字段：输入非数字，验证错误提示

### 后端测试

1. **条件评估测试**
   - 测试 IN/NOT_IN 运算符的多值处理
   - 测试 HAS_ANY/HAS_ALL 运算符的多值处理
   - 测试 DATETIME 类型的转换和比较

2. **系统字段测试**
   - 验证 sys_submitter, sys_submitter_dept, sys_submit_time 能正确注入
   - 验证条件能正确评估系统字段

3. **校验测试**
   - 验证无效的 fieldKey 被拒绝
   - 验证无效的 operator 被拒绝
   - 验证无效的 target_node_id 被拒绝
