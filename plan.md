

# 审批流程设计方案（精简版）

---

## 一、所有枚举

```
FieldType（字段类型）
  TEXT / NUMBER / SINGLE_SELECT / MULTI_SELECT / DATE / DATETIME / USER / DEPARTMENT

NodeType（流程节点类型）
  START / APPROVAL / CONDITION / CC / END

ApproverType（审批人类型）
  SPECIFIC_USER        指定人员
  FORM_FIELD           表单字段取值
  DEPARTMENT_POST      部门岗位匹配

MatchMode（岗位匹配方式，仅 DEPARTMENT_POST 时用）
  FIXED                指定部门 + 指定岗位
  CURRENT              发起人当前部门 + 指定岗位
  ORG_CHAIN_UP         沿发起人部门链向上找岗位

RejectStrategy（驳回策略）
  TO_START             驳回到发起人，流程结束
  TO_PREVIOUS          驳回到上一个审批节点

Operator（条件运算符）
  EQUALS / NOT_EQUALS
  GREATER_THAN / GREATER_EQUAL / LESS_THAN / LESS_EQUAL
  BETWEEN              需要两个值
  CONTAINS / NOT_CONTAINS
  IN / NOT_IN          值是数组
  HAS_ANY / HAS_ALL    多选字段专用，值是数组
  IS_EMPTY / IS_NOT_EMPTY   不需要值

Logic（逻辑关系）
  AND / OR

WorkflowStatus（流程定义状态）
  DRAFT / PUBLISHED / DISABLED

InstanceStatus（流程实例状态）
  RUNNING / APPROVED / REJECTED / CANCELED

TaskStatus（任务状态）
  PENDING / APPROVED / REJECTED / CANCELED

OperationType（操作日志类型）
  SUBMIT / APPROVE / REJECT / CANCEL / CC
```

---

## 二、字段类型 → 可用运算符映射

前端维护，用户选字段后过滤运算符下拉框：

```
TEXT:           EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, IS_EMPTY, IS_NOT_EMPTY
NUMBER:         EQUALS, NOT_EQUALS, GREATER_THAN, GREATER_EQUAL, LESS_THAN, LESS_EQUAL, BETWEEN, IS_EMPTY, IS_NOT_EMPTY
SINGLE_SELECT:  EQUALS, NOT_EQUALS, IN, NOT_IN, IS_EMPTY, IS_NOT_EMPTY
MULTI_SELECT:   HAS_ANY, HAS_ALL, IS_EMPTY, IS_NOT_EMPTY
DATE/DATETIME:  EQUALS, NOT_EQUALS, GREATER_THAN, GREATER_EQUAL, LESS_THAN, LESS_EQUAL, BETWEEN, IS_EMPTY, IS_NOT_EMPTY
USER:           EQUALS, NOT_EQUALS, IN, IS_EMPTY, IS_NOT_EMPTY
DEPARTMENT:     EQUALS, NOT_EQUALS, IN, IS_EMPTY, IS_NOT_EMPTY
```

---

## 三、运算符 → 值控件映射

前端维护，用户选运算符后决定渲染什么输入控件：

```
IS_EMPTY / IS_NOT_EMPTY → 隐藏值控件，value = null
BETWEEN                 → 两个输入控件，value = [min, max]
IN / NOT_IN / HAS_ANY / HAS_ALL → 多选控件，value = [v1, v2, ...]
其他                    → 单个输入控件，value = 单值

输入控件的具体样式由字段类型决定：
  TEXT           → 文本输入框
  NUMBER         → 数字输入框
  SINGLE_SELECT  → 下拉选择（选项来自表单字段配置）
  MULTI_SELECT   → 下拉多选
  DATE/DATETIME  → 日期选择器
  USER           → 人员选择器
  DEPARTMENT     → 部门选择器
```

---

## 四、条件数据结构

### 单条规则

```json
{
  "type": "RULE",
  "fieldKey": "amount",
  "fieldType": "NUMBER",
  "operator": "GREATER_THAN",
  "value": 10000
}
```

