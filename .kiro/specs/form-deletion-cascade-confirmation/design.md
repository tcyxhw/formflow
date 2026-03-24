# Design Document: Form Deletion with Cascade Confirmation

## Overview

This feature enhances the form deletion workflow to support cascade deletion of associated flow definitions through a user-friendly confirmation dialog. Currently, the system prevents deletion of forms with associated flow definitions by returning a 400 error. The new design allows users to explicitly confirm cascade deletion, improving the user experience while maintaining data integrity through transactional guarantees.

### Key Design Goals

1. **User Experience**: Provide clear visibility into what will be deleted before confirming
2. **Data Integrity**: Ensure cascade deletion happens atomically in a single transaction
3. **Error Recovery**: Gracefully handle failures with proper rollback and user feedback
4. **Backward Compatibility**: Preserve existing deletion behavior for forms without flow definitions
5. **Audit Trail**: Maintain comprehensive logging of cascade deletion operations

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue3)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FormManagement.vue                                      │  │
│  │  - Initiates delete action                               │  │
│  │  - Handles confirmation dialog lifecycle                 │  │
│  │  - Manages success/error states                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CascadeDeleteConfirmDialog.vue                          │  │
│  │  - Displays form name and flow definition count          │  │
│  │  - Shows deletion consequences                           │  │
│  │  - Handles user confirmation/cancellation               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DELETE /api/v1/forms/{form_id}                          │  │
│  │  - Route handler with permission checks                  │  │
│  │  - Delegates to FormService                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FormService.delete_form()                               │  │
│  │  - Validates authorization and form status              │  │
│  │  - Detects associated flow definitions                   │  │
│  │  - Orchestrates cascade deletion in transaction          │  │
│  │  - Logs deletion action                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Database Layer (PostgreSQL)                             │  │
│  │  - Form, FormVersion, FlowDefinition, FlowNode,          │  │
│  │    FlowRoute, FlowSnapshot, FlowDraft tables             │  │
│  │  - Transaction management with rollback support          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Scenario 1: Form with Associated Flow Definitions**

```
1. User clicks delete on form with flow definitions
   ↓
2. Frontend sends DELETE /api/v1/forms/{form_id}
   ↓
3. Backend validates authorization and form status
   ↓
4. Backend queries for associated flow definitions
   ↓
5. Backend returns 409 Conflict with flow definition metadata
   ↓
6. Frontend displays CascadeDeleteConfirmDialog with details
   ↓
7. User confirms deletion
   ↓
8. Frontend sends DELETE /api/v1/forms/{form_id}?cascade=true
   ↓
9. Backend performs cascade deletion in transaction:
   - Delete all FlowNode records for associated flow definitions
   - Delete all FlowRoute records for associated flow definitions
   - Delete all FlowSnapshot records for associated flow definitions
   - Delete all FlowDraft records for associated flow definitions
   - Delete all FlowDefinition records
   - Delete all FormVersion records
   - Delete Form record
   ↓
10. Backend logs deletion action
    ↓
11. Backend returns 200 success response
    ↓
12. Frontend displays success notification
    ↓
13. Frontend refreshes form list
```

**Scenario 2: Form without Associated Flow Definitions**

```
1. User clicks delete on form without flow definitions
   ↓
2. Frontend sends DELETE /api/v1/forms/{form_id}
   ↓
3. Backend validates authorization and form status
   ↓
4. Backend queries for associated flow definitions (none found)
   ↓
5. Backend performs standard deletion in transaction:
   - Delete all FormVersion records
   - Delete Form record
   ↓
6. Backend logs deletion action
   ↓
7. Backend returns 200 success response
   ↓
8. Frontend displays success notification
   ↓
9. Frontend refreshes form list
```

---

## Components and Interfaces

### Backend API Contract

#### Endpoint: DELETE /api/v1/forms/{form_id}

**Request Parameters:**
- `form_id` (path): Form ID to delete
- `cascade` (query, optional): Boolean flag to confirm cascade deletion (default: false)

**Response - Case 1: Form has associated flow definitions (cascade=false)**

Status: 409 Conflict

