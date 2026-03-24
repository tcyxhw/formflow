# 条件设置修复验证清单

## 前端验证清单

### 类型定义验证 (my-app/src/types/condition.ts)

- [ ] OperatorConfig 接口包含 'MULTI' valueType
- [ ] DATE 类型包含 NOT_EQUALS, GREATER_EQUAL, LESS_EQUAL
- [ ] DATETIME 类型包含 NOT_EQUALS, GREATER_EQUAL, LESS_EQUAL
- [ ] SINGLE_SELECT 的 IN/NOT_IN valueType 为 'MULTI'
- [ ] MULTI_SELECT 的 HAS_ANY/HAS_ALL valueType 为 'MULTI'
- [ ] MULTI_SELECT 不包含 NOT_CONTAINS

**验证命令**:
```bash
cd my-app
npm run type-check
```

### ValueInput 组件验证 (my-app/src/components/flow-configurator/ValueInput.vue)

- [ ] 支持 DATETIME 日期时间选择器
- [ ] 多值运算符自动检测 (IN, NOT_IN, HAS_ANY, HAS_ALL)
- [ ] 支持人员多选输入 (userMulti)
- [ ] 支持部门多选输入 (departmentMulti)
- [ ] 日期范围选择正确处理

**验证步骤**:
1. 打开条件构造器
2. 选择 SINGLE_SELECT 字段
3. 选择 IN 运算符
4. 验证显示多选控件

### ConditionRule 组件验证 (my-app/src/components/flow-configurator/ConditionRule.vue)

- [ ] BETWEEN 值校验: 检查大小关系
- [ ] DATE 格式校验: YYYY-MM-DD 格式
- [ ] DATETIME 格式校验: ISO 格式
- [ ] NUMBER 值校验: 有效数字
- [ ] 多值数组校验: 至少一个元素

**验证步骤**:
1. 选择 NUMBER 字段，BETWEEN 运算符
2. 输入 min=100, max=50
3. 验证错误提示: "最小值不能大于最大值"

---

## 后端验证清单

### 条件评估器验证 (backend/app/services/condition_evaluator_v2.py)

- [ ] IN 运算符正确处理列表
- [ ] NOT_IN 运算符正确处理列表
- [ ] HAS_ANY 运算符正确处理多值
- [ ] HAS_ALL 运算符正确处理多值
- [ ] DATETIME 类型转换正确
- [ ] USER 类型转换为字符串
- [ ] DEPARTMENT 类型转换为字符串
- [ ] evaluate 函数支持 system_fields 参数
- [ ] evaluate_condition_tree 便利函数支持 system_fields

**验证命令**:
```bash
cd backend
pytest tests/test_condition_evaluator_v2.py -v
```

### 条件校验器验证 (backend/app/services/condition_validator.py)

- [ ] 模块成功导入
- [ ] ConditionValidator 类存在
- [ ] validate_condition_tree 方法存在
- [ ] validate_rule 方法存在
- [ ] validate_group 方法存在
- [ ] validate_branches_config 方法存在
- [ ] FIELD_OPERATOR_MAP 包含所有字段类型

**验证命令**:
```bash
cd backend
python -c "from app.services.condition_validator import ConditionValidator; print('✓ 导入成功')"
```

---

## 集成测试清单

### 前端集成测试

**测试场景1: DATE 字段完整流程**
```
1. 打开条件构造器
2. 选择 DATE 字段
3. 验证运算符列表包含: EQUALS, NOT_EQUALS, GREATER_THAN, GREATER_EQUAL, LESS_THAN, LESS_EQUAL, BETWEEN, IS_EMPTY, IS_NOT_EMPTY
4. 选择 GREATER_EQUAL 运算符
5. 验证显示日期选择器
6. 选择日期 2024-12-01
7. 验证条件正确保存
```

**测试场景2: SINGLE_SELECT IN 运算符**
```
1. 打开条件构造器
2. 选择 SINGLE_SELECT 字段
3. 选择 IN 运算符
4. 验证显示多选控件
5. 选择多个选项
6. 验证条件正确保存为数组
```

