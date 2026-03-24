# 审批流程配置UX缺陷修复设计文档

## 概述

本设计文档针对审批流程配置界面的两个UX缺陷提出改进方案：

1. **缺陷1：条件设置空间受限** - 条件编辑在右侧面板中空间太小，难以配置复杂条件
   - 解决方案：将条件编辑从面板内嵌改为独立模态框，提供更大的操作空间

2. **缺陷2：开始/结束节点显示不必要的配置** - 所有节点类型显示相同的配置选项
   - 解决方案：根据节点类型条件渲染配置字段，开始/结束节点仅显示基本信息

这两个改进都遵循最小化代码改动的原则，通过条件渲染和模态框集成实现。

---

## 缺陷1：条件设置空间受限

### 问题分析

**当前状态**：
- ConditionNodeEditor 在 FlowNodeInspector 的右侧面板中内嵌显示
- 面板宽度固定（通常 300-400px），空间受限
- 用户难以看到完整的条件表达式
- 复杂条件的编辑体验不佳

**根本原因**：
- ConditionNodeEditor 设计为面板内容，没有考虑模态框场景
- 条件编辑和节点配置混在一起，竞争空间

### 解决方案

#### 1.1 交互流程改进

```
用户选择条件节点
    ↓
FlowNodeInspector 显示条件节点配置
    ↓
用户点击"编辑条件"按钮
    ↓
弹出独立模态框（宽度 1000px+）
    ↓
ConditionNodeEditor 在模态框中全屏显示
    ↓
用户编辑条件
    ↓
点击"保存"或"取消"
    ↓
模态框关闭，数据更新或丢弃
```

#### 1.2 组件改动清单

**FlowNodeInspector.vue**：
- 添加 `showConditionModal` 状态
- 添加 `editingConditionBranches` 状态
- 将 ConditionNodeEditor 从 form 中移除
- 添加"编辑条件"按钮，点击时打开模态框
- 添加模态框，包含 ConditionNodeEditor

**ConditionNodeEditor.vue**：
- 无需改动（保持现有功能）
- 在模态框中使用时自动获得更大空间

#### 1.3 UI改动方案

**FlowNodeInspector 中的条件节点配置**：

```
┌─────────────────────────────────────────┐
│ 节点属性                                 │
├─────────────────────────────────────────┤
│                                         │
│ 节点名称                                │
│ [输入框]                                │
│                                         │
│ 节点类型                                │
│ [条件分支]                              │
│                                         │
│ ┌─────────────────────────────────────┐│
│ │ 条件分支配置                        ││
│ │ 当前有 2 个分支                     ││
│ │                                     ││
│ │ [编辑条件] [预览]                   ││
│ └─────────────────────────────────────┘│
│                                         │
└─────────────────────────────────────────┘
```

**模态框设计**：

```
┌──────────────────────────────────────────────────────────────────┐
│ 编辑条件表达式                                              [×]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 条件配置                                                   │ │
│  │ 通过可视化界面配置路由条件                                 │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  [ConditionNodeEditor 完整显示]                           │ │
│  │                                                            │ │
│  │  - 分支列表（完整显示）                                   │ │
│  │  - 默认路由配置                                           │ │
│  │  - 条件编辑模态框（嵌套）                                 │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [取消]  [保存]                                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### 1.4 数据流改动

**保存流程**：
```
用户在模态框中编辑条件
    ↓
点击"保存"按钮
    ↓
ConditionNodeEditor 触发 update:modelValue 事件
    ↓
FlowNodeInspector 接收新的 condition_branches 数据
    ↓
FlowNodeInspector 触发 update-node 事件，发送给父组件
    ↓
父组件更新流程数据
    ↓
模态框关闭
```

**取消流程**：
```
用户在模态框中编辑条件
    ↓
点击"取消"按钮
    ↓
FlowNodeInspector 丢弃临时数据
    ↓
模态框关闭
    ↓
