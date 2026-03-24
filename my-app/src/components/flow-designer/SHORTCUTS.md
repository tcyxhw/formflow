# 快捷键操作功能

## 概述

快捷键操作功能为流程设计器提供了快速的键盘操作支持，提高了用户的工作效率。

## 支持的快捷键

| 快捷键 | 操作 | 描述 |
|--------|------|------|
| Ctrl+Z / Cmd+Z | 撤销 | 撤销上一步操作 |
| Ctrl+Y / Cmd+Shift+Z | 重做 | 重做下一步操作 |
| Ctrl+A / Cmd+A | 全选 | 选中所有节点 |
| Delete | 删除 | 删除选中节点 |
| Ctrl+C / Cmd+C | 复制 | 复制选中节点 |
| Ctrl+V / Cmd+V | 粘贴 | 粘贴复制的节点 |
| Ctrl+D / Cmd+D | 复制（重复） | 复制并粘贴选中节点 |
| Ctrl+S / Cmd+S | 保存 | 保存流程 |

## 文件结构

```
src/
├── constants/
│   ├── shortcuts.ts                    # 快捷键配置常量
│   └── __tests__/
│       └── shortcuts.test.ts           # 快捷键常量测试
├── components/flow-designer/
│   ├── FlowCanvas.vue                  # 流程画布组件（集成快捷键处理）
│   ├── ShortcutHints.vue               # 快捷键提示组件
│   ├── SHORTCUTS.md                    # 本文件
│   └── __tests__/
│       ├── FlowCanvas.test.ts          # 流程画布测试
│       └── ShortcutHints.test.ts       # 快捷键提示组件测试
```

## 核心模块

### 1. 快捷键配置常量 (`src/constants/shortcuts.ts`)

定义了所有支持的快捷键映射和相关配置。

**主要导出：**

- `SHORTCUTS`: 快捷键配置对象
- `ShortcutAction`: 快捷键操作类型
- `ShortcutConfig`: 快捷键配置接口
- `getShortcutAction(event)`: 根据键盘事件获取操作类型
- `getShortcutDisplayText(action)`: 获取快捷键的显示文本
- `getAllShortcuts()`: 获取所有快捷键配置

**特点：**

- 支持 Windows/Linux 和 Mac 平台
- 自动检测 Ctrl/Cmd 键
- 提供平台特定的显示文本（如 Mac 上显示 ⌘ 符号）

### 2. 流程画布组件 (`src/components/flow-designer/FlowCanvas.vue`)

集成了快捷键处理的流程设计画布。

**新增事件：**

```typescript
emit('select-all')      // 全选事件
emit('delete')          // 删除事件
emit('copy')            // 复制事件
emit('paste')           // 粘贴事件
emit('duplicate')       // 复制（重复）事件
emit('save')            // 保存事件
```

**快捷键处理流程：**

1. 在 `onMounted` 时注册全局 `keydown` 事件监听器
2. 使用 `getShortcutAction()` 识别快捷键操作
3. 检查是否在输入框中（某些快捷键在输入框中被禁用）
4. 调用 `preventDefault()` 防止浏览器默认行为
5. 发出相应的事件

### 3. 快捷键提示组件 (`src/components/flow-designer/ShortcutHints.vue`)

显示所有支持的快捷键的帮助组件。

**功能：**

- 显示快捷键帮助按钮
- 点击按钮打开快捷键列表模态框
- 自动适配 Windows/Linux 和 Mac 平台
- 显示每个快捷键的名称、描述和按键组合

**使用方式：**

```vue
<template>
  <ShortcutHints />
</template>

<script setup lang="ts">
import ShortcutHints from '@/components/flow-designer/ShortcutHints.vue'
</script>
```

## 使用示例

### 在 FlowDesigner 中集成快捷键

