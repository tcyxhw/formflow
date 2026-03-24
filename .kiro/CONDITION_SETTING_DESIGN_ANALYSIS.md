# 审批流程条件设置 — 设计方案对比分析

## 执行摘要

对比你的详细设计方案与当前实现，**整体框架已基本完成**，但存在以下**关键缺陷和未完善部分**：

### 核心问题（优先级从高到低）

1. **运算符映射不完整** ⚠️ 高优先级
   - MULTI_SELECT 多了 `NOT_CONTAINS`（设计中没有）
   - DATE/DATETIME 缺少 `NOT_EQUALS`, `GREATER_EQUAL`, `LESS_EQUAL`
   - SINGLE_SELECT 的 `IN`/`NOT_IN` 的 valueType 标记错误

2. **后端条件评估逻辑缺陷** ⚠️ 高优先级
   - `IN`/`NOT_IN` 运算符处理不正确（应该支持多值列表）
   - `HAS_ANY`/`HAS_ALL` 的多值处理逻辑有问题
   - 缺少 `NOT_EQUALS` 的实现
   - 缺少 `GREATER_EQUAL`/`LESS_EQUAL` 的实现

3. **前端校验规则不完整** ⚠️ 中优先级
   - 缺少对 BETWEEN 值的校验（两个值的大小关系）
   - 缺少对 DATE/DATETIME 格式的校验
   - 缺少对 NUMBER 类型值的校验

4. **系统字段实现不完整** ⚠️ 中优先级
   - 缺少 `sys_submit_time` 的 DATETIME 类型支持
   - 缺少对系统字段的后端校验

5. **值输入控件映射不完整** ⚠️ 中优先级
   - SINGLE_SELECT 的 `IN`/`NOT_IN` 应该显示多选控件，但 valueType 标记为 'SINGLE'
   - MULTI_SELECT 缺少对 `NOT_CONTAINS` 的值控件处理

6. **后端类型转换不完整** ⚠️ 低优先级
   - DATETIME 类型缺少处理
   - 类型转换失败时的错误处理不够完善

---

## 详细对比分析

### 一、枚举定义对比

#### 1.1 字段类型 (FieldType)
**设计要求**: TEXT, NUMBER, SINGLE_SELECT, MULTI_SELECT, DATE, DATETIME, USER, DEPARTMENT

**当前实现**: ✅ 完全符合

```typescript
// 前端 condition.ts
export type FieldType = 
  | 'TEXT' | 'NUMBER' | 'SINGLE_SELECT' | 'MULTI_SELECT'
  | 'DATE' | 'DATETIME' | 'USER' | 'DEPARTMENT'
```

---

#### 1.2 运算符 (Operator)
**设计要求**: 15个运算符

**当前实现**: ❌ 多了2个，缺少部分

```typescript
// 前端 condition.ts - 当前有17个
export type Operator =
  | 'EQUALS' | 'NOT_EQUALS' | 'GREATER_THAN' | 'GREATER_EQUAL'
  | 'LESS_THAN' | 'LESS_EQUAL' | 'BETWEEN' | 'CONTAINS'
  | 'NOT_CONTAINS' | 'IN' | 'NOT_IN' | 'HAS_ANY' | 'HAS_ALL'
  | 'IS_EMPTY' | 'IS_NOT_EMPTY'
  | 'DATE_BEFORE_NOW' | 'DATE_AFTER_NOW'  // ⚠️ 额外的，设计中没有
```

**问题**: 
- 多了 `DATE_BEFORE_NOW` 和 `DATE_AFTER_NOW`（这是业务扩展，可以保留但需要文档说明）
- 这两个运算符在设计方案中没有定义

---

#### 1.3 逻辑关系 (Logic)
**设计要求**: AND, OR

**当前实现**: ✅ 完全符合

```typescript
export type LogicType = 'AND' | 'OR'
```

---

#### 1.4 条件节点类型 (ConditionNodeType)
**设计要求**: GROUP, RULE

**当前实现**: ✅ 完全符合（通过 type 字段区分）