条件数据保持不变
```

#### 1.5 模态框配置

| 属性 | 值 | 说明 |
|------|-----|------|
| 标题 | "编辑条件表达式" | 清晰的操作指示 |
| 宽度 | 1000px | 为条件编辑提供充足空间 |
| 高度 | 自适应（最大 80vh） | 避免超出视口 |
| 预设 | dialog | 使用对话框预设 |
| 可关闭 | false | 防止误操作 |
| 遮罩可关闭 | false | 强制用户选择保存或取消 |
| 正按钮 | "保存" | 保存条件数据 |
| 负按钮 | "取消" | 丢弃临时数据 |

#### 1.6 代码改动示例

**FlowNodeInspector.vue 中的改动**：

```vue
<script setup>
// 新增状态
const showConditionModal = ref(false)
const editingConditionBranches = ref<ConditionBranchesConfig | null>(null)

// 打开条件编辑模态框
const openConditionModal = () => {
  editingConditionBranches.value = node.value?.condition_branches ?? null
  showConditionModal.value = true
}

// 保存条件
const saveCondition = () => {
  if (editingConditionBranches.value) {
    emitPatch({ condition_branches: editingConditionBranches.value })
  }
  showConditionModal.value = false
}

// 取消编辑
const cancelCondition = () => {
  editingConditionBranches.value = null
  showConditionModal.value = false
}
</script>

<template>
  <!-- 条件节点配置 -->
  <div v-if="node.type === 'condition'" class="condition-config">
    <div class="config-header">
      <span>条件分支配置</span>
      <span class="branch-count">当前有 {{ node.condition_branches?.branches.length ?? 0 }} 个分支</span>
    </div>
    <div class="config-actions">
      <n-button type="primary" @click="openConditionModal">
        编辑条件
      </n-button>
      <n-button v-if="node.condition_branches" text>
        预览
      </n-button>
    </div>
  </div>

  <!-- 条件编辑模态框 -->
  <n-modal
    v-model:show="showConditionModal"
    title="编辑条件表达式"
    preset="dialog"
    size="large"
    :mask-closable="false"
    @positive-click="saveCondition"
    @negative-click="cancelCondition"
  >
    <ConditionNodeEditor
      :model-value="editingConditionBranches"
      :all-nodes="allNodes"
      :form-schema="formSchema"
      :form-id="formId"
      :disabled="disabled"
      @update:model-value="(val) => (editingConditionBranches = val)"
    />
  </n-modal>
</template>
```

---

## 缺陷2：开始/结束节点显示不必要的配置

### 问题分析

**当前状态**：
- FlowNodeInspector 对所有节点类型显示相同的配置字段
- 开始节点（start）显示负责人类型、审批策略等不相关的配置
- 结束节点（end）显示负责人类型、审批策略等不相关的配置
- 用户困惑，UI 显得冗余

**根本原因**：
- FlowNodeInspector 没有根据节点类型进行条件渲染
- 所有配置字段都无条件显示

### 解决方案

#### 2.1 节点类型配置映射

| 节点类型 | 显示字段 | 隐藏字段 |
|---------|---------|---------|
| start | 节点名称、节点类型 | 负责人类型、审批策略、SLA、允许代理、驳回策略、自动审批 |
| end | 节点名称、节点类型 | 负责人类型、审批策略、SLA、允许代理、驳回策略、自动审批 |
| user | 节点名称、节点类型、负责人类型、审批策略、SLA、允许代理、驳回策略、自动审批 | 无 |
| auto | 节点名称、节点类型、负责人类型、审批策略、SLA、允许代理、驳回策略、自动审批 | 无 |
| condition | 节点名称、节点类型、条件分支配置 | 负责人类型、审批策略、SLA、允许代理、驳回策略、自动审批 |

#### 2.2 UI改动方案

**开始节点配置**：

```
┌─────────────────────────────────────────┐
│ 节点属性                                 │
├─────────────────────────────────────────┤
│                                         │
│ 节点名称                                │
│ [输入框]                                │
│                                         │
│ 节点类型                                │
│ [开始]                                  │
│                                         │
│ ℹ️ 开始节点是流程的入口点，无需配置    │
│    审批相关参数。                       │
│                                         │
└─────────────────────────────────────────┘
```

**结束节点配置**：

```
┌─────────────────────────────────────────┐
│ 节点属性                                 │
├─────────────────────────────────────────┤
│                                         │
│ 节点名称                                │
│ [输入框]                                │
│                                         │
│ 节点类型                                │
│ [结束]                                  │
│                                         │
│ ℹ️ 结束节点是流程的终点，无需配置      │
│    审批相关参数。                       │
│                                         │
└─────────────────────────────────────────┘
```

**人工审批节点配置**（保持不变）：

```
┌─────────────────────────────────────────┐
│ 节点属性                                 │
├─────────────────────────────────────────┤
│                                         │
│ 节点名称                                │
│ [输入框]                                │
│                                         │
│ 节点类型                                │
│ [人工审批]                              │
│                                         │
│ 负责人类型                              │
│ [选择框]                                │
│                                         │
│ 审批策略                                │
│ [选择框]                                │
│                                         │
│ ... (其他审批配置)                      │
│                                         │
└─────────────────────────────────────────┘
```

#### 2.3 组件改动清单

**FlowNodeInspector.vue**：
- 添加 `shouldShowApprovalConfig()` 方法，根据节点类型判断是否显示审批配置
- 添加 `shouldShowConditionConfig()` 方法，根据节点类型判断是否显示条件配置
- 使用 `v-if` 条件渲染审批相关字段
- 为开始/结束节点添加信息提示

#### 2.4 条件渲染逻辑

```typescript
// 是否显示审批相关配置
const shouldShowApprovalConfig = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'user' || nodeType === 'auto'
}

