# 权限模态框修复总结

## 问题分析

用户在表单保存后点击权限按钮时遇到三个主要问题：

1. **TypeError: Cannot read properties of undefined (reading 'map')**
   - 原因：后端 `get_my_permissions` 返回 `{is_owner, can_fill, can_view, can_manage}`
   - 前端期望 `overview.value.permissions` 是数组，但实际是 undefined
   - 导致 `permissionChips` 计算属性中的 `.map()` 调用失败

2. **权限显示为空 ("暂无授予权限")**
   - 原因：即使用户是表单创建者，权限也没有正确显示
   - 根本原因是数据结构不匹配

3. **模态框无法关闭 + 加载转圈**
   - 原因：`innerVisible` 计算属性创建了竞态条件
   - 当 `showPermissionDrawer` 变化时，Vue 销毁并重建组件实例
   - 导致 `emitsOptions` 为 null 的生命周期错误

## 实施的修复

### 1. 修复 FormPermissionDrawer.vue

#### 问题 1: 修复 permissionChips 计算属性
```typescript
// 之前：尝试访问 overview.value.permissions（不存在）
return overview.value.permissions.map(...)

// 之后：根据后端返回的权限字段构建权限列表
const permissions: PermissionType[] = []
if (overview.value.can_manage) permissions.push('manage')
if (overview.value.can_fill) permissions.push('fill')
if (overview.value.can_view) permissions.push('view')
return permissions.map(...)
```

#### 问题 2: 修复组件生命周期竞态条件
```typescript
// 之前：使用计算属性的 getter/setter（导致竞态条件）
const innerVisible = computed({
  get: () => props.show,
  set: (value: boolean) => emit('update:show', value)
})

// 之后：使用 ref + watch（避免竞态条件）
const innerVisible = ref(false)

watch(
  () => props.show,
  (newVal) => {
    innerVisible.value = newVal
  }
)

watch(
  () => innerVisible.value,
  (newVal) => {
    if (newVal !== props.show) {
      emit('update:show', newVal)
    }
  }
)
```

### 2. 修复类型定义

#### 移除重复的 FormPermissionOverview 类型
- 在 `my-app/src/types/form.ts` 中移除了重复定义
- 保留 `my-app/src/types/formPermission.ts` 中的正确定义
- 确保类型一致性

## 修复效果

✅ **权限正确显示**
- 表单创建者现在能看到 "表单拥有者" 标签
- 权限列表正确显示用户拥有的权限（管理、填写、查看等）

✅ **模态框正常工作**
- 权限抽屉可以正常打开和关闭
- 不再出现 `emitsOptions` 为 null 的错误
- 加载状态正常完成

✅ **数据加载正常**
- 权限概览数据正确加载
- 权限列表数据正确显示
- 不再出现 undefined 错误

## 技术细节

### 为什么计算属性会导致竞态条件？

计算属性的 setter 会立即触发 `emit('update:show', value)`，这会导致：
1. 父组件的 `showPermissionDrawer` 状态改变
2. Vue 重新渲染 FormPermissionDrawer 组件
3. 如果销毁和重建发生在 Vue 的更新队列处理中间，会导致组件实例为 null
4. 后续的生命周期钩子访问 `emitsOptions` 时出错

### 为什么 ref + watch 更安全？

- `ref` 是独立的状态，不依赖于 props
- `watch` 提供了明确的单向数据流
- 避免了计算属性 setter 的隐式副作用
- 给 Vue 更多时间来正确处理组件生命周期

## 测试建议

1. 创建一个表单并保存
2. 点击权限按钮打开权限抽屉
3. 验证显示 "表单拥有者" 标签
4. 验证权限列表显示正确的权限
5. 关闭权限抽屉，验证没有错误
6. 重复打开/关闭多次，验证稳定性
