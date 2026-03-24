# 表单详情接口错误处理修复

## 问题描述

当前端在流程配置页面加载表单 schema 时，如果表单不存在，后端返回通用的 "查询失败" 错误（5001），而不是具体的 "表单不存在" 错误（4041）。

### 错误日志示例
```
GET /api/v1/forms/13 HTTP/1.1" 400 Bad Request
"Get form detail error: 404: 表单不存在: id=13"
```

## 根本原因

在 `backend/app/api/v1/forms.py` 的 `get_form_detail` 接口中：

1. 当 `FormPermissionService.ensure_permission` 抛出 `AuthorizationError` 时，代码尝试调用 `FormService.get_form_by_id` 来检查是否是公开表单
2. 如果表单不存在，`get_form_by_id` 会抛出 `NotFoundError`
3. 这个 `NotFoundError` 没有被内层 try-except 捕获，而是被外层的 `except Exception` 捕获
4. 最后返回通用的 "查询失败" 错误（5001），而不是具体的 "表单不存在" 错误（4041）

## 修复方案

### 后端修改（forms.py）

改进错误处理，区分不同的错误类型：

```python
async def get_form_detail(
        form_id: int = Path(..., description="表单ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """获取表单详情"""
    try:
        # 仅限拥有管理或查看权限的用户访问
        try:
            FormPermissionService.ensure_permission(
                form_id=form_id,
                tenant_id=tenant_id,
                permission=PermissionType.VIEW,
                user_id=current_user.id,
                db=db
            )
        except AuthorizationError:
            # 对于公开表单允许访问
            try:
                form = FormService.get_form_by_id(form_id, tenant_id, db)
                if form.access_mode != AccessMode.PUBLIC.value:
                    raise
            except NotFoundError:
                # 表单不存在，返回404
                return error_response(f"表单不存在: id={form_id}", 4041)

        form, current_version, versions = FormService.get_form_detail(
            form_id=form_id,
            tenant_id=tenant_id,
            db=db
        )

        response_data = FormResponse.from_orm(form).dict()

        if current_version:
            response_data["schema_json"] = current_version.schema_json
            response_data["ui_schema_json"] = current_version.ui_schema_json
            response_data["logic_json"] = current_version.logic_json
            response_data["current_version"] = current_version.version

        response_data["versions"] = [
            FormVersionResponse.from_orm(v).dict() for v in versions
        ]

        stats = FormService.get_form_statistics(form_id, tenant_id, db)
        response_data["total_submissions"] = stats["total_submissions"]

        return success_response(data=response_data)
    except NotFoundError as e:
        logger.error(f"Get form detail error: {e}")
        return error_response(str(e), 4041)
    except AuthorizationError as e:
        logger.error(f"Get form detail error: {e}")
        return error_response(str(e), 4003)
    except Exception as e:
        logger.error(f"Get form detail error: {e}")
        return error_response("查询失败", 5001)
```

### 前端修改（Configurator.vue）

改进表单 schema 加载的错误处理和日志：

```typescript
const loadFlowDraft = async (id: number) => {
  try {
    const result = await store.loadDefinition(id)
    
    // 加载关联的表单schema
    try {
      const formId = result.detail?.definition?.form_id
      console.log('Flow definition loaded:', {
        flowId: id,
        formId: formId,
        definition: result.detail?.definition
      })
      
      if (formId) {
        try {
          const formDetail = await getFormDetail(formId)
          formSchema.value = formDetail.schema_json
          console.log('Form schema loaded successfully for form:', formId)
        } catch (formError) {
          console.warn(`Failed to load form schema for form ID ${formId}:`, formError)
          message.warning(`无法加载表单 ID ${formId} 的字段信息，条件构建器可能无法正常工作`)
          // 不影响流程配置的加载，但提示用户
        }
      } else {
        console.warn('No form_id found in flow definition')
      }
    } catch (error) {
      console.warn('Unexpected error loading form schema:', error)
      // 不影响流程配置的加载
    }
  } catch (error) {
    message.error(resolveErrorMessage(error, '加载流程失败'))
  }
}
```

## 修复效果

### 错误代码映射

| 错误类型 | 错误代码 | 说明 |
|---------|---------|------|
| 表单不存在 | 4041 | NotFoundError |
| 权限不足 | 4003 | AuthorizationError |
| 其他错误 | 5001 | 通用服务器错误 |

### 前端行为

- 当表单不存在时，前端会显示警告信息：`无法加载表单 ID {formId} 的字段信息，条件构建器可能无法正常工作`
- 流程配置页面仍然可以正常加载和编辑
- 用户可以继续配置流程，但条件构建器中不会显示表单字段

## 测试步骤

1. 创建一个流程定义，但关联的表单 ID 不存在
2. 打开流程配置页面
3. 检查浏览器控制台日志，应该看到：
   - `Flow definition loaded: { flowId: X, formId: Y, definition: {...} }`
   - `Failed to load form schema for form ID Y: ...`
4. 页面应该显示警告信息，但流程配置仍然可用

## 相关文件

- `backend/app/api/v1/forms.py` - 修改 `get_form_detail` 接口
- `my-app/src/views/flow/Configurator.vue` - 改进错误处理和日志