// 是否显示条件配置
const shouldShowConditionConfig = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'condition'
}

// 是否显示基本信息提示
const shouldShowBasicInfoHint = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'start' || nodeType === 'end'
}
```

#### 2.5 代码改动示例

**FlowNodeInspector.vue 中的改动**：

```vue
<script setup>
const shouldShowApprovalConfig = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'user' || nodeType === 'auto'
}

const shouldShowConditionConfig = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'condition'
}

const shouldShowBasicInfoHint = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'start' || nodeType === 'end'
}
</script>

<template>
  <div v-if="node" class="inspector-body">
    <n-form label-placement="left" label-width="88" size="small">
      <!-- 基本信息 -->
      <n-form-item label="节点名称">
        <n-input
          :value="node.name"
          placeholder="请输入节点名称"
          :disabled="disabled"
          @update:value="(val) => emitPatch({ name: val })"
        />
      </n-form-item>

      <n-form-item label="节点类型">
        <n-select
          :value="node.type"
          :options="nodeTypeOptions"
          :disabled="disabled"
          @update:value="(val) => emitPatch({ type: val as FlowNodeType })"
        />
      </n-form-item>

      <!-- 开始/结束节点提示 -->
      <n-alert
        v-if="shouldShowBasicInfoHint(node.type)"
        type="info"
        :bordered="false"
      >
        {{ node.type === 'start' ? '开始节点是流程的入口点，无需配置审批相关参数。' : '结束节点是流程的终点，无需配置审批相关参数。' }}
      </n-alert>

      <!-- 审批相关配置 -->
      <template v-if="shouldShowApprovalConfig(node.type)">
        <n-form-item label="负责人类型">
          <n-select
            :value="node.assignee_type"
            :options="assigneeOptions"
            :disabled="disabled"
            placeholder="暂未指定"
            @update:value="(val) => emitPatch({ assignee_type: val as FlowAssigneeType })"
          />
        </n-form-item>

        <n-form-item label="审批策略">
          <n-select
            :value="node.approve_policy"
            :options="approvePolicyOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ approve_policy: val as FlowApprovePolicy })"
          />
        </n-form-item>

        <!-- ... 其他审批配置 ... -->
      </template>

      <!-- 条件配置 -->
      <template v-if="shouldShowConditionConfig(node.type)">
        <n-divider>条件分支配置</n-divider>
        
        <div class="condition-config">
          <div class="config-header">
            <span>条件分支配置</span>
            <span class="branch-count">当前有 {{ node.condition_branches?.branches.length ?? 0 }} 个分支</span>
          </div>
          <div class="config-actions">
            <n-button type="primary" @click="openConditionModal">
              编辑条件
            </n-button>
          </div>
        </div>
      </template>
    </n-form>
  </div>
</template>