**测试场景3: BETWEEN 校验**
```
1. 选择 NUMBER 字段，BETWEEN 运算符
2. 输入 min=100, max=50
3. 验证显示错误: "最小值不能大于最大值"
4. 修改为 min=50, max=100
5. 验证错误消失
```

### 后端集成测试

**测试场景1: IN 运算符评估**
```python
condition = {
    "type": "RULE",
    "fieldKey": "status",
    "fieldType": "SINGLE_SELECT",
    "operator": "IN",
    "value": ["pending", "approved"]
}
data = {"status": "pending"}
result = ConditionEvaluatorV2.evaluate(condition, data)
assert result == True, "IN 运算符应该返回 True"
```

**测试场景2: HAS_ANY 运算符评估**
```python
condition = {
    "type": "RULE",
    "fieldKey": "tags",
    "fieldType": "MULTI_SELECT",
    "operator": "HAS_ANY",
    "value": ["urgent", "important"]
}
data = {"tags": ["urgent", "normal"]}
result = ConditionEvaluatorV2.evaluate(condition, data)
assert result == True, "HAS_ANY 应该返回 True"
```

**测试场景3: 系统字段注入**
```python
condition = {
    "type": "RULE",
    "fieldKey": "sys_submitter",
    "fieldType": "USER",
    "operator": "EQUALS",
    "value": 101
}
system_fields = {"sys_submitter": 101}
result = ConditionEvaluatorV2.evaluate(condition, {}, system_fields)
assert result == True, "系统字段应该正确注入"
```

**测试场景4: 条件校验**
```python
config = {
    "branches": [
        {
            "priority": 1,
            "label": "分支1",
            "target_node_id": 999,  # 不存在
            "condition": {"type": "GROUP", "logic": "AND", "children": []}
        }
    ],
    "default_target_node_id": 1
}
errors = ConditionValidator.validate_branches_config(
    config, {}, [1, 2, 3]
)
assert any("999" in err for err in errors), "应该检测到不存在的节点"
```

---

## 性能验证清单

- [ ] 前端类型检查通过 (npm run type-check)
- [ ] 前端代码检查通过 (npm run lint)
- [ ] 后端代码检查通过 (pytest)
- [ ] 没有新增的 console.error 或 console.warn
- [ ] 没有新增的 Python 警告

---

## 文档验证清单

- [ ] 修改文件清单完整
- [ ] 代码注释清晰
- [ ] 函数文档字符串完整
- [ ] 类型注解完整
- [ ] 错误消息用户友好

---

## 部署前检查清单

### 前端部署检查

```bash
# 1. 类型检查
cd my-app
npm run type-check

# 2. 代码检查
npm run lint

# 3. 构建测试
npm run build

# 4. 验证构建产物
ls -la dist/
```

### 后端部署检查

```bash
# 1. 导入检查
cd backend
python -c "from app.services.condition_validator import ConditionValidator; print('✓')"
python -c "from app.services.condition_evaluator_v2 import ConditionEvaluatorV2; print('✓')"

# 2. 运行测试
pytest tests/test_condition_evaluator_v2.py -v

# 3. 启动服务
uvicorn app.main:app --reload --port 8000
```

---

## 验证完成标准

✅ 所有前端验证项通过
✅ 所有后端验证项通过
✅ 所有集成测试通过
✅ 性能验证通过
✅ 文档验证通过
✅ 部署前检查通过

---

## 已知限制

1. **人员/部门选择器**: 当前使用简化的文本输入，建议后续集成真实的选择器组件
2. **DATE_BEFORE_NOW/DATE_AFTER_NOW**: 这些运算符是业务扩展，超出设计范围
3. **多语言支持**: 错误消息目前仅支持中文

---

## 后续改进建议

1. **增强人员/部门选择**
   - 集成真实的人员/部门选择器组件
   - 支持搜索和过滤

2. **增强日期选择**
   - 支持相对日期（如"今天"、"本周"等）
   - 支持日期快捷选择

3. **增强条件预览**
   - 显示更详细的条件描述
   - 支持条件的自然语言表达

4. **增强错误处理**
   - 更详细的错误信息
   - 错误恢复建议

5. **性能优化**
   - 缓存字段选项
   - 优化大型条件树的评估
