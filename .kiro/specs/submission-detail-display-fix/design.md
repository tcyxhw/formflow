# 提交详情显示修复 Bugfix Design

## Overview

本次修复针对提交详情页面的三个关键问题：
1. 后端在获取可填写表单列表时错误地访问不存在的 `form.category` 属性导致 AttributeError
2. 前端提交详情页面显示了过多不必要的信息（快照信息卡片、流程轨迹卡片、基本信息卡片中的多余字段）
3. 前端表单数据字段标签显示为英文字段名而非中文标签

修复策略：
- 后端：将 `form.category` 改为 `form.category_id`
- 前端：移除快照信息卡片和流程轨迹卡片，精简基本信息卡片字段
- 前端：确保使用 `snapshot_json.field_labels` 中的中文标签显示字段

## Glossary

- **Bug_Condition (C)**: 触发 bug 的条件 - 后端访问 `form.category` 或前端显示过多信息/英文标签
- **Property (P)**: 期望的正确行为 - 后端使用 `form.category_id`，前端仅显示必要信息和中文标签
- **Preservation**: 修复后必须保持不变的现有行为 - 其他表单属性返回、表单数据内容显示、其他页面功能
- **form.category**: Form 模型中不存在的属性（错误访问）
- **form.category_id**: Form 模型中实际存在的外键字段，指向 Category 表
- **FillableFormItem**: `app/schemas/form_workspace.py` 中定义的响应模型，用于返回可填写表单列表
- **snapshot_json.field_labels**: 提交记录中保存的字段中文标签映射，格式为 `{field_key: "中文标签"}`

## Bug Details

### Bug Condition

Bug 在以下四种情况下触发：

1. 当用户访问表单填写页面时，后端在 `form_workspace_service.py` 的 `get_fillable_forms` 和 `get_quick_access_forms` 方法中尝试访问 `form.category` 属性
2. 当用户在提交详情页面查看提交信息时，前端显示了快照信息卡片、流程轨迹卡片以及基本信息卡片中的多余字段
3. 当用户在提交详情页面查看表单数据时，字段标签显示为英文字段名（`data_jsonb` 的 key）而非中文标签
4. **当后端从 schema_json 提取字段标签时，代码使用 `field["name"]` 但实际字段使用 `field["id"]`，导致提取失败**

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type BackendRequest OR FrontendRenderContext
  OUTPUT: boolean
  
  IF input is BackendRequest THEN
    RETURN input.endpoint IN ['/api/v1/form-workspace/fillable-forms', '/api/v1/form-workspace/quick-access']
           AND code_accesses_form_category_attribute
  ELSE IF input is FrontendRenderContext THEN
    RETURN (input.page == 'SubmissionDetailView')
           AND (displays_snapshot_card OR displays_timeline_card OR displays_extra_basic_fields
                OR uses_field_key_as_label)
  END IF