<style scoped>
.condition-config {
  padding: 12px;
  background: #f9fbfc;
  border-radius: 6px;
  border: 1px solid #e0e5ec;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
}

.branch-count {
  color: #6b7385;
  font-size: 12px;
}

.config-actions {
  display: flex;
  gap: 8px;
}
</style>
```

---

## 数据流改动

### 缺陷1的数据流

```
FlowNodeInspector
  ├─ node (条件节点)
  ├─ showConditionModal (状态)
  ├─ editingConditionBranches (临时数据)
  │
  ├─ openConditionModal()
  │  └─ 复制 node.condition_branches 到 editingConditionBranches
  │  └─ 打开模态框
  │
  ├─ saveCondition()
  │  └─ 调用 emitPatch({ condition_branches: editingConditionBranches })
  │  └─ 关闭模态框
  │
  └─ cancelCondition()
     └─ 清空 editingConditionBranches
     └─ 关闭模态框
```

### 缺陷2的数据流

```
FlowNodeInspector
  ├─ node (任意节点类型)
  │
  ├─ shouldShowApprovalConfig(node.type)
  │  └─ 返回 node.type === 'user' || node.type === 'auto'
  │
  ├─ shouldShowConditionConfig(node.type)
  │  └─ 返回 node.type === 'condition'
  │
  └─ shouldShowBasicInfoHint(node.type)
     └─ 返回 node.type === 'start' || node.type === 'end'
```

---

## 测试策略

### 缺陷1的测试

#### 单元测试

1. **模态框打开/关闭**
   - 点击"编辑条件"按钮，模态框应打开
   - 模态框中的 ConditionNodeEditor 应正确显示
   - 点击"保存"，模态框应关闭，数据应更新
   - 点击"取消"，模态框应关闭，数据应保持不变

2. **条件数据保存**
   - 在模态框中修改条件数据
   - 点击"保存"，修改应被保存
   - 重新打开模态框，应显示已保存的数据

3. **条件数据丢弃**
   - 在模态框中修改条件数据
   - 点击"取消"，修改应被丢弃
   - 重新打开模态框，应显示原始数据

#### 集成测试

1. **完整流程**
   - 选择条件节点
   - 点击"编辑条件"
   - 在模态框中添加/修改条件
   - 保存条件
   - 验证流程数据已更新

2. **模态框空间**
   - 验证模态框宽度足够显示 ConditionNodeEditor
   - 验证条件编辑器在模态框中正确显示
   - 验证没有水平滚动条

### 缺陷2的测试

#### 单元测试

1. **开始节点配置**
   - 选择开始节点
   - 验证仅显示"节点名称"和"节点类型"
   - 验证不显示审批相关配置
   - 验证显示信息提示

2. **结束节点配置**
   - 选择结束节点
   - 验证仅显示"节点名称"和"节点类型"
   - 验证不显示审批相关配置
   - 验证显示信息提示

3. **人工审批节点配置**
   - 选择人工审批节点
   - 验证显示所有审批相关配置
   - 验证不显示信息提示

4. **条件节点配置**
   - 选择条件节点
   - 验证显示"节点名称"、"节点类型"、"条件分支配置"
   - 验证不显示审批相关配置

5. **节点类型切换**
   - 选择人工审批节点，验证显示审批配置
   - 切换到开始节点，验证隐藏审批配置
   - 切换回人工审批节点，验证重新显示审批配置

#### 集成测试

1. **流程配置完整性**
   - 创建包含开始、人工审批、条件、结束节点的流程
   - 验证每个节点显示正确的配置字段
   - 验证流程数据正确保存

2. **回归测试**
   - 验证人工审批节点的所有配置功能正常
   - 验证条件节点的条件编辑功能正常
   - 验证流程的保存和加载功能正常

---

## 正确性属性

### 缺陷1的正确性属性

```typescript
// Property 1: 模态框打开时，条件数据正确加载
∀ node ∈ ConditionNodes:
  openConditionModal(node) ⟹ 
    editingConditionBranches = node.condition_branches ∧
    showConditionModal = true

// Property 2: 保存时，条件数据正确更新
∀ node ∈ ConditionNodes, newData ∈ ConditionBranchesConfig:
  saveCondition(newData) ⟹ 
    node.condition_branches = newData ∧
    showConditionModal = false

