# 任务 3.2 前端 API 接口实现总结

## 任务概述
实现前端表单字段 API 接口 (`getFormFields()`)，并在条件构造器中集成使用。

## 完成情况

### ✅ 3.2.1 在 `my-app/src/api/form.ts` 添加 `getFormFields()` 接口

**实现内容：**
1. 添加了 `FormFieldsResponse` 类型导入到 `form.ts`
2. 实现了 `getFormFields(formId: number)` 函数
3. 函数调用后端 API 端点：`GET /api/v1/forms/{formId}/fields`
4. 返回类型为 `Promise<Response<FormFieldsResponse>>`

**代码位置：** `my-app/src/api/form.ts`

```typescript
/**
 * 获取表单字段列表
 * 用于条件构造器等功能获取表单的所有字段定义
 */
export const getFormFields = (formId: number): Promise<Response<FormFieldsResponse>> => {
  return request.get(`${FORM_BASE_PATH}/${formId}/fields`)
}
```

### ✅ 3.2.2 在条件构造器中集成

**实现内容：**

#### 1. 前端类型定义 (`my-app/src/types/form.ts`)
- 添加 `FormFieldOption` 接口
- 添加 `FormField` 接口
- 添加 `FormFieldsResponse` 接口

#### 2. 条件构造器 V2 (`my-app/src/components/flow-configurator/ConditionBuilderV2.vue`)
- 添加 `formId` 属性支持
- 实现 `loadFormFields()` 异步函数
- 在组件挂载时自动加载字段
- 监听 `formId` 变化，自动重新加载
- 优先使用 API 加载的字段，备用 `formSchema`
- 添加字段类型映射逻辑

**关键特性：**
- 支持动态加载表单字段
- 支持字段缓存（通过 `apiFields` ref）
- 支持错误处理（加载失败时降级到 `formSchema`）
- 支持字段类型自动映射

#### 3. 条件节点编辑器 (`my-app/src/components/flow-configurator/ConditionNodeEditor.vue`)
- 添加 `formId` 属性
- 传递 `formId` 给 `ConditionBuilderV2`

#### 4. 流程节点检查器 (`my-app/src/components/flow-configurator/FlowNodeInspector.vue`)
- 添加 `formId` 属性
- 传递 `formId` 给 `ConditionNodeEditor`

#### 5. 流程配置器 (`my-app/src/views/flow/Configurator.vue`)
- 添加 `formId` ref 来存储表单 ID
- 在 `loadFlowDraft()` 中提取并保存 `formId`
- 传递 `formId` 给 `FlowNodeInspector`

## 技术实现细节

### 字段类型映射
实现了从后端字段类型到条件构造器字段类型的映射：
- `text` / `textarea` → `TEXT`
- `number` → `NUMBER`
- `select` / `radio` → `SINGLE_SELECT`
- `multiselect` / `checkbox` → `MULTI_SELECT`
- `date` → `DATE`
- `datetime` → `DATETIME`
- `user` → `USER`
- `department` → `DEPARTMENT`
- `string` → `TEXT`

### 错误处理
- API 加载失败时，自动降级到 `formSchema`
- 错误信息记录到控制台
- 用户体验不受影响

### 性能优化
- 字段列表缓存在 `apiFields` ref 中
- 避免重复加载相同的字段
- 支持增量更新

## 测试覆盖

### 单元测试 (`my-app/src/api/__tests__/form.test.ts`)
✅ 5 个测试全部通过：
- `getFormFields` 调用正确的 API 端点
- 返回包含表单字段和系统字段的响应
- 处理包含选项的字段
- 其他表单 API 测试

### 集成测试 (`my-app/src/components/flow-configurator/__tests__/ConditionBuilderV2Integration.test.ts`)
✅ 6 个测试全部通过：
- 挂载时加载表单字段
- `formId` 变化时重新加载字段
- 没有 `formId` 时使用 `formSchema`
- 优先使用 API 加载的字段
- 处理 API 加载失败
- 正确映射 API 返回的字段类型

## 数据流

```
Configurator.vue (获取 formId)
    ↓
FlowNodeInspector (接收 formId)
    ↓
ConditionNodeEditor (接收 formId)
    ↓
ConditionBuilderV2 (调用 getFormFields API)
    ↓
后端 API: GET /api/v1/forms/{formId}/fields
    ↓
返回 FormFieldsResponse (包含表单字段和系统字段)
    ↓
条件构造器使用字段列表进行条件配置
```

## 后端 API 信息

**端点：** `GET /api/v1/forms/{formId}/fields`

**响应格式：**
```json
{
  "form_id": 123,
  "form_name": "招待费申请",
  "fields": [
    {
      "key": "amount",
      "name": "金额",
      "type": "number",
      "description": "申请金额",
      "required": true,
      "options": null,
      "props": {}
    }
  ],
  "system_fields": [
    {
      "key": "sys_submitter",
      "name": "提交人",
      "type": "string",
      "description": "表单提交人",
      "required": false,
      "options": null,
      "props": {}
    }
  ]
}
```

## 文件修改清单

### 新增文件
- `my-app/src/api/__tests__/form.test.ts` - 表单 API 单元测试
- `my-app/src/components/flow-configurator/__tests__/ConditionBuilderV2Integration.test.ts` - 条件构造器集成测试

### 修改文件
1. `my-app/src/types/form.ts` - 添加表单字段相关类型
2. `my-app/src/api/form.ts` - 添加 `getFormFields()` 函数
3. `my-app/src/components/flow-configurator/ConditionBuilderV2.vue` - 集成 API 加载
4. `my-app/src/components/flow-configurator/ConditionNodeEditor.vue` - 传递 formId
5. `my-app/src/components/flow-configurator/FlowNodeInspector.vue` - 传递 formId
6. `my-app/src/views/flow/Configurator.vue` - 提取并传递 formId

## 验收标准

✅ API 接口可正常调用
✅ 返回正确的字段列表
✅ 包含系统字段
✅ 前端可正确使用
✅ 条件构造器可动态加载字段
✅ 支持字段缓存
✅ 错误处理完善
✅ 单元测试通过
✅ 集成测试通过

## 使用示例

### 在条件构造器中使用
```vue
<ConditionBuilderV2
  :model-value="condition"
  :form-id="formId"
  :form-schema="formSchema"
  @update:model-value="updateCondition"
/>
```

### 直接调用 API
```typescript
import { getFormFields } from '@/api/form'

const loadFields = async () => {
  try {
    const response = await getFormFields(123)
    console.log(response.data.fields)
    console.log(response.data.system_fields)
  } catch (error) {
    console.error('Failed to load fields:', error)
  }
}
```

## 后续优化建议

1. **字段缓存优化**：可以使用 Pinia 全局状态管理缓存字段列表
2. **性能优化**：可以添加字段列表的分页加载
3. **搜索功能**：可以在条件构造器中添加字段搜索功能
4. **字段分组**：可以按类型或分类对字段进行分组显示
5. **权限控制**：可以根据用户权限过滤可用字段

## 总结

任务 3.2 已完全实现，前端 API 接口 `getFormFields()` 已成功集成到条件构造器中。系统现在可以动态加载表单字段，为用户提供更好的条件配置体验。所有测试均已通过，代码质量符合项目规范。