```typescript
export interface ConditionRule {
  type: 'RULE'
  // ...
}

export interface ConditionGroup {
  type: 'GROUP'
  // ...
}
```

---

### 二、字段类型与运算符映射对比

#### 2.1 TEXT 类型
**设计要求**:
```
EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ✅ 完全符合

```typescript
TEXT: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'CONTAINS', label: '包含', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_CONTAINS', label: '不包含', needsValue: true, valueType: 'SINGLE' },
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

---

#### 2.2 NUMBER 类型
**设计要求**:
```
EQUALS, NOT_EQUALS, GREATER_THAN, GREATER_EQUAL, LESS_THAN, LESS_EQUAL, BETWEEN, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ✅ 完全符合

---

#### 2.3 SINGLE_SELECT 类型
**设计要求**:
```
EQUALS, NOT_EQUALS, IN, NOT_IN, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ⚠️ 运算符正确，但 valueType 标记错误

```typescript
SINGLE_SELECT: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'IN', label: '属于', needsValue: true, valueType: 'SINGLE' },  // ❌ 应该是 'RANGE' 或新增 'MULTI'
  { value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'SINGLE' },  // ❌ 应该是 'RANGE' 或新增 'MULTI'
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**问题**: 
- `IN` 和 `NOT_IN` 应该支持多值，但 valueType 标记为 'SINGLE'
- 需要新增 valueType: 'MULTI' 或改为 'RANGE'

---

#### 2.4 MULTI_SELECT 类型
**设计要求**:
```
HAS_ANY, HAS_ALL, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ❌ 多了一个运算符

```typescript
MULTI_SELECT: [
  { value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'SINGLE' },
  { value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'SINGLE' },
  { value: 'NOT_CONTAINS', label: '不包含', needsValue: true, valueType: 'SINGLE' },  // ❌ 设计中没有
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**问题**: 
- 多了 `NOT_CONTAINS`，设计中没有定义
- 需要移除或在设计中补充说明

---

#### 2.5 DATE 类型
**设计要求**:
```
EQUALS, NOT_EQUALS, GREATER_THAN, GREATER_EQUAL, LESS_THAN, LESS_EQUAL, BETWEEN, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ❌ 缺少部分运算符

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

**问题**: 
- ❌ 缺少 `NOT_EQUALS`
- ❌ 缺少 `GREATER_EQUAL`（不早于）
- ❌ 缺少 `LESS_EQUAL`（不晚于）
- ⚠️ 多了 `DATE_BEFORE_NOW` 和 `DATE_AFTER_NOW`（业务扩展）

---

#### 2.6 DATETIME 类型
**设计要求**: 同 DATE

**当前实现**: ❌ 缺少部分运算符

```typescript
DATETIME: [
  { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
  { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
  { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
  { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
  { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
  { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
]
```

**问题**: 
- ❌ 缺少 `NOT_EQUALS`
- ❌ 缺少 `GREATER_EQUAL`
- ❌ 缺少 `LESS_EQUAL`

---

#### 2.7 USER 类型
**设计要求**:
```
EQUALS, NOT_EQUALS, IN, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ✅ 完全符合

---

#### 2.8 DEPARTMENT 类型
**设计要求**:
```
EQUALS, NOT_EQUALS, IN, IS_EMPTY, IS_NOT_EMPTY
```

**当前实现**: ✅ 完全符合

---

### 三、运算符与值输入控件映射对比

#### 3.1 设计要求的决策表

| 字段类型 | 运算符 | 值控件 | value形态 |
|---------|--------|--------|----------|
| SINGLE_SELECT | IN | 下拉多选 | ["选项A","选项B"] |
| SINGLE_SELECT | NOT_IN | 下拉多选 | ["选项A","选项B"] |
| MULTI_SELECT | HAS_ANY | 下拉多选 | ["标签1","标签2"] |
| MULTI_SELECT | HAS_ALL | 下拉多选 | ["标签1","标签2"] |

#### 3.2 当前实现问题

**问题1**: valueType 标记不准确
```typescript
// 当前标记为 'SINGLE'，但实际应该支持多值
{ value: 'IN', label: '属于', needsValue: true, valueType: 'SINGLE' }
{ value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'SINGLE' }
{ value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'SINGLE' }
{ value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'SINGLE' }
```

**需要修复**: 
- 新增 valueType: 'MULTI' 类型
- 或改为 'RANGE'（但这会与 BETWEEN 混淆）
- 建议新增 'MULTI' 类型

---

### 四、后端条件评估逻辑对比

#### 4.1 evaluate 函数
**设计要求**: 递归评估条件树，支持 RULE 和 GROUP

**当前实现**: ✅ 基本符合

```python
@staticmethod
def evaluate(condition: Optional[Dict[str, Any]], data: Dict[str, Any]) -> bool:
    if condition is None:
        return True
    
    condition_type = condition.get('type')
    if condition_type == 'RULE':
        return ConditionEvaluatorV2._evaluate_rule(condition, data)
    elif condition_type == 'GROUP':
        return ConditionEvaluatorV2._evaluate_group(condition, data)
