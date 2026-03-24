# 表单创建者权限完整性修复

## 问题描述

表单创建者在权限面板中只显示了三个权限（管理、填写、查看），但应该拥有全部五个权限（管理、编辑、导出、填写、查看）。

## 根本原因

### 后端问题
`backend/app/api/v1/form_permissions.py` 的 `get_my_permissions` 端点只检查并返回了三个权限：
- `can_manage`
- `can_fill`
- `can_view`

缺少了：
- `can_edit`
- `can_export`

### 前端问题
`my-app/src/components/form/FormPermissionDrawer.vue` 的 `permissionChips` 计算属性也只处理了这三个权限。

## 实施的修复

### 1. 后端修复 (backend/app/api/v1/form_permissions.py)

**优化逻辑**：
- 表单创建者直接返回所有权限为 `true`（无需逐一检查）
- 非创建者才需要逐一检查各项权限

```python
# 表单创建者拥有所有权限
if is_owner:
    data = {
        "is_owner": True,
        "can_fill": True,
        "can_view": True,
        "can_manage": True,
        "can_edit": True,
        "can_export": True
    }
else:
    # 非创建者需要逐一检查权限
    can_fill = FormPermissionService.has_permission(...)
    can_view = FormPermissionService.has_permission(...)
    can_manage = FormPermissionService.has_permission(...)
    can_edit = FormPermissionService.has_permission(...)
    can_export = FormPermissionService.has_permission(...)
    # ...
```

**优势**：
- 性能更好（创建者无需多次数据库查询）
- 逻辑更清晰（创建者和普通用户的权限检查分离）
- 确保创建者拥有完整权限

### 2. 前端修复 (my-app/src/components/form/FormPermissionDrawer.vue)

**更新 permissionChips 计算属性**：
```typescript
const permissions: PermissionType[] = []
if (overview.value.can_manage) permissions.push('manage')
if (overview.value.can_edit) permissions.push('edit')
if (overview.value.can_export) permissions.push('export')
if (overview.value.can_fill) permissions.push('fill')
if (overview.value.can_view) permissions.push('view')
```

**更新权限标签颜色**：
- `manage` → 警告色（warning）
- `edit` → 错误色（error）
- `export` → 信息色（info）
- `fill` → 成功色（success）
- `view` → 默认色（default）

## 修复效果

✅ **表单创建者现在显示完整权限**
- 表单拥有者
- 管理
- 编辑
- 导出
- 填写
- 查看

✅ **权限显示更加清晰**
- 不同权限用不同颜色区分
- 权限列表完整且准确

✅ **性能优化**
- 创建者权限检查从 3 次数据库查询减少到 0 次
- 直接返回预定义的权限集合

## 测试步骤

1. 创建一个新表单
2. 保存表单
3. 点击权限按钮
4. 验证显示以下权限：
   - ✓ 表单拥有者（标签）
   - ✓ 管理（警告色）
   - ✓ 编辑（错误色）
   - ✓ 导出（信息色）
   - ✓ 填写（成功色）
   - ✓ 查看（默认色）

## 相关文件修改

- `backend/app/api/v1/form_permissions.py` - 添加 `can_edit` 和 `can_export` 权限检查
- `my-app/src/components/form/FormPermissionDrawer.vue` - 更新权限显示逻辑