### 逻辑组（可嵌套）

```json
{
  "type": "GROUP",
  "logic": "AND",
  "children": [
    { "type": "RULE", "fieldKey": "amount", "fieldType": "NUMBER", "operator": "GREATER_THAN", "value": 10000 },
    { "type": "RULE", "fieldKey": "category", "fieldType": "SINGLE_SELECT", "operator": "EQUALS", "value": "招待" }
  ]
}
```

### 条件节点完整配置（存在节点表 node_config 里）

```json
{
  "branches": [
    {
      "priority": 1,
      "label": "大额走总监",
      "targetNodeKey": "node_director",
      "condition": { "type": "GROUP", "logic": "AND", "children": [...] }
    },
    {
      "priority": 2,
      "label": "普通走经理",
      "targetNodeKey": "node_manager",
      "condition": { "type": "GROUP", "logic": "AND", "children": [...] }
    }
  ],
  "defaultTargetNodeKey": "node_manager"
}
```

---

## 五、审批节点配置结构

根据 approverType 不同，使用不同字段：

```
SPECIFIC_USER 时：
{
  "approverType": "SPECIFIC_USER",
  "approverIds": [1001, 1002],
  "rejectStrategy": "TO_START"
}

FORM_FIELD 时：
{
  "approverType": "FORM_FIELD",
  "formFieldKey": "project_leader",
  "rejectStrategy": "TO_START"
}

DEPARTMENT_POST + FIXED 时：
{
  "approverType": "DEPARTMENT_POST",
  "matchMode": "FIXED",
  "departmentId": 50,
  "postId": 12,
  "rejectStrategy": "TO_START"
}

DEPARTMENT_POST + CURRENT 时：
{
  "approverType": "DEPARTMENT_POST",
  "matchMode": "CURRENT",
  "postId": 15,
  "rejectStrategy": "TO_PREVIOUS"
}

DEPARTMENT_POST + ORG_CHAIN_UP 时：
{
  "approverType": "DEPARTMENT_POST",
  "matchMode": "ORG_CHAIN_UP",
  "postId": 15,
  "rejectStrategy": "TO_START"
}
```

---

## 六、核心逻辑——条件评估

流程走到 CONDITION 节点时触发。

### evaluate（递归）

```
evaluate(node, formData):

  如果 node.type == RULE:
    actualValue = formData[node.fieldKey]
    return compare(actualValue, node.operator, node.value, node.fieldType)

  如果 node.type == GROUP:
    对每个 child 递归调用 evaluate，收集结果
    logic == AND → 全部true才true
    logic == OR  → 有一个true就true
```

### compare（每种运算符怎么算）

```
compare(actual, operator, expected, fieldType):

  // 1. 空值运算符
  IS_EMPTY:      actual是null或""或空数组 → true
  IS_NOT_EMPTY:  取反

  // 2. actual为空时兜底
  actual为null或"" → 直接返回false

  // 3. 类型转换
  NUMBER:    actual和expected都转double，BETWEEN时expected两个元素都转
  DATE:      actual和expected都转日期对象
  其他:      都转字符串

  // 4. 执行比较
  EQUALS:        actual == expected
  NOT_EQUALS:    actual != expected
  GREATER_THAN:  actual > expected
  GREATER_EQUAL: actual >= expected
  LESS_THAN:     actual < expected
  LESS_EQUAL:    actual <= expected
  BETWEEN:       actual >= expected[0] && actual <= expected[1]
  CONTAINS:      actual字符串包含expected子串
  NOT_CONTAINS:  取反
  IN:            expected列表包含actual
  NOT_IN:        取反
  HAS_ANY:       actual列表和expected列表有交集
  HAS_ALL:       actual列表包含expected列表全部元素
```

### 分支选择

```
按 priority 从小到大遍历 branches
对每个 branch 调 evaluate(branch.condition, formData)
第一个返回 true 的 → 走它的 targetNodeKey
全部 false → 走 defaultTargetNodeKey
```

---

## 七、核心逻辑——审批人解析