```

---

#### 4.2 _evaluate_rule 函数
**设计要求**: 处理空值、类型转换、调用 compare

**当前实现**: ⚠️ 基本符合，但有缺陷

```python
@staticmethod
def _evaluate_rule(rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
    field_key = rule.get('fieldKey')
    operator = rule.get('operator')
    value = rule.get('value')
    field_type = rule.get('fieldType')
    
    # 处理空值检查
    if operator == 'IS_EMPTY':
        return field_value is None or field_value == '' or field_value == []
    elif operator == 'IS_NOT_EMPTY':
        return field_value is not None and field_value != '' and field_value != []
    
    # 对于其他运算符，如果字段值为空，返回 False
    if field_value is None:
        return False
```

**问题**: 
- ❌ 缺少对 `NOT_EQUALS` 的处理
- ❌ 缺少对 `GREATER_EQUAL`/`LESS_EQUAL` 的处理
- ⚠️ 空值处理逻辑正确，但需要补充文档

---

#### 4.3 _compare 函数
**设计要求**: 实现所有15个运算符的比较逻辑

**当前实现**: ❌ 缺少部分运算符

```python
@staticmethod
def _compare(left: Any, operator: str, right: Any, field_type: Optional[str]) -> bool:
    # 已实现的运算符
    if operator == 'EQUALS': return left == right
    elif operator == 'NOT_EQUALS': return left != right  # ✅ 有实现
    elif operator == 'GREATER_THAN': return left > right
    elif operator == 'GREATER_EQUAL': return left >= right  # ✅ 有实现
    elif operator == 'LESS_THAN': return left < right
    elif operator == 'LESS_EQUAL': return left <= right  # ✅ 有实现
    elif operator == 'BETWEEN': ...
    elif operator == 'CONTAINS': ...
    elif operator == 'NOT_CONTAINS': ...
    elif operator == 'IN': ...  # ⚠️ 实现有问题
    elif operator == 'NOT_IN': ...  # ⚠️ 实现有问题
    elif operator == 'HAS_ANY': ...  # ⚠️ 实现有问题
    elif operator == 'HAS_ALL': ...  # ⚠️ 实现有问题
    elif operator == 'IS_EMPTY': ...
    elif operator == 'IS_NOT_EMPTY': ...
    elif operator == 'DATE_BEFORE_NOW': ...  # ⚠️ 额外实现
    elif operator == 'DATE_AFTER_NOW': ...  # ⚠️ 额外实现
```

**具体问题**:

**问题1**: IN/NOT_IN 的实现不正确
```python
# 当前实现
elif operator == 'IN':
    if isinstance(right, list):
        return left in right
    return left == right

# 问题: 这个实现是对的，但需要确保 right 总是列表
```

**问题2**: HAS_ANY/HAS_ALL 的实现逻辑有缺陷
```python
# 当前实现
elif operator == 'HAS_ANY':
    if isinstance(left, list) and isinstance(right, list):
        return any(item in left for item in right)
    if isinstance(left, list):
        return right in left
    return False

# 问题: 当 right 不是列表时，应该转换为列表
```

---

#### 4.4 _convert_value 函数
**设计要求**: 根据 fieldType 进行类型转换

**当前实现**: ⚠️ 缺少 DATETIME 处理

```python
@staticmethod
def _convert_value(value: Any, field_type: Optional[str]) -> Any:
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
    
    elif field_type == 'MULTI_SELECT':
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',')]
        return [value]
    
    # ❌ 缺少 DATETIME 处理
    # ❌ 缺少 USER/DEPARTMENT 处理
    
    return value