END FUNCTION
```

### Examples

**后端问题示例：**
- 用户访问 `/api/v1/form-workspace/fillable-forms?page=1&size=10`
- 后端在第 143 行执行 `category=form.category`
- 实际行为：抛出 `AttributeError: 'Form' object has no attribute 'category'`
- 预期行为：应使用 `category_id=form.category_id` 并成功返回表单列表

**前端显示过多信息示例：**
- 用户访问提交详情页面 `/submissions/123`
- 实际行为：显示基本信息卡片（包含 8 个字段）、快照信息卡片、流程轨迹卡片
- 预期行为：仅显示基本信息卡片，且只包含提交 ID、表单名称、提交时间三个字段

**前端字段标签英文显示示例：**
- 用户查看表单数据，字段 key 为 `student_name`
- `snapshot_json.field_labels` 中有 `{"student_name": "学生姓名"}`
- 实际行为：标签显示为 `student_name`
- 预期行为：标签显示为 `学生姓名`

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 后端返回可填写表单列表时，应继续返回所有其他表单属性（id、name、status、owner_name、created_at、updated_at、submit_deadline 等）
- 前端提交详情页面显示表单数据内容时，应继续正确显示所有字段的值（包括附件处理逻辑）
- 用户访问其他表单相关页面（表单列表、表单设计器等）时，应继续正常工作不受影响
- 附件列表显示功能应保持不变

**Scope:**
所有不涉及以下内容的输入应完全不受影响：
- 后端：不访问 `form.category` 的其他 API 端点
- 前端：提交详情页面之外的其他页面
- 前端：表单数据内容的值显示逻辑（仅修改标签显示）

## Hypothesized Root Cause

基于 bug 描述和代码分析，最可能的问题原因是：

1. **后端属性访问错误**: 
   - Form 模型中只有 `category_id` 字段（外键），没有 `category` 属性
   - 虽然有 `category_obj` 关系属性（通过 `relationship` 定义），但代码中使用的是 `form.category`
   - `FillableFormItem` schema 中定义的字段名为 `category`，但应该传入 `category_id` 的值

2. **前端过度显示信息**:
   - 组件模板中包含了快照信息卡片（`<n-card title="快照信息">`）
   - 组件模板中包含了流程轨迹卡片（`<n-card class="timeline-card">`）
   - 基本信息卡片中包含了 8 个 `<n-descriptions-item>`，而需求只要求 3 个

3. **前端字段标签显示逻辑**:
   - `displayFields` computed 中使用了 `labels[key] || key` 作为 fallback
   - 可能 `snapshot_json.field_labels` 未正确传递或为空对象
   - 或者代码逻辑本身正确，但数据源有问题

## Correctness Properties

Property 1: Bug Condition - 后端正确访问分类 ID

_For any_ 后端请求到可填写表单列表或快速访问表单列表的 API 端点，修复后的代码 SHALL 使用 `form.category_id` 而非 `form.category`，成功返回表单列表数据而不抛出 AttributeError。

**Validates: Requirements 2.1**

Property 2: Bug Condition - 前端精简显示信息

_For any_ 用户访问提交详情页面的场景，修复后的前端 SHALL 仅显示基本信息卡片（包含提交 ID、表单名称、提交时间三个字段），不显示快照信息卡片和流程轨迹卡片。

**Validates: Requirements 2.2**

Property 3: Bug Condition - 前端显示中文标签

_For any_ 用户在提交详情页面查看表单数据的场景，修复后的前端 SHALL 使用 `snapshot_json.field_labels` 中的中文标签显示字段名称，而非英文字段 key。

**Validates: Requirements 2.3**

Property 4: Preservation - 其他表单属性返回

_For any_ 后端返回可填写表单列表的请求，修复后的代码 SHALL 继续返回所有其他表单属性（id、name、status、owner_name、created_at、updated_at、submit_deadline 等），保持响应结构不变。

**Validates: Requirements 3.1**

Property 5: Preservation - 表单数据内容显示

_For any_ 用户在提交详情页面查看表单数据的场景，修复后的前端 SHALL 继续正确显示所有字段的值，包括附件处理逻辑，仅修改标签显示。

**Validates: Requirements 3.2**

Property 6: Preservation - 其他页面功能

_For any_ 用户访问其他表单相关页面（表单列表、表单设计器等）的场景，修复后的代码 SHALL 继续正常工作，不受本次修复影响。

**Validates: Requirements 3.3**

## Fix Implementation

### Changes Required

假设我们的根本原因分析是正确的：

**File 1**: `backend/app/services/form_workspace_service.py`

**Function**: `get_fillable_forms` (第 40 行开始)

**Specific Changes**:
1. **修改第 143 行**: 将 `category=form.category` 改为 `category=form.category_id`
   - 原代码：`category=form.category,`
   - 修改后：`category=form.category_id,`

2. **修改第 342 行**: 将 `category=form.category` 改为 `category=form.category_id`
   - 原代码：`category=form.category,`
   - 修改后：`category=form.category_id,`

3. **修改第 476 行**: 将分类过滤逻辑从 `form.category` 改为 `form.category_id`
   - 原代码：`return [form for form in forms if form.category == category]`
   - 修改后：`return [form for form in forms if form.category_id == category]`

**File 2**: `backend/app/api/v1/submissions.py`

**Function**: `get_submission` (获取提交详情 API)

**Specific Changes**:
1. **修改第 173-174 行**: 将 `field["name"]` 改为 `field["id"]`
   - 原代码：`if isinstance(field, dict) and "name" in field and "label" in field:`
   - 修改后：`if isinstance(field, dict) and "id" in field and "label" in field:`
   - 原代码：`field_labels[field["name"]] = field["label"]`
   - 修改后：`field_labels[field["id"]] = field["label"]`

**File 3**: `my-app/src/views/submissions/SubmissionDetailView.vue`

**Component**: `SubmissionDetailView`

**Specific Changes**:
1. **移除快照信息卡片**: 删除第 68-82 行的 `<n-card title="快照信息">` 整个卡片
   - 包括其中的 `<n-descriptions>` 和所有 `<n-descriptions-item>`

2. **移除流程轨迹卡片**: 删除第 145-234 行的 `<n-card class="timeline-card">` 整个卡片
   - 包括其中的 `<n-timeline>` 和所有相关逻辑

3. **精简基本信息卡片**: 在第 24-60 行的基本信息卡片中，仅保留以下三个字段：
   - 提交 ID (`<n-descriptions-item label="提交 ID">`)
   - 表单名称 (`<n-descriptions-item label="表单名称">`)
   - 提交时间 (`<n-descriptions-item label="提交时间">`)
   - 删除其他字段：提交人、状态、耗时、来源、IP 地址

4. **确保字段标签显示逻辑正确**: 检查第 272-283 行的 `displayFields` computed
   - 当前代码：`label: labels[key] || key`
   - 确认 `labels` 来自 `submission.value.snapshot_json?.field_labels || {}`
   - 如果逻辑正确但仍显示英文，则需要检查后端返回的 `snapshot_json.field_labels` 数据

5. **移除相关的 computed 和 ref**: 删除不再使用的响应式变量和计算属性
   - `timelineLoading`、`timelineError`、`timeline` 等与流程轨迹相关的变量
   - `loadTimeline`、`resetTimelineState` 等相关函数
   - 流程轨迹相关的 computed 属性

## Testing Strategy

### Validation Approach

测试策略遵循两阶段方法：首先在未修复的代码上运行测试以暴露 bug 的反例，然后验证修复后的代码能正确工作并保持现有行为不变。

### Exploratory Bug Condition Checking

**Goal**: 在实施修复之前，在未修复的代码上暴露 bug 的反例。确认或反驳根本原因分析。如果反驳，需要重新假设。

**Test Plan**: 编写测试模拟访问可填写表单列表 API 和渲染提交详情页面，断言会出现 AttributeError 或显示过多信息。在未修复的代码上运行这些测试以观察失败并理解根本原因。

**Test Cases**:
1. **后端分类访问测试**: 调用 `get_fillable_forms` API，断言会抛出 AttributeError（在未修复代码上会失败）
2. **前端快照卡片显示测试**: 渲染提交详情页面，断言快照信息卡片存在（在未修复代码上会通过，修复后应失败）
3. **前端流程轨迹卡片显示测试**: 渲染提交详情页面，断言流程轨迹卡片存在（在未修复代码上会通过，修复后应失败）
4. **前端基本信息字段数量测试**: 渲染提交详情页面，断言基本信息卡片有 8 个字段（在未修复代码上会通过，修复后应只有 3 个）
5. **前端字段标签英文显示测试**: 渲染提交详情页面，检查字段标签是否为英文 key（在未修复代码上可能通过）

**Expected Counterexamples**:
- 后端访问 `form.category` 时抛出 AttributeError
- 前端显示了快照信息卡片和流程轨迹卡片
- 前端基本信息卡片显示了 8 个字段而非 3 个
- 前端字段标签显示为英文 key 而非中文标签
- 可能的原因：属性名错误、模板包含过多元素、标签映射未正确使用

### Fix Checking

**Goal**: 验证对于所有触发 bug 条件的输入，修复后的函数产生预期行为。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  IF input is BackendRequest THEN
    result := get_fillable_forms_fixed(input)
    ASSERT result contains form list with category_id
    ASSERT no AttributeError thrown
  ELSE IF input is FrontendRenderContext THEN
    rendered := render_submission_detail_fixed(input)
    ASSERT rendered does NOT contain snapshot card
    ASSERT rendered does NOT contain timeline card
    ASSERT rendered basic info card has exactly 3 fields
    ASSERT rendered field labels are in Chinese
  END IF
END FOR
```