```json
{
  "code": 4009,
  "message": "表单存在关联的审批流程定义，需要确认级联删除",
  "data": {
    "form_id": 123,
    "form_name": "请假申请表",
    "flow_definition_count": 2,
    "flow_definitions": [
      {
        "id": 456,
        "name": "部门经理审批流程",
        "version": 1
      },
      {
        "id": 457,
        "name": "HR审批流程",
        "version": 2
      }
    ]
  }
}
```

**Response - Case 2: Cascade deletion successful**

Status: 200 OK

```json
{
  "code": 0,
  "message": "表单及关联的审批流程已成功删除",
  "data": {
    "form_id": 123,
    "form_name": "请假申请表",
    "deleted_flow_definitions": 2,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Response - Case 3: Standard deletion (no flow definitions)**

Status: 200 OK

```json
{
  "code": 0,
  "message": "表单删除成功",
  "data": {
    "form_id": 123,
    "form_name": "请假申请表"
  }
}
```

**Response - Case 4: Authorization error**

Status: 403 Forbidden

```json
{
  "code": 4003,
  "message": "只有创建者可以删除表单"
}
```

**Response - Case 5: Form status error**

Status: 400 Bad Request

```json
{
  "code": 4002,
  "message": "只能删除草稿状态的表单，已发布的表单请归档"
}
```

**Response - Case 6: Cascade deletion failure**

Status: 500 Internal Server Error

```json
{
  "code": 5001,
  "message": "删除失败：数据库约束冲突",
  "data": {
    "form_id": 123,
    "error_detail": "Foreign key constraint violation on process_instance table"
  }
}
```

### Backend Service Layer

#### FormService.delete_form() - Enhanced

```python
def delete_form(
    form_id: int,
    tenant_id: int,
    user_id: int,
    db: Session,
    cascade: bool = False
) -> Dict[str, Any]:
    """
    Delete a form with optional cascade deletion of flow definitions.
    
    Args:
        form_id: Form ID to delete
        tenant_id: Tenant ID
        user_id: Current user ID
        db: Database session
        cascade: If True, cascade delete associated flow definitions
        
    Returns:
        Dictionary with deletion result metadata
        
    Raises:
        AuthorizationError: If user is not form owner
        BusinessError: If form status is not draft or cascade needed but not confirmed
        DatabaseError: If cascade deletion fails
    """
