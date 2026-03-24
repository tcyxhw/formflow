# 流程配置器表单 Schema 加载错误修复

## 问题描述

当用户打开流程配置页面时，后端日志出现错误：
```
"Get form detail error: 404: 表单不存在: id=13"
```

## 根本原因

在 `my-app/src/views/flow/Configurator.vue` 的 `loadFlowDraft` 函数中，存在 ID 混淆问题：

**错误代码**：
```typescript
const formDetail = await getFormDetail(store.flowDefinitionId || id)
```

**问题**：
- `store.flowDefinitionId` 是**流程定义 ID**（FlowDefinition）
- `getFormDetail()` 需要的是**表单 ID**（Form）
- 这两个 ID 是完全不同的实体
- 使用流程定义 ID 去查询表单，导致 404 错误

## 解决方案

修改 `loadFlowDraft` 函数，从流程定义的返回数据中提取正确的表单 ID：

**修正代码**：
```typescript
const loadFlowDraft = async (id: number) => {
  try {
    const result = await store.loadDefinition(id)
    
    // 加载关联的表单schema
    try {
      const formId = result.detail?.definition?.form_id
      if (formId) {
        const formDetail = await getFormDetail(formId)
        formSchema.value = formDetail.schema_json
      }
    } catch (error) {
      console.warn('Failed to load form schema:', error)
      // 不影响流程配置的加载
    }
  } catch (error) {
    message.error(resolveErrorMessage(error, '加载流程失败'))
  }
}
```

## 关键改动

1. **保存返回值**：`const result = await store.loadDefinition(id)`
2. **提取表单 ID**：`const formId = result.detail?.definition?.form_id`
3. **条件检查**：`if (formId)` 确保表单 ID 存在
4. **使用正确 ID**：`await getFormDetail(formId)`

## 数据流向

```
流程配置页面
    ↓
loadFlowDraft(flowDefinitionId)
    ↓
store.loadDefinition(flowDefinitionId)
    ↓
getFlowDefinitionDetail(flowDefinitionId)  ← 返回 FlowDefinitionDetailResponse
    ↓
result.detail.definition.form_id  ← 提取表单 ID
    ↓
getFormDetail(formId)  ← 使用正确的表单 ID
    ↓
formSchema.value = formDetail.schema_json  ← 加载表单 schema
```

## 修改文件

- `my-app/src/views/flow/Configurator.vue` - `loadFlowDraft` 函数

## 验证

修改后，打开流程配置页面时：
1. ✅ 流程定义加载成功
2. ✅ 表单 schema 加载成功（不再出现 404 错误）
3. ✅ 条件构建器可以正确引用表单字段

## 影响范围

- 仅影响流程配置页面的表单 schema 加载
- 不影响其他功能
- 向后兼容（如果表单 ID 不存在，会优雅降级）
