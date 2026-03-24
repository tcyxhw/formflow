# FlowDesigner 流程设计器主容器

## 概述

`FlowDesigner.vue` 是审批流程设计系统的主容器组件，整合了所有流程设计相关的子组件，提供完整的流程编辑、保存和发布功能。

## 功能特性

### 1. 流程编辑
- **节点管理**：添加、编辑、删除流程节点
- **路由管理**：创建、编辑、删除节点之间的连接
- **位置管理**：拖拽调整节点在画布上的位置
- **实时同步**：所有编辑操作实时同步到 Pinia store

### 2. 编辑器面板
- **节点编辑器**：配置节点属性（名称、类型、审批人、驳回策略等）
- **路由编辑器**：配置路由条件、优先级、默认路由设置
- **标签页切换**：在节点编辑和路由编辑之间快速切换

### 3. 保存和发布
- **草稿保存**：保存当前编辑状态到后端
- **流程发布**：发布流程版本，锁定配置
- **版本管理**：支持版本标签和变更说明

### 4. 用户界面
- **三栏布局**：左侧节点调色板、中间画布、右侧编辑器
- **状态指示**：显示保存状态（已保存/未保存）
- **工具栏**：快速访问保存和发布功能

## 组件结构

```
FlowDesigner.vue
├── 头部工具栏 (designer-header)
│   ├── 返回按钮
│   ├── 流程名称和版本
│   ├── 保存状态指示器
│   └── 保存/发布按钮
├── 主体布局 (designer-body)
│   ├── 左侧边栏 (left-sidebar)
│   │   └── FlowNodePalette (节点调色板)
│   ├── 中间画布 (designer-canvas-wrapper)
│   │   └── FlowCanvas (流程画布)
│   └── 右侧边栏 (right-sidebar)
│       ├── 编辑器标签页
│       ├── FlowNodeEditor (节点编辑器)
│       └── FlowRouteEditor (路由编辑器)
└── 发布对话框 (publish-dialog)
    ├── 版本标签输入
    ├── 变更说明输入
    └── 发布确认
```

## Props

无 props，通过路由参数获取流程定义 ID。

## 路由参数

- `flowDefinitionId` (number): 流程定义的 ID

## 事件处理

### 节点操作
- `handleSelectNode(nodeKey)`: 选中节点
- `handleUpdateNode(payload)`: 更新节点属性
- `handleDeleteNode(nodeKey)`: 删除节点
- `handleUpdatePosition(payload)`: 更新节点位置

### 路由操作
- `handleSelectRoute(index)`: 选中路由
- `handleUpdateRoute(payload)`: 更新路由属性
- `handleDeleteRoute(index)`: 删除路由
- `handleAddRoute(payload)`: 添加新路由

### 保存和发布
- `handleSaveDraft()`: 保存草稿
- `handlePublish()`: 发布流程

## 状态管理

使用 Pinia store `useFlowDraftStore` 管理以下状态：

```typescript
// 流程信息
flowDefinitionId: number
flowName: string
version: number

// 流程结构
nodes: FlowNodeConfig[]
routes: FlowRouteConfig[]
nodesGraph: Record<string, FlowNodePosition>

// 选中状态
selectedNodeKey?: string
selectedRouteIndex?: number | null

// 操作状态
loading: boolean
saving: boolean
publishing: boolean
dirty: boolean
```

## 使用示例

### 在路由中配置

```typescript
// src/router/index.ts
{
  path: '/flow/:flowDefinitionId',
  component: () => import('@/views/FlowDesigner.vue'),
  meta: {
    title: '流程设计器',
    requiresAuth: true
  }
}
```

### 导航到流程设计器

```typescript
import { useRouter } from 'vue-router'

const router = useRouter()

// 打开流程设计器
router.push({
  name: 'FlowDesigner',
  params: { flowDefinitionId: 123 }
})
```

## 关键功能说明

### 1. 节点编辑流程

```
选择节点 → 自动切换到节点编辑标签页 → 编辑属性 → 实时保存到 store
```

### 2. 路由编辑流程

```
选择路由 → 自动切换到路由编辑标签页 → 编辑条件和优先级 → 实时保存到 store
```

### 3. 保存流程

```
编辑操作 → 标记为脏状态 → 点击保存按钮 → 发送到后端 → 清除脏状态
```

### 4. 发布流程

```
点击发布按钮 → 打开发布对话框 → 输入版本信息 → 确认发布 → 创建快照
```

## 错误处理

- **缺少流程定义 ID**：显示错误提示并返回
- **加载失败**：显示错误提示并返回
- **删除开始/结束节点**：显示警告提示，阻止删除
- **从结束节点添加路由**：显示错误提示，阻止操作
- **保存失败**：显示错误提示，保留编辑状态
- **发布失败**：显示错误提示，保留编辑状态

## 样式特点

- **响应式设计**：支持不同屏幕尺寸
- **深色/浅色主题**：使用 Naive UI 主题系统
- **流畅动画**：平滑的过渡效果
- **清晰的视觉层级**：通过颜色和间距区分不同区域

### 响应式断点

- **1400px 以上**：完整三栏布局
- **1200px - 1400px**：缩小侧栏宽度
- **768px - 1200px**：进一步缩小
- **768px 以下**：垂直堆叠布局

## 性能优化

1. **懒加载子组件**：通过动态 import 加载
2. **事件防抖**：避免频繁的 store 更新
3. **虚拟滚动**：大量节点时使用虚拟滚动
4. **缓存**：缓存表单 schema 和流程定义

## 测试覆盖

### 单元测试 (`FlowDesigner.test.ts`)
- 组件初始化
- 头部功能
- 编辑器标签页
- 节点操作
- 路由操作
- 保存功能
- 发布功能
- 位置更新
- 节点编辑
- 路由编辑
- 响应式布局

### 集成测试 (`FlowDesignerIntegration.test.ts`)
- 完整流程设计工作流
- 多节点编辑场景
- 节点和路由的关联操作
- 状态同步
- 错误处理
- UI 交互集成
- 数据持久化
- 性能和稳定性
- 组件通信

## 常见问题

### Q: 如何添加新节点？
A: 从左侧节点调色板拖拽节点到画布，或通过 store 的 `addNode()` 方法。

### Q: 如何删除节点？
A: 右键点击节点选择删除，或通过 store 的 `removeNode()` 方法。

### Q: 如何编辑节点属性？
A: 点击节点选中，在右侧编辑器中修改属性。

### Q: 如何创建路由？
A: 从节点的出口点拖拽到目标节点的入口点。

### Q: 如何保存编辑？
A: 点击头部的"保存草稿"按钮。

### Q: 如何发布流程？
A: 点击头部的"发布流程"按钮，填写版本信息后确认。

### Q: 发布后还能编辑吗？
A: 不能。发布后流程版本被锁定，需要创建新版本才能继续编辑。

## 相关文件

- `src/components/flow-designer/FlowCanvas.vue` - 流程画布
- `src/components/flow-designer/FlowNodePalette.vue` - 节点调色板
- `src/components/flow-designer/FlowNodeEditor.vue` - 节点编辑器
- `src/components/flow-designer/FlowRouteEditor.vue` - 路由编辑器
- `src/stores/flowDraft.ts` - 流程草稿状态管理
- `src/api/flow.ts` - 流程 API 接口
- `src/types/flow.ts` - 流程相关类型定义

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本
- 支持节点和路由编辑
- 支持保存和发布功能
- 完整的单元测试和集成测试
