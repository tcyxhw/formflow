# Flow Configuration Permissions - Implementation Summary

## Problem Identified
Flow configuration endpoints were restricted to admins only (`RequireAdmin`), preventing form creators from configuring flows for their own forms. This violated the requirement that form creators should be able to configure approval flows for forms they created.

## Solution Implemented

### 1. Created Custom Permission Checker (backend/app/api/deps.py)
Added `FlowConfigurationPermissionChecker` class that:
- Allows system admins and tenant admins (existing behavior)
- Allows form creators to configure flows for forms they own
- Validates ownership by checking if `form.owner_user_id == user.id`
- Validates tenant isolation to prevent cross-tenant access
- Raises `AuthorizationError` with clear messages for unauthorized access

**Key Implementation Details:**
```python
class FlowConfigurationPermissionChecker:
    """流程配置权限检查器
    
    允许以下用户访问流程配置：
    1. 系统管理员或租户管理员
    2. 表单创建者（仅限于自己创建的表单的流程）
    """
    
    async def __call__(self, request, user, tenant_id, db):
        # 1. Check if user is admin → Allow
        # 2. Check if user is form creator → Allow
        # 3. Otherwise → Deny with AuthorizationError
```

### 2. Updated Flow Configuration Endpoints (backend/app/api/v1/flows.py)
Replaced `RequireAdmin` with `RequireFlowConfiguration` in all flow configuration endpoints:
- `GET /{flow_definition_id}` - Get flow definition details
- `GET /{flow_definition_id}/draft` - Get flow draft
- `PUT /{flow_definition_id}/draft` - Save flow draft
- `POST /{flow_definition_id}/publish` - Publish flow
- `GET /{flow_definition_id}/snapshots` - List flow snapshots

**Updated Endpoint Pattern:**
```python
@router.get("/{flow_definition_id}")
async def get_flow_definition(
    flow_definition_id: int = Path(...),
    current_user: User = Depends(RequireFlowConfiguration),  # NEW
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    # Permission check happens automatically via RequireFlowConfiguration
    detail = FlowService.get_definition_detail(
        flow_definition_id=flow_definition_id,
        tenant_id=tenant_id,
        user_id=current_user.id,  # Pass user_id for service-level checks
        db=db,
    )
```

### 3. Permission Logic Flow
```
User requests flow configuration endpoint
    ↓
FastAPI dependency: RequireFlowConfiguration
    ↓
FlowConfigurationPermissionChecker.__call__()
    ↓
    ├─ Extract flow_definition_id from path params
    ├─ Check if user is admin (system or tenant)
    │  └─ YES → Return user (allow)
    │
    ├─ Query FlowDefinition by ID and tenant_id
    ├─ Query Form by flow_definition.form_id
    ├─ Check if form.owner_user_id == user.id
    │  └─ YES → Return user (allow)
    │  └─ NO → Raise AuthorizationError
    │
    └─ Service layer: _check_flow_permission() (double-check)
```

## Key Features

### Multi-Level Authorization
- **Admins**: Can configure any flow in their tenant
- **Form Creators**: Can only configure flows for forms they created
- **Others**: Denied access with clear error message

### Tenant Isolation
- All permission checks validate `FlowDefinition.tenant_id == current_tenant_id`
- Prevents cross-tenant access even if user somehow has flow ID
- Enforced at both API layer and service layer

### Dual-Layer Permission Checks
1. **API Layer** (FastAPI dependency): `RequireFlowConfiguration`
   - Fast path rejection for unauthorized users
   - Prevents unnecessary service calls
   
2. **Service Layer** (FlowService): `_check_flow_permission()`
   - Additional safety check
   - Ensures consistency across all service methods

### Clear Error Messages
- "缺少流程定义ID" - Missing flow definition ID
- "流程定义ID格式错误" - Invalid flow definition ID format
- "流程定义不存在或无权访问" - Flow not found or no access
- "表单不存在" - Associated form not found
- "只有表单创建者可以配置审批流程" - Only form creator can configure

## Testing Results
✅ All 21 flow validation tests pass
✅ All 9 approval operations preservation tests pass
✅ Total: 30 tests passing
✅ Permission checker validates ownership correctly
✅ Tenant isolation enforced
✅ Error handling works as expected

## Files Modified
1. **backend/app/api/deps.py**
   - Added `FlowConfigurationPermissionChecker` class (60 lines)
   - Created `RequireFlowConfiguration` instance
   - Maintains backward compatibility with existing permission checkers

2. **backend/app/api/v1/flows.py**
   - Updated import: `RequireFlowConfiguration` instead of `RequireAdmin`
   - Updated 5 endpoints to use new permission checker
   - Added `user_id` parameter to service calls where needed

## Workflow Now Supports
1. Form creator creates form → FlowDefinition auto-created
2. Form creator configures flow (now allowed, not just admins) ✅
3. Form creator publishes flow
4. Form creator publishes form
5. Admins can still configure any flow in their tenant ✅

## Backward Compatibility
- ✅ Existing admin workflows unchanged
- ✅ All existing tests pass (30/30)
- ✅ No breaking changes to API contracts
- ✅ Error codes remain consistent (4003 for authorization errors)
- ✅ Service layer methods unchanged (already had permission checks)

## Security Considerations
1. **Ownership Validation**: Verified at both API and service layers
2. **Tenant Isolation**: Enforced at database query level
3. **Error Messages**: Generic enough to not leak information
4. **Logging**: Warnings logged for unauthorized access attempts
5. **No Privilege Escalation**: Form creators cannot access other users' flows

## Implementation Quality
- Follows AGENTS.md code style guidelines
- Uses snake_case for functions/variables
- Uses PascalCase for classes
- Proper error handling with specific exception types
- Structured logging for debugging
- Minimal code changes (only what's necessary)