### Preservation Checking

**Goal**: 验证对于所有不触发 bug 条件的输入，修复后的函数产生与原始函数相同的结果。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  IF input is BackendRequest THEN
    ASSERT get_fillable_forms_original(input) = get_fillable_forms_fixed(input)
    ASSERT all other form attributes are returned
  ELSE IF input is FrontendRenderContext THEN
    ASSERT form data values display logic unchanged
    ASSERT attachment handling logic unchanged
    ASSERT other pages functionality unchanged
  END IF
END FOR
```

**Testing Approach**: 推荐使用基于属性的测试进行保持性检查，因为：
- 它自动生成跨输入域的许多测试用例
- 它能捕获手动单元测试可能遗漏的边缘情况
- 它为所有非 bug 输入提供强有力的保证，确保行为不变

**Test Plan**: 首先在未修复的代码上观察其他 API 端点和页面的行为，然后编写基于属性的测试捕获该行为。

**Test Cases**:
1. **其他表单属性返回保持性**: 验证修复后返回的表单列表包含所有其他属性（id、name、status 等）
2. **表单数据值显示保持性**: 验证修复后表单数据的值显示逻辑保持不变
3. **附件处理保持性**: 验证修复后附件列表和附件字段的处理逻辑保持不变
4. **其他页面功能保持性**: 验证修复后其他表单相关页面继续正常工作

### Unit Tests

**后端测试**:
- 测试 `get_fillable_forms` 方法能正确返回表单列表，使用 `category_id`
- 测试 `get_quick_access_forms` 方法能正确返回快速访问表单列表
- 测试分类过滤逻辑 `_apply_category_filter` 使用 `category_id` 进行过滤
- 测试边缘情况：表单没有分类（`category_id` 为 NULL）

**前端测试**:
- 测试提交详情页面仅显示基本信息卡片
- 测试基本信息卡片只包含 3 个字段
- 测试字段标签使用中文显示
- 测试附件列表继续正常显示

### Property-Based Tests

**后端测试**:
- 生成随机表单数据，验证 API 返回的 `category` 字段值等于 `form.category_id`
- 生成随机分类过滤条件，验证过滤逻辑使用 `category_id` 正确工作
- 测试所有其他表单属性在修复前后返回值相同

**前端测试**:
- 生成随机提交数据，验证页面不显示快照信息卡片和流程轨迹卡片
- 生成随机字段标签映射，验证字段标签始终使用中文显示
- 测试表单数据值显示逻辑在修复前后保持一致

### Integration Tests

**后端集成测试**:
- 测试完整的表单填写流程：获取可填写表单列表 -> 选择表单 -> 填写提交
- 测试快速访问功能：添加快速访问 -> 获取快速访问列表
- 测试分类筛选功能在整个流程中正常工作

**前端集成测试**:
- 测试完整的提交查看流程：提交列表 -> 点击查看详情 -> 显示精简信息
- 测试表单数据显示：包含各种字段类型（文本、数字、附件等）
- 测试从提交详情页面返回到列表页面的导航