```

**问题**: 
- ❌ 缺少 DATETIME 类型的转换
- ❌ 缺少 USER/DEPARTMENT 类型的转换（应该转换为字符串或数字）

---

### 五、前端校验规则对比

#### 5.1 设计要求的校验规则

```
每条 RULE 需要校验：
✓ fieldKey 不能为空
✓ operator 不能为空
✓ 如果 operator 不是 IS_EMPTY/IS_NOT_EMPTY，则 value 不能为空
✓ 如果 operator 是 BETWEEN，value 必须是长度为2的数组，且两个值都不能为空，且第一个 <= 第二个
✓ 如果 operator 是 IN/NOT_IN/HAS_ANY/HAS_ALL，value 必须是非空数组，且至少有一个元素
✓ 如果 fieldType 是 NUMBER，value 必须是有效数字
✓ 如果 fieldType 是 DATE，value 必须是有效日期格式
```

#### 5.2 当前实现
**当前状态**: ❌ 校验规则不完整

在 ConditionRule.vue 中：
```typescript
const needsValue = computed(() => {
  if (!rule.operator) return false
  return !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(rule.operator)
})
```

**问题**: 
- ❌ 缺少 BETWEEN 值的校验（两个值的大小关系）
- ❌ 缺少 DATE/DATETIME 格式的校验
- ❌ 缺少 NUMBER 类型值的校验
- ❌ 缺少 IN/NOT_IN/HAS_ANY/HAS_ALL 的数组长度校验

---

### 六、系统字段实现对比

#### 6.1 设计要求

```typescript
{ key: "sys_submitter",      name: "提交人",     type: "USER" }
{ key: "sys_submitter_dept", name: "提交人部门", type: "DEPARTMENT" }
{ key: "sys_submit_time",    name: "提交时间",   type: "DATETIME" }
```

#### 6.2 当前实现
**前端**: ✅ 完全符合

```typescript
// ConditionBuilderV2.vue
fields.push(
  {
    key: 'sys_submitter',
    name: '提交人',
    type: 'USER',
    isSystem: true,
  },
  {
    key: 'sys_submitter_dept',
    name: '提交人部门',
    type: 'DEPARTMENT',
    isSystem: true,
  },
  {
    key: 'sys_submit_time',
    name: '提交时间',
    type: 'DATETIME',
    isSystem: true,
  }
)
```

**后端**: ❌ 缺少实现

- 后端没有在 form_fields API 中返回系统字段
- 后端没有在条件评估时注入系统字段值

---

### 七、条件节点配置结构对比

#### 7.1 设计要求

```json
{
  "branches": [
    {
      "priority": 1,
      "label": "分支标签",
      "targetNodeKey": "node_id",
      "condition": { ... }
    }
  ],
  "defaultTargetNodeKey": "node_id"
}
```

#### 7.2 当前实现
**前端类型定义**: ⚠️ 字段名不一致

```typescript
// flow.ts
export interface ConditionBranch {
  priority: number
  label: string
  condition: Condition
  target_node_id: number  // ❌ 应该是 targetNodeKey
}

export interface ConditionBranchesConfig {
  branches: ConditionBranch[]
  default_target_node_id: number  // ❌ 应该是 defaultTargetNodeKey
}
```

**问题**: 
- ❌ 字段名使用 snake_case，但设计中是 camelCase
- ⚠️ 这可能是前后端约定的差异，需要确认

---

### 八、前端交互细节对比

#### 8.1 设计要求的联动规则

```
选字段时：
  → 清空运算符和值
  → 刷新运算符下拉选项