```

#### New Helper Method: FormService._get_associated_flow_definitions()

```python
def _get_associated_flow_definitions(
    form_id: int,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Query all flow definitions associated with a form.
    
    Returns:
        List of flow definition metadata (id, name, version)
    """
```

#### New Helper Method: FormService._cascade_delete_flow_definitions()

```python
def _cascade_delete_flow_definitions(
    form_id: int,
    db: Session
) -> int:
    """
    Delete all flow definitions and related records for a form in transaction.
    
    Deletion order (respecting foreign key constraints):
    1. FlowNode records
    2. FlowRoute records
    3. FlowSnapshot records
    4. FlowDraft records
    5. FlowDefinition records
    
    Returns:
        Count of deleted flow definitions
        
    Raises:
        DatabaseError: If any deletion fails
    """
```

### Frontend Components

#### CascadeDeleteConfirmDialog.vue

```typescript
interface Props {
  visible: boolean
  formId: number
  formName: string
  flowDefinitionCount: number
  flowDefinitions: Array<{
    id: number
    name: string
    version: number
  }>
  loading: boolean
}

interface Emits {
  'update:visible': [value: boolean]
  'confirm': []
  'cancel': []
}
```

#### FormManagement.vue - Enhanced

```typescript
// New state
const showCascadeDialog = ref(false)
const cascadeDialogData = ref<CascadeDialogData | null>(null)
const deleteLoading = ref(false)

// Enhanced delete handler
async function handleDeleteForm(formId: number) {
  try {
    deleteLoading.value = true
    await deleteForm(formId)
    // Success - form deleted without flow definitions
    showSuccessNotification()
    await refreshFormList()
  } catch (error) {
    if (error.code === 4009) {
      // Form has flow definitions - show confirmation dialog
      cascadeDialogData.value = error.data
      showCascadeDialog.value = true
    } else {
      showErrorNotification(error.message)
    }
  } finally {
    deleteLoading.value = false
  }
}

// Handle cascade confirmation
async function handleCascadeConfirm() {
  try {
    deleteLoading.value = true
    await deleteForm(cascadeDialogData.value!.form_id, { cascade: true })
    showSuccessNotification('表单及关联的审批流程已成功删除')
    showCascadeDialog.value = false
    await refreshFormList()
  } catch (error) {
    showErrorNotification(error.message)
  } finally {
    deleteLoading.value = false
  }
}
```

### API Client Layer

#### Enhanced deleteForm() in src/api/form.ts

```typescript
export async function deleteForm(
  formId: number,
  options?: { cascade?: boolean }
): Promise<{ data: DeleteFormResponse }> {
  const params = new URLSearchParams()
  if (options?.cascade) {
    params.append('cascade', 'true')
  }
  
  const queryString = params.toString()
  const url = `/forms/${formId}${queryString ? '?' + queryString : ''}`
  
  return request.delete(url)
}
```

---

## Data Models

### Database Schema Changes

No schema changes required. The feature uses existing tables:
- `form` - Form records
- `form_version` - Form versions
- `flow_definition` - Flow definitions
- `flow_node` - Flow nodes
- `flow_route` - Flow routes
- `flow_snapshot` - Flow snapshots
- `flow_draft` - Flow drafts

### Pydantic Schemas

#### New Response Schema: CascadeDeleteResponse

```python
class FlowDefinitionMetadata(BaseModel):
    id: int
    name: str
    version: int

class CascadeDeleteConflictResponse(BaseModel):
    form_id: int
    form_name: str
    flow_definition_count: int
    flow_definitions: List[FlowDefinitionMetadata]

class CascadeDeleteSuccessResponse(BaseModel):
    form_id: int
    form_name: str
    deleted_flow_definitions: int
    timestamp: datetime
```

---

## Transaction Handling and Error Recovery

### Transaction Strategy

**Cascade Deletion Transaction:**

```python
try:
    db.begin_nested()  # Create savepoint
    
    # Step 1: Delete FlowNode records
    db.query(FlowNode).filter(
        FlowNode.flow_definition_id.in_(
            db.query(FlowDefinition.id).filter(
                FlowDefinition.form_id == form_id
            )
        )
    ).delete(synchronize_session=False)
    
    # Step 2: Delete FlowRoute records
    db.query(FlowRoute).filter(
        FlowRoute.flow_definition_id.in_(
            db.query(FlowDefinition.id).filter(
                FlowDefinition.form_id == form_id
            )
        )
    ).delete(synchronize_session=False)
    
    # Step 3: Delete FlowSnapshot records
    db.query(FlowSnapshot).filter(
        FlowSnapshot.flow_definition_id.in_(
            db.query(FlowDefinition.id).filter(
                FlowDefinition.form_id == form_id
            )
        )
    ).delete(synchronize_session=False)
    
    # Step 4: Delete FlowDraft records
    db.query(FlowDraft).filter(
        FlowDraft.flow_definition_id.in_(
            db.query(FlowDefinition.id).filter(
                FlowDefinition.form_id == form_id
            )
        )
    ).delete(synchronize_session=False)
    
    # Step 5: Delete FlowDefinition records
    deleted_flow_count = db.query(FlowDefinition).filter(
        FlowDefinition.form_id == form_id
    ).delete(synchronize_session=False)
    
    # Step 6: Delete FormVersion records
    db.query(FormVersion).filter(
        FormVersion.form_id == form_id
    ).delete(synchronize_session=False)
    
    # Step 7: Delete Form record
    db.delete(form)
    
    db.commit()
    return deleted_flow_count
    
except Exception as e:
    db.rollback()
    logger.error(f"Cascade deletion failed: {e}")
    raise DatabaseError(f"Cascade deletion failed: {str(e)}")
```

### Error Handling

**Constraint Violation Handling:**

```python
from sqlalchemy.exc import IntegrityError, OperationalError

try:
    # Cascade deletion logic
except IntegrityError as e:
    db.rollback()
    logger.error(f"Constraint violation during cascade delete: {e}")
    raise BusinessError(
        "删除失败：存在关联的数据无法删除。"
        "请检查是否存在进行中的审批流程实例。"
    )
except OperationalError as e:
    db.rollback()
    logger.error(f"Database error during cascade delete: {e}")
    raise DatabaseError("数据库操作失败，请稍后重试")
```

### Session Reset

```python
def _reset_session_on_error(db: Session) -> None:
    """Reset database session after failed transaction."""
    try:
        db.rollback()
        db.close()
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
```

---

## Error Handling

### Error Codes and Messages

| Code | HTTP Status | Scenario | Message |
|------|-------------|----------|---------|
| 4002 | 400 | Form not in draft status | 只能删除草稿状态的表单，已发布的表单请归档 |
| 4003 | 403 | User not form owner | 只有创建者可以删除表单 |
| 4009 | 409 | Cascade deletion needed | 表单存在关联的审批流程定义，需要确认级联删除 |
| 5001 | 500 | Cascade deletion failed | 删除失败：数据库约束冲突 |

### Frontend Error Handling

```typescript
// In FormManagement.vue
async function handleDeleteForm(formId: number) {
  try {
    await deleteForm(formId)
  } catch (error) {
    if (error.code === 4009) {
      // Show cascade confirmation dialog
      showCascadeDialog.value = true
      cascadeDialogData.value = error.data
    } else if (error.code === 4002) {
      // Show form status error
      showErrorNotification('只能删除草稿状态的表单')
    } else if (error.code === 4003) {
      // Show authorization error
      showErrorNotification('只有创建者可以删除表单')
    } else if (error.code === 5001) {
      // Show cascade deletion failure
      showErrorNotification('删除失败，请稍后重试')
    }
  }
}
```

---

## Testing Strategy

### Unit Testing Approach

**Backend Unit Tests:**

1. **Authorization Tests**
   - Test that non-owner cannot delete form
   - Test that user without MANAGE permission cannot delete form

2. **Form Status Tests**
   - Test that only draft forms can be deleted
   - Test that published/archived forms cannot be deleted

3. **Flow Definition Detection Tests**
   - Test detection of single flow definition
   - Test detection of multiple flow definitions
   - Test no flow definitions case

4. **Cascade Deletion Tests**
   - Test successful cascade deletion of all related records
   - Test transaction rollback on constraint violation
   - Test proper cleanup of FlowNode, FlowRoute, FlowSnapshot, FlowDraft records

5. **Error Handling Tests**
   - Test IntegrityError handling
   - Test OperationalError handling
   - Test session reset after failure

**Frontend Unit Tests:**

1. **Dialog Display Tests**
   - Test dialog shows when cascade needed
   - Test dialog displays correct form name and flow count
   - Test dialog displays flow definition details

2. **User Interaction Tests**
   - Test cancel button closes dialog without deletion
   - Test confirm button triggers cascade deletion
   - Test loading state during deletion

3. **Error Handling Tests**
   - Test error notification on 4009 response
   - Test error notification on 5001 response
   - Test form list refresh after successful deletion

### Property-Based Testing Approach

Property-based tests will verify universal properties across randomized inputs using Hypothesis (Python) and Vitest (TypeScript).

---

## Logging and Audit Trail

### Deletion Logging

```python
logger.info(
    f"Form cascade deleted",
    extra={
        "form_id": form_id,
        "form_name": form.name,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "deleted_flow_definitions": deleted_flow_count,
        "timestamp": datetime.utcnow().isoformat(),
        "cascade": cascade
    }
)
```

### Audit Log Entry

The existing `@audit_log` decorator will capture:
- Action: `delete_form`
- Resource type: `form`
- Record before: Form record snapshot
- User ID: Current user
- Tenant ID: Current tenant
- Timestamp: Operation timestamp

---

## Backward Compatibility

### Existing Behavior Preservation

1. **Forms without flow definitions**: Continue using existing deletion logic
2. **Non-draft forms**: Continue returning error
3. **Non-owner users**: Continue returning authorization error
4. **API response format**: Maintain existing success response format for standard deletions

### Migration Path

No data migration required. The feature is purely additive:
- New query parameter `cascade` is optional (defaults to false)
- New response code 409 is only returned when flow definitions exist
- Existing deletion logic remains unchanged for forms without flow definitions



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Flow Definition Detection

*For any* form, when a delete request is initiated, the system SHALL query the database to check for associated flow definitions, and return metadata (count and details) if any exist.

**Validates: Requirements 1.1, 1.2**

### Property 2: Standard Deletion for Forms Without Flow Definitions

*For any* form without associated flow definitions, the delete operation SHALL proceed with standard deletion logic without requiring cascade confirmation.

**Validates: Requirements 1.3, 8.1**

### Property 3: Cascade Deletion Atomicity

*For any* form with associated flow definitions, when cascade deletion is confirmed, all related records (FlowNode, FlowRoute, FlowSnapshot, FlowDraft, FlowDefinition, FormVersion, Form) SHALL be deleted in a single atomic transaction.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Transaction Rollback on Failure

*For any* cascade deletion operation, if any deletion step fails due to constraint violation or database error, the entire transaction SHALL be rolled back and the database SHALL remain in its pre-deletion state.

**Validates: Requirements 3.4, 5.1, 5.2**

### Property 5: Authorization Validation

*For any* delete request, the system SHALL verify the requesting user is the form owner before proceeding with deletion, and return an authorization error if the user is not the owner.

**Validates: Requirements 4.1, 4.2**

### Property 6: Form Status Validation

*For any* delete request, the system SHALL verify the form status is "draft" before proceeding with deletion, and return an error if the form is in any other status.

**Validates: Requirements 4.3, 4.4**

### Property 7: Cascade Confirmation Dialog Display

*For any* form with associated flow definitions, when the frontend receives a 409 Conflict response, the cascade deletion confirmation dialog SHALL be displayed with the form name and flow definition count.

**Validates: Requirements 2.1, 2.2**

### Property 8: Dialog Cancel Action

*For any* cascade deletion confirmation dialog, when the user clicks "Cancel", the dialog SHALL close without triggering any deletion operation.

**Validates: Requirements 2.5**

### Property 9: Dialog Confirm Action

*For any* cascade deletion confirmation dialog, when the user clicks "Confirm Delete", the frontend SHALL send a DELETE request with the cascade=true parameter.

**Validates: Requirements 2.6**

### Property 10: Success Notification and List Refresh

*For any* successful cascade deletion operation, the frontend SHALL display a success notification and refresh the form list, such that the deleted form no longer appears in the list.

**Validates: Requirements 6.1, 6.3, 6.4**

### Property 11: Error Handling and UI State Recovery

*For any* failed cascade deletion operation, the frontend SHALL display an error notification and maintain the dialog in a valid state allowing the user to retry or cancel.

**Validates: Requirements 5.3, 5.4**

### Property 12: Audit Trail Logging

*For any* cascade deletion operation, the system SHALL log the deletion action with form ID, user ID, tenant ID, timestamp, and cascade flag indicator.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 13: Backward Compatibility - No Dialog for Forms Without Flow Definitions

*For any* form without associated flow definitions, the delete operation SHALL complete without displaying a confirmation dialog, maintaining existing user experience.

**Validates: Requirements 8.2**

### Property 14: Backward Compatibility - Non-Draft Form Rejection

*For any* delete request on a non-draft form, the system SHALL return an error regardless of whether flow definitions exist, maintaining existing validation behavior.

**Validates: Requirements 8.3**

### Property 15: Backward Compatibility - Authorization Rejection

*For any* delete request from a non-owner user, the system SHALL return an authorization error regardless of whether flow definitions exist, maintaining existing authorization behavior.

**Validates: Requirements 8.4**

---

## Testing Strategy

### Unit Testing Approach

**Backend Unit Tests (pytest):**

1. **Authorization and Status Validation**
   - Test non-owner cannot delete form
   - Test user without MANAGE permission cannot delete form
   - Test only draft forms can be deleted
   - Test published/archived forms are rejected

2. **Flow Definition Detection**
   - Test detection of single flow definition
   - Test detection of multiple flow definitions
   - Test no flow definitions case
   - Test correct metadata returned in 409 response

3. **Cascade Deletion Operations**
   - Test successful cascade deletion of all related records
   - Test FlowNode records are deleted
   - Test FlowRoute records are deleted
   - Test FlowSnapshot records are deleted
   - Test FlowDraft records are deleted
   - Test FlowDefinition records are deleted
   - Test FormVersion records are deleted
   - Test Form record is deleted

4. **Transaction Rollback**
   - Test rollback on IntegrityError
   - Test rollback on OperationalError
   - Test database state unchanged after failed transaction
   - Test session properly reset after rollback

5. **Logging and Audit Trail**
   - Test deletion action is logged with correct metadata
   - Test cascade flag is recorded in logs
   - Test timestamp is included in logs

**Frontend Unit Tests (Vitest):**

1. **Dialog Display and Interaction**
   - Test dialog shows on 409 response
   - Test dialog displays form name and flow count
   - Test cancel button closes dialog without deletion
   - Test confirm button triggers cascade deletion API call

2. **Error Handling**
   - Test error notification on 4009 response
   - Test error notification on 5001 response
   - Test dialog remains open after error
   - Test retry functionality after error

3. **Success Handling**
   - Test success notification displayed
   - Test form list refresh triggered
   - Test deleted form removed from list

4. **Backward Compatibility**
   - Test no dialog shown for forms without flow definitions
   - Test standard deletion completes without dialog
   - Test authorization errors still returned
   - Test form status errors still returned

### Property-Based Testing Approach

**Backend Property Tests (Hypothesis):**

1. **Property 1: Flow Definition Detection**
   - Generate random forms with 0-N flow definitions
   - Verify detection returns correct count and metadata
   - Verify response code is 200 (no flow defs) or 409 (has flow defs)

2. **Property 3: Cascade Deletion Atomicity**
   - Generate random form with random flow definitions
   - Trigger cascade deletion
   - Verify all related records are deleted
   - Verify form no longer exists in database

3. **Property 4: Transaction Rollback**
   - Generate form with flow definitions
   - Simulate constraint violation during deletion
   - Verify transaction is rolled back
   - Verify form still exists in database

4. **Property 5: Authorization Validation**
   - Generate random user and form with different owner
   - Attempt deletion as non-owner
   - Verify authorization error returned
   - Verify form not deleted

5. **Property 6: Form Status Validation**
   - Generate forms with random statuses (draft, published, archived)
   - Attempt deletion on each
   - Verify only draft forms can be deleted
   - Verify non-draft forms return error

6. **Property 12: Audit Trail Logging**
   - Generate random cascade deletion
   - Verify log entry contains form_id, user_id, tenant_id, timestamp, cascade flag
   - Verify log entry is created for each deletion

**Frontend Property Tests (Vitest with fast-check):**

1. **Property 7: Cascade Confirmation Dialog Display**
   - Generate random 409 responses with flow definition metadata
   - Render component with response data
   - Verify dialog is displayed
   - Verify form name and count are rendered

2. **Property 8: Dialog Cancel Action**
   - Generate random dialog state
   - Simulate cancel click
   - Verify dialog closes
   - Verify no API call made

3. **Property 9: Dialog Confirm Action**
   - Generate random dialog state
   - Simulate confirm click
   - Verify API call made with cascade=true parameter
   - Verify correct form_id in request

4. **Property 10: Success Notification and List Refresh**
   - Generate random successful deletion response
   - Verify success notification displayed
   - Verify form list refresh triggered
   - Verify deleted form not in refreshed list

### Test Configuration

**Backend Tests:**
- Minimum 100 iterations per property test
- Use pytest fixtures for database setup/teardown
- Use transaction rollback for test isolation
- Tag format: `# Feature: form-deletion-cascade-confirmation, Property {number}: {property_text}`

**Frontend Tests:**
- Minimum 100 iterations per property test
- Mock API responses for deterministic testing
- Use component testing library (Vue Test Utils)
- Tag format: `// Feature: form-deletion-cascade-confirmation, Property {number}: {property_text}`

### Test Coverage Goals

- Backend: 95%+ coverage of FormService.delete_form() and related methods
- Frontend: 90%+ coverage of FormManagement.vue and CascadeDeleteConfirmDialog.vue
- Integration: End-to-end tests for complete cascade deletion workflow
- Error scenarios: All error paths tested with both unit and property tests