流程走到 APPROVAL 节点时触发。

```
resolveApprover(nodeConfig, instance, formData):

  SPECIFIC_USER:
    直接返回 nodeConfig.approverIds

  FORM_FIELD:
    从 formData 取 nodeConfig.formFieldKey 的值
    为空 → 报错
    不为空 → 返回

  DEPARTMENT_POST:
    根据 matchMode 分三种：

    FIXED:
      查 user_department_post 表
      WHERE department_id = nodeConfig.departmentId AND post_id = nodeConfig.postId
      查到 → 返回用户ID列表
      没查到 → 报错

    CURRENT:
      先查发起人的部门ID
      再查该部门下指定岗位的人
      查到 → 返回
      没查到 → 报错（不向上找）

    ORG_CHAIN_UP:
      currentDeptId = 发起人部门ID
      循环：
        查 currentDeptId 下指定岗位的人
        查到 → 返回
        没查到 → currentDeptId = 该部门的 parent_id
        parent_id 为空（到顶了）→ 跳出循环，报错
```

---

## 八、引擎主流程

```
1. 用户提交表单
   → 查已发布的流程定义
   → 创建流程实例（status=RUNNING，快照表单数据）
   → 从 START 节点开始推进

2. 推进逻辑 advanceFrom(当前节点)
   → 查连线表找下一个节点
   → 调用 executeNode(下一个节点)

3. executeNode 按节点类型分别处理

   CONDITION:
     评估条件 → 确定目标节点 → 递归调 executeNode(目标节点)

   APPROVAL:
     解析审批人 → 创建待办任务 → 通知审批人 → 停下来等操作

   CC:
     创建抄送任务 → 不停留，继续 advanceFrom

   END:
     实例状态改 APPROVED → 通知发起人 → 结束

4. 审批人通过
   → 更新任务状态 → 记日志 → advanceFrom(当前节点) 继续往后走

5. 审批人驳回
   → 更新任务状态 → 记日志
   → TO_START: 实例状态改 REJECTED，结束
   → TO_PREVIOUS: 找上一个审批节点，重新创建任务

6. 发起人撤回
   → 取消所有待处理任务 → 实例状态改 CANCELED
```

---

## 九、数据库需要的表

```
流程定义表:     id, form_id, name, status, version, created_by
流程节点表:     id, workflow_id, node_key, node_type, node_name, node_config(JSON), position_x, position_y
流程连线表:     id, workflow_id, source_node_key, target_node_key
流程实例表:     id, workflow_id, form_id, form_data_id, status, current_node_key, initiator_id, form_data_snapshot(JSON), started_at, finished_at
审批任务表:     id, instance_id, node_key, node_name, task_type, assignee_id, status, comment, operated_at
操作日志表:     id, instance_id, operation_type, operator_id, node_key, comment, created_at

另外你的系统必须有：
部门表:         id, name, parent_id（parent_id 是组织链向上查找的关键）
岗位表:         id, name
用户部门岗位关系: user_id, department_id, post_id
```

---

## 十、一个完整例子串一遍

学生请假，请假2天：

```
表单数据: { "leave_days": 2, "leave_type": "事假" }
发起人: 信息学院学生(userId=301)

流程定义:
  START → CONDITION(请假天数判断) → 分支1(≤3天)→ 辅导员审批 → END
                                  → 分支2(>3天) → 院长审批 → END

① 提交，创建实例，从START推进到CONDITION节点

② CONDITION节点评估:
   分支1条件: leave_days LESS_EQUAL 3
   compare(2, LESS_EQUAL, 3, NUMBER) → 2 <= 3 → true
   命中分支1 → 走辅导员审批节点

③ 辅导员审批节点配置:
   approverType=DEPARTMENT_POST, matchMode=ORG_CHAIN_UP, postId=辅导员
   发起人部门=信息学院(id=30)
   查信息学院下辅导员 → 找到张老师(userId=501)
   创建任务给张老师

④ 张老师通过 → advanceFrom → 走到END → 实例状态改APPROVED → 通知学生
```