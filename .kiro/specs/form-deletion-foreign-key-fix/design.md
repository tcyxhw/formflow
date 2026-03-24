# Form Deletion Foreign Key Fix - Design Document

## Overview

When users attempt to delete a form that has associated flow definitions, the system crashes with a `ForeignKeyViolation` error instead of gracefully handling the constraint violation. The database correctly prevents orphaned references, but the application doesn't catch and handle this error appropriately.

The fix will implement proper error handling in the `delete_form` service method to detect when flow definitions exist for a form and return a clear 400 error message instead of allowing the database constraint violation to propagate. This ensures users receive actionable feedback and the transaction is properly rolled back without leaving the session in a failed state.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a user attempts to delete a form that has associated flow_definition records
- **Property (P)**: The desired behavior when the bug condition occurs - return a 400 error with a clear message and properly rollback the transaction
- **Preservation**: Existing deletion logic for forms without flow definitions and other form operations that must remain unchanged
- **delete_form()**: The service method in `backend/app/services/form_service.py` that handles form deletion
- **flow_definition**: Records in the `flow_definition` table that reference a form via the `form_id` foreign key
- **ForeignKeyViolation**: The database constraint error that occurs when attempting to delete a form with existing flow definitions

## Bug Details

### Bug Condition

The bug manifests when a user attempts to delete a form that has associated flow_definition records. The `delete_form` service method attempts to delete the form without first checking if flow definitions exist, causing the database to raise a `ForeignKeyViolation` error. This error is not caught by the service layer, propagates to the API layer, and is caught only by the generic `Exception` handler, resulting in a 500 error instead of a meaningful 400 error.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type DeleteFormRequest
         - form_id: integer
         - tenant_id: integer
         - user_id: integer
  OUTPUT: boolean
  
  RETURN form_exists(form_id, tenant_id)
         AND form_status(form_id) == "draft"
         AND user_owns_form(form_id, user_id)
         AND flow_definitions_exist(form_id) > 0
         AND NOT error_handled_gracefully
END FUNCTION
```

### Examples

**Example 1: Form with flow definitions - Bug Manifestation**
- User creates a form "Approval Request"
- User creates a flow definition for the form
- User attempts to delete the form
- Expected: 400 error with message "Cannot delete form with existing flow definitions"
- Actual: 500 error with generic "删除失败" message, database error in logs

**Example 2: Form without flow definitions - Works Correctly**
- User creates a form "Survey"
- User does NOT create any flow definitions
- User attempts to delete the form
- Expected: 200 success response
- Actual: 200 success response (no bug)

**Example 3: Published form with flow definitions - Correct Error**
- User creates a form "Approval Request"
- User publishes the form
- User creates a flow definition for the form
- User attempts to delete the form
- Expected: 400 error with message "Only draft forms can be deleted"
- Actual: 400 error with correct message (status check happens first)

**Example 4: Form without permission - Correct Error**
- User A creates a form
- User B attempts to delete User A's form
- Expected: 403 authorization error
- Actual: 403 authorization error (permission check happens first)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Forms without flow definitions must continue to be successfully deleted
- Forms with status other than "draft" must continue to return an error
- Forms owned by other users must continue to return an authorization error
- Deletion must continue to delete all associated FormVersion records
- Deletion must continue to log the action for audit purposes
- All other form operations (create, update, publish, archive) must be unaffected

**Scope:**
All inputs that do NOT involve attempting to delete a form with existing flow definitions should be completely unaffected by this fix. This includes:
- Deleting forms without flow definitions
- Deleting forms with status other than "draft"
- Attempting to delete forms without proper permissions
- All other form management operations

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Missing Constraint Check**: The `delete_form` method does not check for the existence of flow_definition records before attempting to delete the form. The database constraint is enforced at the database level, but the application doesn't proactively check for this condition.

2. **Unhandled Database Exception**: The `ForeignKeyViolation` exception from SQLAlchemy is not caught in the service layer. It propagates to the API layer where only `BusinessError` is explicitly caught, causing the generic `Exception` handler to catch it and return a 500 error.

3. **Transaction State Not Rolled Back**: When the database constraint violation occurs, the transaction enters a failed state. The generic exception handler doesn't explicitly rollback the session, potentially leaving it in a pending rollback state.

4. **No User-Friendly Error Message**: Even if the exception were caught, there's no mechanism to provide a clear, actionable error message to the user about why the deletion failed.

## Correctness Properties

Property 1: Bug Condition - Form Deletion with Flow Definitions

_For any_ form deletion request where the form has associated flow_definition records (isBugCondition returns true), the fixed delete_form function SHALL return a 400 error with a clear message indicating the form cannot be deleted due to existing flow definitions, and SHALL properly rollback the transaction without leaving the session in a failed state.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Form Deletion Without Flow Definitions

_For any_ form deletion request where the form does NOT have associated flow_definition records (isBugCondition returns false), the fixed delete_form function SHALL produce exactly the same result as the original function, successfully deleting the form and all its associated versions, and preserving all existing deletion behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `backend/app/services/form_service.py`

**Function**: `FormService.delete_form()`

**Specific Changes**:

1. **Add Flow Definition Check**: Before attempting to delete the form, query the database to check if any flow_definition records exist for this form_id.
   - Query: `db.query(FlowDefinition).filter(FlowDefinition.form_id == form_id).first()`
   - If found, raise a `BusinessError` with a clear message

2. **Explicit Error Handling**: Raise a `BusinessError` exception when flow definitions exist, which will be caught by the existing exception handler in the API layer.
   - Error message: "Cannot delete form with existing flow definitions. Please delete the associated flow definitions first."
   - This ensures the error is caught by the `except BusinessError` handler in the API layer

3. **Transaction Rollback**: The existing `db.commit()` call will not be reached if the check fails, so the transaction will be automatically rolled back by SQLAlchemy when the exception is raised.

4. **Import FlowDefinition Model**: Add import for `FlowDefinition` model from `app.models.workflow` to enable the query.

### Implementation Pseudocode

```
FUNCTION delete_form(form_id, tenant_id, user_id, db)
  form := get_form_by_id(form_id, tenant_id, db)
  
  IF form.owner_user_id != user_id THEN
    RAISE AuthorizationError("Only creator can delete form")
  END IF
  
  IF form.status != "draft" THEN
    RAISE BusinessError("Only draft forms can be deleted")
  END IF
  
  # NEW: Check for flow definitions
  flow_defs := db.query(FlowDefinition).filter(FlowDefinition.form_id == form_id).first()
  IF flow_defs IS NOT NULL THEN
    RAISE BusinessError("Cannot delete form with existing flow definitions. Please delete the associated flow definitions first.")
  END IF
  
  # Delete associated versions
  db.query(FormVersion).filter(FormVersion.form_id == form_id).delete()
  
  # Delete form
  db.delete(form)
  db.commit()
  
  log("Deleted form: id={form_id}, tenant={tenant_id}")
  RETURN true