// Property 3: 取消时，条件数据保持不变
∀ node ∈ ConditionNodes, originalData = node.condition_branches:
  cancelCondition() ⟹ 
    node.condition_branches = originalData ∧
    showConditionModal = false
```

### 缺陷2的正确性属性

```typescript
// Property 1: 开始节点仅显示基本信息
∀ node ∈ StartNodes:
  renderNodeConfig(node) ⟹ 
    showField('nodeName') ∧
    showField('nodeType') ∧
    ¬showField('assigneeType') ∧
    ¬showField('approvePolicy') ∧
    showHint('startNodeInfo')

// Property 2: 结束节点仅显示基本信息
∀ node ∈ EndNodes:
  renderNodeConfig(node) ⟹ 
    showField('nodeName') ∧
    showField('nodeType') ∧
    ¬showField('assigneeType') ∧
    ¬showField('approvePolicy') ∧
    showHint('endNodeInfo')

// Property 3: 人工审批节点显示所有审批配置
∀ node ∈ UserNodes:
  renderNodeConfig(node) ⟹ 
    showField('nodeName') ∧
    showField('nodeType') ∧
    showField('assigneeType') ∧
    showField('approvePolicy') ∧
    showField('slaHours') ∧
    showField('allowDelegate') ∧
    showField('rejectStrategy') ∧
    showField('autoApproveEnabled')

// Property 4: 条件节点显示条件配置
∀ node ∈ ConditionNodes:
  renderNodeConfig(node) ⟹ 
    showField('nodeName') ∧
    showField('nodeType') ∧
    showField('conditionBranches') ∧
    ¬showField('assigneeType') ∧
    ¬showField('approvePolicy')
```

---

## 防止回归

### 缺陷1的防止回归

1. **条件编辑功能保持不变**
   - ConditionNodeEditor 的所有功能（添加规则、添加分组、删除规则等）应继续正常工作
   - 条件数据的序列化和反序列化应保持一致

2. **其他节点类型不受影响**
   - 人工审批节点、自动节点、开始/结束节点的配置应不受影响
   - 流程的保存和加载应正常工作

3. **模态框集成**
   - 模态框应正确处理 ConditionNodeEditor 的事件
   - 模态框的打开/关闭应不影响其他组件

### 缺陷2的防止回归

1. **人工审批节点配置保持不变**
   - 所有审批相关配置字段应继续显示
   - 所有配置功能应继续正常工作

2. **条件节点配置保持不变**
   - 条件分支配置应继续显示
   - 条件编辑功能应继续正常工作

3. **流程数据结构保持不变**
   - 节点数据结构应保持一致
   - 流程的保存和加载应正常工作

---

## 实现优先级

### 第一阶段（高优先级）

1. **缺陷2：开始/结束节点配置** - 改动最小，影响最直接
   - 在 FlowNodeInspector 中添加条件渲染逻辑
   - 预计改动：20-30 行代码

2. **缺陷1：条件编辑模态框** - 改动中等，收益大
   - 在 FlowNodeInspector 中添加模态框
   - 预计改动：50-80 行代码

### 第二阶段（可选优化）

1. **条件编辑预览** - 在 FlowNodeInspector 中显示条件预览
2. **模态框大小调整** - 根据内容自动调整模态框大小
3. **快捷键支持** - 在模态框中支持 Ctrl+S 保存、Esc 取消

---

## 依赖和兼容性

### 依赖

- Vue 3（已有）
- Naive UI（已有）
- TypeScript（已有）

### 兼容性

- 浏览器：Chrome、Firefox、Safari、Edge（最新版本）
- 屏幕尺寸：1024px 及以上（模态框宽度 1000px）
- 移动端：不支持（流程设计器本身不支持移动端）

---

## 总结

这两个改进通过最小化代码改动实现了显著的UX提升：

1. **缺陷1** - 将条件编辑从面板内嵌改为独立模态框，提供更大的操作空间
2. **缺陷2** - 根据节点类型条件渲染配置字段，隐藏不相关的配置

两个改进都遵循现有的设计规范，使用 Naive UI 组件，保持代码风格一致。