```vue
<template>
  <div class="flow-designer">
    <FlowCanvas
      :nodes="nodes"
      :routes="routes"
      :nodesGraph="nodesGraph"
      @select-all="handleSelectAll"
      @delete="handleDelete"
      @copy="handleCopy"
      @paste="handlePaste"
      @duplicate="handleDuplicate"
      @save="handleSave"
      @undo="handleUndo"
      @redo="handleRedo"
    />
    <ShortcutHints />
  </div>
</template>

<script setup lang="ts">
import FlowCanvas from '@/components/flow-designer/FlowCanvas.vue'
import ShortcutHints from '@/components/flow-designer/ShortcutHints.vue'

const handleSelectAll = () => {
  // 实现全选逻辑
}

const handleDelete = () => {
  // 实现删除逻辑
}

const handleCopy = () => {
  // 实现复制逻辑
}

const handlePaste = () => {
  // 实现粘贴逻辑
}

const handleDuplicate = () => {
  // 实现复制（重复）逻辑
}

const handleSave = () => {
  // 实现保存逻辑
}

const handleUndo = () => {
  // 实现撤销逻辑
}

const handleRedo = () => {
  // 实现重做逻辑
}
</script>
```

## 测试覆盖

### 快捷键常量测试 (`src/constants/__tests__/shortcuts.test.ts`)

- ✅ 快捷键配置验证
- ✅ 快捷键识别（Windows/Linux 和 Mac）
- ✅ 快捷键显示文本格式化
- ✅ 平台特定符号显示

**测试数量：** 43 个测试用例

### 流程画布测试 (`src/components/flow-designer/__tests__/FlowCanvas.test.ts`)

- ✅ 基础渲染测试
- ✅ 撤销/重做快捷键测试
- ✅ 快捷键操作测试（全选、删除、复制、粘贴等）
- ✅ 事件发出验证

**测试数量：** 43 个测试用例

### 快捷键提示组件测试 (`src/components/flow-designer/__tests__/ShortcutHints.test.ts`)

- ✅ 组件渲染测试
- ✅ 模态框打开/关闭测试
- ✅ 快捷键显示测试
- ✅ 平台特定符号测试

**测试数量：** 10 个测试用例

## 平台兼容性

### Windows/Linux

- Ctrl+Z：撤销
- Ctrl+Y：重做
- Ctrl+A：全选
- Delete：删除
- Ctrl+C：复制
- Ctrl+V：粘贴
- Ctrl+D：复制（重复）
- Ctrl+S：保存

### Mac

- Cmd+Z：撤销
- Cmd+Y 或 Cmd+Shift+Z：重做
- Cmd+A：全选
- Delete：删除
- Cmd+C：复制
- Cmd+V：粘贴
- Cmd+D：复制（重复）
- Cmd+S：保存

## 实现细节

### 快捷键识别逻辑

```typescript
// 统一处理 Ctrl 和 Cmd
const isCtrlOrCmd = event.ctrlKey || event.metaKey

// 识别快捷键
if (isCtrlOrCmd && event.key === 'z' && !event.shiftKey) {
  return 'undo'
}
```

### 输入框中的快捷键禁用

某些快捷键在输入框中被禁用，以避免干扰用户输入：

```typescript
const disableInInputActions: ShortcutAction[] = ['selectAll', 'delete']
if (isInInput && disableInInputActions.includes(action)) {
  return
}
```

### 事件监听器生命周期

```typescript
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
```

## 性能考虑

- 快捷键识别使用简单的条件判断，性能开销极小
- 事件监听器在组件卸载时正确清理
- 没有使用任何第三方快捷键库，减少依赖

## 扩展性

要添加新的快捷键，只需：

1. 在 `src/constants/shortcuts.ts` 中的 `SHORTCUTS` 对象中添加新的快捷键配置
2. 在 `getShortcutAction()` 函数中添加识别逻辑
3. 在 `FlowCanvas.vue` 中的 `handleKeyDown()` 函数中添加处理逻辑
4. 在 `emit` 中添加新的事件
5. 编写相应的测试用例

## 已知限制

- 某些快捷键可能与浏览器或操作系统的快捷键冲突
- 在某些输入法下，快捷键识别可能不准确
- 不支持自定义快捷键映射（可作为未来功能）

## 相关文档

- [FlowCanvas 组件文档](./FlowCanvas.README.md)
- [快捷键常量源代码](../../constants/shortcuts.ts)
- [快捷键提示组件源代码](./ShortcutHints.vue)
