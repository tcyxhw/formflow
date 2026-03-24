# 审批流程完善设计方案 - 第二部分

## 六、CONDITION 节点实现详设

### 6.1 节点类型扩展

**修改 FlowNode 模型**：
```python
# 在 backend/app/models/workflow.py 中
class FlowNode(DBBaseModel):
    type = Column(String(20), nullable=False, comment="节点类型：start/user/auto/end/condition/cc")
    
    # 对于 CONDITION 节点
    condition_branches = Column(JSONB, nullable=True, comment="条件分支配置")
```

### 6.2 条件分支配置格式

```json
{
  "branches": [
    {
      "priority": 1,
      "label": "大额招待费",
      "condition": {
        "type": "GROUP",
        "logic": "AND",
        "children": [
          {
            "type": "RULE",
            "fieldKey": "amount",
            "fieldType": "NUMBER",
            "operator": "GREATER_THAN",
            "value": 10000
          },
          {
            "type": "RULE",
            "fieldKey": "category",
            "fieldType": "SINGLE_SELECT",
            "operator": "EQUALS",
            "value": "招待"
          }
        ]
      },
      "target_node_id": 123
    },
    {
      "priority": 2,
      "label": "普通报销",
      "condition": {
        "type": "GROUP",
        "logic": "AND",
        "children": [
          {
            "type": "RULE",
            "fieldKey": "amount",
            "fieldType": "NUMBER",
            "operator": "LESS_EQUAL",
            "value": 10000
          }
        ]
      },
      "target_node_id": 124
    }
  ],
  "default_target_node_id": 124
}
```

### 6.3 流程推进逻辑扩展

**修改 ProcessService._dispatch_nodes()**：

```python
@staticmethod
def _dispatch_nodes(...) -> List[Task]:
    """按照节点类型生成任务或继续路由"""
    
    tasks: List[Task] = []
    
    for node in candidate_nodes:
        if node.id in visited:
            continue
        visited.add(node.id)
        
        # 处理 CONDITION 节点
        if node.type == "condition":
            condition_result = ProcessService._evaluate_condition_branches(
                node=node,
                context=context,
                db=db,
            )
            
            if condition_result:
                target_node = db.query(FlowNode).filter(
                    FlowNode.id == condition_result["target_node_id"]
                ).first()
                
                if target_node:
                    tasks.extend(
                        ProcessService._dispatch_nodes(
                            process=process,
                            candidate_nodes=[target_node],
                            tenant_id=tenant_id,
                            db=db,
                            context=context,
                            visited=visited,
                            origin_node=node,
                        )
                    )
            continue
        
        # 处理 CC 节点
        if node.type == "cc":
            ProcessService._create_cc_task(process, node, tenant_id, db)
            
            # CC 节点后继续推进
            next_nodes = ProcessService._resolve_next_nodes(
                flow_definition_id=process.flow_definition_id,
                from_node=node,
                tenant_id=tenant_id,
                db=db,
                context=context,
            )
            
            tasks.extend(
                ProcessService._dispatch_nodes(
                    process=process,
                    candidate_nodes=next_nodes,
                    tenant_id=tenant_id,
                    db=db,
                    context=context,
                    visited=visited,
                    origin_node=node,
                )
            )
            continue
        
        # 处理其他节点（保持原有逻辑）
        if node.type == "end":
            if process.state != "canceled":
                process.state = "finished"
                ProcessService._update_submission_status(
                    process=process,
                    status=SubmissionStatus.APPROVED.value,
                    db=db,
                )
            continue
        
        if node.type == "auto":
            # 原有逻辑
            pass
        
        if node.type == "user":
            # 原有逻辑
            pass
```

### 6.4 条件分支评估方法

```python
@staticmethod
def _evaluate_condition_branches(
    node: FlowNode,
    context: Dict[str, object],
    db: Session,
) -> Optional[Dict]:
    """评估条件分支，返回匹配的分支信息"""
    
    if not node.condition_branches:
        return None
    
    branches = node.condition_branches.get("branches", [])
    
    # 按 priority 排序
    sorted_branches = sorted(branches, key=lambda x: x.get("priority", 999))
    
    # 遍历分支，找到第一个匹配的
    for branch in sorted_branches:
        condition = branch.get("condition")
        if not condition:
            continue
        
        # 使用 ConditionEvaluatorV2 评估条件
        if ConditionEvaluatorV2.evaluate(condition, context):
            return {
                "priority": branch.get("priority"),
                "label": branch.get("label"),
                "target_node_id": branch.get("target_node_id"),
            }
    
    # 没有分支匹配，使用默认分支
    default_target_id = node.condition_branches.get("default_target_node_id")
    if default_target_id:
        return {
            "priority": 999,
            "label": "默认分支",
            "target_node_id": default_target_id,
        }
    
    return None
```

### 6.5 流程校验扩展