END FUNCTION
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that attempt to delete forms with flow definitions and assert that the deletion fails with a proper error. Run these tests on the UNFIXED code to observe the 500 error and database exception, confirming the bug exists.

**Test Cases**:
1. **Delete Form with Single Flow Definition**: Create a form, create a flow definition for it, attempt to delete the form (will fail with 500 on unfixed code)
2. **Delete Form with Multiple Flow Definitions**: Create a form, create multiple flow definitions for it, attempt to delete the form (will fail with 500 on unfixed code)
3. **Delete Form with Flow Definition and Nodes**: Create a form, create a flow definition with nodes, attempt to delete the form (will fail with 500 on unfixed code)
4. **Delete Form with Flow Definition and Snapshots**: Create a form, create a flow definition with snapshots, attempt to delete the form (will fail with 500 on unfixed code)

**Expected Counterexamples**:
- Deletion attempt raises `ForeignKeyViolation` error
- API returns 500 error instead of 400
- Error message is generic "删除失败" instead of specific about flow definitions
- Possible causes: missing constraint check, unhandled database exception, no user-friendly error message

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := delete_form_fixed(input)
  ASSERT result.status_code == 400
  ASSERT result.message CONTAINS "flow definitions"
  ASSERT transaction_rolled_back(input.db)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT delete_form_original(input) = delete_form_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for forms without flow definitions, then write property-based tests capturing that behavior to ensure the fix doesn't change it.

**Test Cases**:
1. **Delete Draft Form Without Flow Definitions**: Verify that draft forms without flow definitions continue to be deleted successfully
2. **Delete Published Form Preservation**: Verify that attempting to delete published forms continues to return the correct error
3. **Delete Unauthorized Form Preservation**: Verify that attempting to delete forms without permission continues to return authorization error
4. **Delete Form with Versions Preservation**: Verify that deleting a form continues to delete all associated versions
5. **Audit Logging Preservation**: Verify that deletion continues to be logged for audit purposes

### Unit Tests

- Test that deleting a form with flow definitions returns 400 error with specific message
- Test that deleting a form without flow definitions succeeds
- Test that deleting a published form returns appropriate error
- Test that deleting a form without permission returns authorization error
- Test that form versions are deleted along with the form
- Test that audit log is created for successful deletion

### Property-Based Tests

- Generate random forms with and without flow definitions, verify deletion behavior is correct
- Generate random user permissions and verify authorization checks work correctly
- Generate random form statuses and verify only draft forms can be deleted
- Test that all non-buggy deletion scenarios continue to work after fix

### Integration Tests

- Test full flow: create form → create flow definition → attempt delete → verify 400 error
- Test full flow: create form → delete form → verify success
- Test full flow: create form → publish → attempt delete → verify error
- Test full flow: create form → create flow definition → delete flow definition → delete form → verify success