选运算符时：
  → 清空值
  → 刷新值输入控件
  → 如果选了 IS_EMPTY/IS_NOT_EMPTY，隐藏值控件
  → 如果选了 BETWEEN，显示两个值控件
  → 如果选了 IN/NOT_IN/HAS_ANY/HAS_ALL，显示多选控件
```

#### 8.2 当前实现
**ConditionRule.vue**: ✅ 基本符合

```typescript
const updateField = (fieldKey: string) => {
  const field = props.fields.find(f => f.key === fieldKey)
  if (!field) return

  emit('update', {
    ...props.rule,
    fieldKey,
    fieldType: field.type,
    operator: '', // 重置运算符
    value: null, // 重置值
  })
}

const updateOperator = (operator: string) => {
  emit('update', {
    ...props.rule,
    operator: operator as any,
    value: null, // 重置值
  })
}
```

**ValueInput.vue**: ⚠️ 需要查看完整实现

---

### 九、后端校验规则对比

#### 9.1 设计要求

```
✓ condition 里引用的 fieldKey 在表单字段配置里确实存在
✓ condition 里的 fieldType 和表单字段配置里的类型一致
✓ condition 里的 operator 和 fieldType 的映射关系是合法的
✓ targetNodeKey 在流程定义的节点列表里确实存在
✓ defaultTargetNodeKey 在流程定义的节点列表里确实存在
```

#### 9.2 当前实现
**当前状态**: ❌ 后端校验不完整

在 flow_service.py 或 process_service.py 中需要添加这些校验，但目前没有看到完整实现。

---

## 总结：未完善部分清单

### 🔴 高优先级（必须修复）

1. **DATE/DATETIME 运算符缺失**
   - 缺少 `NOT_EQUALS`, `GREATER_EQUAL`, `LESS_EQUAL`
   - 文件: `my-app/src/types/condition.ts`

2. **SINGLE_SELECT 的 IN/NOT_IN valueType 错误**
   - 应该支持多值，但标记为 'SINGLE'
   - 需要新增 valueType: 'MULTI'
   - 文件: `my-app/src/types/condition.ts`

3. **MULTI_SELECT 多了 NOT_CONTAINS**
   - 设计中没有定义
   - 需要移除或补充设计说明
   - 文件: `my-app/src/types/condition.ts`

4. **后端 IN/NOT_IN/HAS_ANY/HAS_ALL 实现有缺陷**
   - 需要确保正确处理多值列表
   - 文件: `backend/app/services/condition_evaluator_v2.py`

5. **后端缺少 DATETIME 类型转换**
   - 文件: `backend/app/services/condition_evaluator_v2.py`

### 🟡 中优先级（应该完善）

6. **前端校验规则不完整**
   - 缺少 BETWEEN 值的大小关系校验
   - 缺少 DATE/DATETIME 格式校验
   - 缺少 NUMBER 类型值校验
   - 文件: `my-app/src/components/flow-configurator/ConditionRule.vue`

7. **后端系统字段实现不完整**
   - 后端需要在条件评估时注入系统字段值
   - 文件: `backend/app/services/condition_evaluator_v2.py`

8. **后端条件校验不完整**
   - 需要校验 fieldKey 存在性
   - 需要校验 operator 和 fieldType 的映射关系
   - 文件: `backend/app/services/flow_service.py` 或新增验证模块

### 🟢 低优先级（可选优化）

9. **字段名 snake_case vs camelCase 不一致**
   - 前端类型定义使用 snake_case
   - 需要确认与后端的约定
   - 文件: `my-app/src/types/flow.ts`

10. **DATE_BEFORE_NOW 和 DATE_AFTER_NOW 需要文档说明**
    - 这是业务扩展，超出设计范围
    - 需要在设计文档中补充说明

---

## 建议修复顺序

1. **第一阶段**: 修复高优先级问题（1-5）
2. **第二阶段**: 完善中优先级问题（6-8）
3. **第三阶段**: 优化低优先级问题（9-10）