**修改 FlowService._validate_flow_structure()**：

```python
@staticmethod
def _validate_flow_structure(nodes, routes):
    """扩展校验 CONDITION 节点"""
    
    errors = []
    
    # 原有校验...
    
    # 新增：CONDITION 节点校验
    condition_nodes = [n for n in nodes if n.type == "condition"]
    for cond_node in condition_nodes:
        # 校验：CONDITION 节点至少有 2 条出边
        outgoing_routes = [r for r in routes if r.from_node_id == cond_node.id]
        if len(outgoing_routes) < 2:
            errors.append(f"条件节点 {cond_node.name} 必须至少有 2 条出边")
        
        # 校验：条件分支配置
        if not cond_node.condition_branches:
            errors.append(f"条件节点 {cond_node.name} 缺失条件分支配置")
        else:
            branches = cond_node.condition_branches.get("branches", [])
            if not branches:
                errors.append(f"条件节点 {cond_node.name} 缺失分支定义")
            
            # 校验每个分支的条件表达式
            for idx, branch in enumerate(branches):
                condition = branch.get("condition")
                if not condition:
                    errors.append(f"条件节点 {cond_node.name} 的第 {idx+1} 个分支缺失条件")
                else:
                    is_valid, error_msg = ConditionConverter.validate_tree(condition)
                    if not is_valid:
                        errors.append(f"条件节点 {cond_node.name} 的第 {idx+1} 个分支条件格式错误：{error_msg}")
    
    return errors
```

---

## 七、CC 节点实现详设

### 7.1 CC 节点配置格式

```json
{
  "cc_assignee_type": "user",  // user/group/role/department/position
  "cc_assignee_value": {
    "user_ids": [1001, 1002]
  }
}
```

### 7.2 抄送任务创建

```python
@staticmethod
def _create_cc_task(
    process: ProcessInstance,
    node: FlowNode,
    tenant_id: int,
    db: Session,
) -> List[Task]:
    """创建抄送任务"""
    
    cc_tasks = []
    
    # 解析抄送人
    cc_assignee_type = node.cc_assignee_type
    cc_assignee_value = node.cc_assignee_value or {}
    
    assignee_ids = []
    
    if cc_assignee_type == "user":
        assignee_ids = cc_assignee_value.get("user_ids", [])
    elif cc_assignee_type == "group":
        group_id = cc_assignee_value.get("group_id")
        # 查询组内所有用户
        group_users = db.query(User).filter(
            User.group_id == group_id,
            User.tenant_id == tenant_id,
        ).all()
        assignee_ids = [u.id for u in group_users]
    elif cc_assignee_type == "role":
        role_id = cc_assignee_value.get("role_id")
        # 查询角色下所有用户
        role_users = db.query(User).join(UserRole).filter(
            UserRole.role_id == role_id,
            User.tenant_id == tenant_id,
        ).all()
        assignee_ids = [u.id for u in role_users]
    # ... 其他类型
    
    # 为每个抄送人创建任务
    for assignee_id in assignee_ids:
        task = Task(
            tenant_id=tenant_id,
            process_instance_id=process.id,
            node_id=node.id,
            assignee_user_id=assignee_id,
            task_type="cc",  # 标记为抄送任务
            status="open",
        )
        db.add(task)
        cc_tasks.append(task)
    
    return cc_tasks
```

---

## 八、条件表达式格式统一

### 8.1 转换策略

**方案**：保留设计格式（条件树），后端添加转换层

**流程**：
1. 前端生成条件树格式
2. 保存到数据库（条件树格式）
3. 后端评估时，先转换为 JsonLogic（兼容现有代码）
4. 或直接用条件树格式评估（新的 ConditionEvaluatorV2）

### 8.2 转换实现

**条件树 → JsonLogic**：
```python
def tree_to_jsonlogic(tree: Dict) -> Dict:
    """
    {
      "type": "GROUP",
      "logic": "AND",
      "children": [...]
    }
    →
    {
      "and": [...]
    }
    """
    if tree["type"] == "RULE":
        return {
            OPERATOR_MAP[tree["operator"]]: [
                {"var": tree["fieldKey"]},
                tree["value"]
            ]
        }
    
    if tree["type"] == "GROUP":
        logic_key = tree["logic"].lower()
        children_jsonlogic = [tree_to_jsonlogic(child) for child in tree["children"]]
        return {logic_key: children_jsonlogic}
```

**JsonLogic → 条件树**：
```python
def jsonlogic_to_tree(jsonlogic: Dict) -> Dict:
    """反向转换"""
    # 实现反向转换逻辑
```

### 8.3 条件评估器 V2

**支持条件树格式直接评估**：
```python
class ConditionEvaluatorV2:
    @staticmethod
    def evaluate(condition: Dict, data: Dict) -> bool:
        """直接评估条件树格式"""
        
        if condition["type"] == "RULE":
            return ConditionEvaluatorV2._evaluate_rule(condition, data)
        
        if condition["type"] == "GROUP":
            logic = condition["logic"]
            results = [
                ConditionEvaluatorV2.evaluate(child, data)
                for child in condition["children"]
            ]
            
            if logic == "AND":
                return all(results)
            elif logic == "OR":
                return any(results)
        
        return False
    
    @staticmethod
    def _evaluate_rule(rule: Dict, data: Dict) -> bool:
        """评估单条规则"""
        
        field_key = rule["fieldKey"]
        operator = rule["operator"]
        expected = rule["value"]
        field_type = rule["fieldType"]
        
        actual = data.get(field_key)
        
        return ConditionEvaluatorV2.compare(actual, operator, expected, field_type)
    
    @staticmethod
    def compare(actual, operator, expected, field_type) -> bool:
        """支持所有 15 种运算符"""
        
        # IS_EMPTY / IS_NOT_EMPTY
        if operator == "IS_EMPTY":
            return actual is None or actual == "" or (isinstance(actual, list) and len(actual) == 0)
        
        if operator == "IS_NOT_EMPTY":
            return not (actual is None or actual == "" or (isinstance(actual, list) and len(actual) == 0))
        
        # 其他运算符需要有值
        if actual is None:
            return False
        
        # 类型转换
        if field_type == "NUMBER":
            try:
                actual = float(actual)
                expected = float(expected)
            except (TypeError, ValueError):
                return False
        
        elif field_type in ["DATE", "DATETIME"]:
            # 日期转换
            pass
        
        elif field_type == "MULTI_SELECT":
            if not isinstance(actual, list):
                actual = [actual]
            if not isinstance(expected, list):
                expected = [expected]
        
        # 比较
        if operator == "EQUALS":
            return actual == expected
        elif operator == "NOT_EQUALS":
            return actual != expected
        elif operator == "GREATER_THAN":
            return actual > expected
        elif operator == "GREATER_EQUAL":
            return actual >= expected
        elif operator == "LESS_THAN":
            return actual < expected
        elif operator == "LESS_EQUAL":
            return actual <= expected
        elif operator == "BETWEEN":
            return expected[0] <= actual <= expected[1]
        elif operator == "CONTAINS":
            return str(expected) in str(actual)
        elif operator == "NOT_CONTAINS":
            return str(expected) not in str(actual)
        elif operator == "IN":
            return actual in expected
        elif operator == "NOT_IN":
            return actual not in expected
        elif operator == "HAS_ANY":
            return len(set(actual) & set(expected)) > 0
        elif operator == "HAS_ALL":
            return set(expected).issubset(set(actual))
        
        return False
```

---

## 九、审批操作流程详设

### 9.1 审批通过流程

```
1. 查任务
   - 校验 task.assignee_user_id == current_user
   - 校验 task.status == "open"

2. 查流程实例
   - 校验 instance.state == "running"

3. 更新任务
   - task.status = "completed"
   - task.action = "approve"
   - task.comment = request.comment
   - task.completed_by = current_user
   - task.completed_at = now()

4. 记录操作日志
   - WorkflowOperationLog(
       process_instance_id=instance.id,
       operation_type="APPROVE",
       operator_id=current_user,
       comment=request.comment
     )

5. 推进流程
   - ProcessService.handle_task_completion(task, ...)
   - 根据会签策略决定是否推进
   - 如果推进，调用 advance_from_node()
```

### 9.2 审批驳回流程

```
1. 查任务
   - 校验 task.assignee_user_id == current_user
   - 校验 task.status == "open"

2. 查流程实例
   - 校验 instance.state == "running"

3. 更新任务
   - task.status = "completed"
   - task.action = "reject"
   - task.comment = request.comment
   - task.completed_by = current_user
   - task.completed_at = now()

4. 记录操作日志
   - WorkflowOperationLog(
       process_instance_id=instance.id,
       operation_type="REJECT",
       operator_id=current_user,
       comment=request.comment
     )

5. 处理驳回
   - 查当前节点的 reject_strategy
   - 如果 TO_START：
     - instance.state = "canceled"
     - 取消所有待处理任务
     - 更新 submission.status = "REJECTED"
   - 如果 TO_PREVIOUS：
     - 查找上一个审批节点
     - 重新创建该节点的任务
```

### 9.3 撤回申请流程

```
1. 查流程实例
   - 校验 instance.initiator_id == current_user
   - 校验 instance.state == "running"

2. 取消所有待处理任务
   - UPDATE task SET status = "canceled"
     WHERE process_instance_id = instance.id
     AND status = "open"

3. 更新实例状态
   - instance.state = "canceled"

4. 记录操作日志
   - WorkflowOperationLog(
       process_instance_id=instance.id,
       operation_type="CANCEL",
       operator_id=current_user
     )

5. 更新提交状态
   - submission.status = "CANCELED"
```

