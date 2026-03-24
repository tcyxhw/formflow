# Approval Claim Tenant Fix Bugfix Design

## Overview

This document outlines the fix for two categories of bugs in the approval workflow:

1. **Backend Bug**: The `claim_task` operation fails when creating `TaskActionLog` records because `tenant_id` is not passed to `_create_action_log`, causing a database NOT NULL constraint violation.

2. **Frontend UI Bugs**: Three UI issues in the approval workbench - removing the "轨迹" (trace) section, removing "无截止" (no deadline) status display, and fixing SLA label-font mismatch.

The backend fix involves adding the missing `tenant_id` parameter to the `_create_action_log` call in `claim_task`. The frontend fixes involve removing specific UI components and correcting CSS class assignments.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when `claim_task` is called without passing `tenant_id` to `_create_action_log`
- **Property (P)**: The desired behavior - `TaskActionLog` records should have valid `tenant_id` values
- **Preservation**: Existing behavior for other operations and UI components that must remain unchanged
- **`claim_task`**: The service function in `task_service.py` that handles task claiming
- **`_create_action_log`**: Internal helper method that creates `TaskActionLog` records
- **`TaskActionLog`**: Database model for tracking task action history
- **SLA**: Service Level Agreement - time-based task deadlines and status tracking
- **租户 (Tenant)**: Multi-tenant identifier for data isolation

## Bug Details

### Bug Condition

The backend bug manifests when a user clicks the "claim" button on a task in the approval console. The `claim_task` function calls `_create_action_log` without passing the `tenant_id` parameter, resulting in a NULL value in the database.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type { task_id: int, user_id: int, tenant_id: int }
  OUTPUT: boolean

  RETURN claim_task_is_called(input)
         AND tenant_id_not_passed_to_create_action_log(input)
END FUNCTION
```

The frontend bugs manifest when:
- The approval workbench page is rendered (shows unwanted "轨迹" section)
- SLA overview displays tasks without due dates (shows "无截止" text)
- SLA status labels are rendered (incorrect font style assignments)

### Examples

**Backend Bug Example:**
- User clicks "claim" on task ID 12345
- Expected: `TaskActionLog` record created with `tenant_id = 1`
- Actual: `TaskActionLog` record created with `tenant_id = NULL`, database raises constraint violation

**Frontend Bug Examples:**
- Approval workbench displays a "轨迹" section that should be removed entirely
- SLA card shows "无截止" text for tasks without deadlines, which should not be displayed
- SLA status label "正常" uses warning-styled font instead of success-styled font

## Expected Behavior

### Preservation Requirements

**Backend Unchanged Behaviors:**
- `release_task` operation must continue to create action logs with proper `tenant_id`
- `perform_action` operation must continue to create action logs correctly
- `transfer_task` operation must continue to work as before
- `delegate_task` operation must continue to work as before
- Task queries and listings must return correct data

**Frontend Unchanged Behaviors:**
- Task list display must continue to work correctly
- SLA summary cards must continue to display valid status levels
- Other approval workbench sections must remain functional
- All interactive buttons (approve, reject, etc.) must continue to work

**Scope:**
All inputs that do NOT involve the `claim` operation should be completely unaffected by this backend fix. All UI components except the three specified bugs should remain unchanged.

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Missing Parameter in claim_task**: The `claim_task` function in `task_service.py` has access to the task's `tenant_id` but does not pass it to `_create_action_log`
   - The task object retrieved from the database contains `tenant_id`
   - The `_create_action_log` method signature accepts `tenant_id` parameter
   - The call site in `claim_task` omits this parameter

2. **Frontend Trace Component**: The "轨迹" section is likely a dedicated component that was added for debugging or historical reasons but is no longer needed
   - Component may be imported and rendered in the approval workbench template
   - Removing it should not affect other functionality

3. **Frontend "无截止" Display**: The SLA overview component has conditional logic to display "无截止" text for tasks without due dates
   - This text display should be removed from the template
   - Tasks without deadlines should simply not show any deadline information

4. **Frontend Label-Font Mismatch**: The SLA status labels are mapped to incorrect CSS classes
   - Normal status should use success/green styling
   - Warning status should use warning/yellow styling
   - Critical/Expired status should use error/red styling

## Correctness Properties

Property 1: Bug Condition - TaskActionLog tenant_id on Claim

_For any_ claim operation where `claim_task` is called, the fixed `_create_action_log` SHALL receive and persist the correct `tenant_id` from the task, preventing database constraint violations.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Other Operations Unchanged

_For any_ operation that is NOT a claim (release, perform_action, transfer, delegate), the fixed code SHALL produce action logs with the same behavior as the original code, preserving all existing functionality for non-claim operations.

**Validates: Requirements 3.1, 3.2**

Property 3: Frontend - Trace Section Removed

_For any_ render of the approval workbench, the fixed template SHALL NOT include the "轨迹" section, removing it from the user interface.

**Validates: Requirements 2.4**

Property 4: Frontend - "无截止" Status Removed

_For any_ SLA overview display of tasks without due dates, the fixed component SHALL NOT display "无截止" text.

**Validates: Requirements 2.5**

Property 5: Frontend - SLA Label-Font Correct Mapping

_For any_ SLA status label display, the fixed component SHALL correctly pair each label with its corresponding font style (normal→success, warning→warning, critical→error, expired→error).

**Validates: Requirements 2.6**

## Fix Implementation

### Backend Changes

**File**: `app/services/task_service.py` (or similar path)

**Function**: `claim_task`

**Specific Changes:**
1. **Add tenant_id parameter passing**: Locate the call to `_create_action_log` within `claim_task` and add the `tenant_id` parameter
   - Extract `tenant_id` from the task object before the action log creation
   - Pass `tenant_id=task.tenant_id` to the `_create_action_log` call

**Pseudocode:**
```
FUNCTION claim_task(task_id, user_id, db_session):
  task = db_session.query(Task).filter(Task.id == task_id).first()
  # ... existing validation code ...

  # FIX: Pass tenant_id to _create_action_log
  tenant_id = task.tenant_id

  _create_action_log(
    db=db_session,
    task_id=task_id,
    action="claim",
    user_id=user_id,
    tenant_id=tenant_id,  # ADD THIS LINE
    # ... other existing parameters ...
  )

  # ... rest of the function ...
END FUNCTION
```

### Frontend Changes

**File**: `src/views/approval/ApprovalWorkbench.vue` (or similar path)

**Change 1 - Remove Trace Section:**
1. Remove the import of the trace/timeline component
2. Remove the component from the template section
3. Remove any related data properties or methods

**Change 2 - Remove "无截止" Display:**
1. Locate the SLA overview template section
2. Remove the conditional rendering that displays "无截止" text
3. Tasks without deadlines should show nothing or a placeholder

**Change 3 - Fix Label-Font Mapping:**
1. Locate the SLA status label rendering code
2. Verify and correct the CSS class bindings:
   - `normal` status → `success` class (green)
   - `warning` status → `warning` class (yellow)
   - `critical` status → `error` class (red)
   - `expired` status → `error` class (red)

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Backend Goal**: Confirm that `claim_task` fails with NOT NULL violation when `tenant_id` is not passed.

**Test Plan**: 
1. Write a test that calls `claim_task` on a task
2. Verify the database raises constraint violation
3. Confirm the root cause is missing `tenant_id` parameter

**Test Cases**:
1. **Claim Task Test**: Call `claim_task` and expect database error (will fail on unfixed code)
2. **Other Operations Test**: Verify other operations work correctly (baseline)

**Expected Counterexamples**:
- Database constraint violation on `TaskActionLog.tenant_id`
- Error message: `psycopg2.errors.NotNullViolation: null value in column "tenant_id"`

**Frontend Goal**: Verify the three UI bugs exist before fixing.

**Test Plan**:
1. Render approval workbench and verify "轨迹" section is visible
2. Check SLA overview for "无截止" text
3. Inspect SLA labels and verify incorrect font styling

**Test Cases**:
1. **Trace Section Test**: Verify trace section exists (should be removed)
2. **No Deadline Text Test**: Verify "无截止" is displayed (should be removed)
3. **Label-Font Test**: Verify label-to-font mapping is incorrect (should be fixed)

### Fix Checking

**Backend Goal**: Verify that for all claim operations, the fixed function creates `TaskActionLog` with valid `tenant_id`.

**Pseudocode:**
```
FOR ALL task_id, user_id DO
  result := claim_task_fixed(task_id, user_id)
  ASSERT action_log.tenant_id IS NOT NULL
END FOR
```

**Frontend Goal**: Verify the three UI fixes are correctly applied.

**Pseudocode:**
```
FOR ALL approval_workbench_renders DO
  ASSERT trace_section NOT EXISTS
  ASSERT "无截止" NOT IN sla_overview
  ASSERT label_font_mapping IS CORRECT
END FOR
```

### Preservation Checking

**Backend Goal**: Verify that for all non-claim operations, the fixed code produces the same behavior as before.

**Pseudocode:**
```
FOR ALL operation IN [release, perform_action, transfer, delegate] DO
  FOR ALL input DO
    ASSERT original_function(input) = fixed_function(input)
  END FOR
END FOR
```

**Frontend Goal**: Verify that non-targeted UI components continue to work correctly.

**Test Plan**: After applying fixes, verify:
- Task list displays correctly
- SLA cards for valid statuses work
- Action buttons function properly

**Test Cases**:
1. **Task List Preservation**: Verify task list renders correctly after trace removal
2. **SLA Badge Preservation**: Verify SLA badges for valid statuses still display
3. **Button Functionality**: Verify approve/reject buttons still work

### Unit Tests

**Backend:**
- Test `claim_task` creates action log with correct `tenant_id`
- Test other operations continue to work correctly
- Test edge cases (task with null tenant_id, etc.)

**Frontend:**
- Test trace section is not rendered
- Test "无截止" is not displayed
- Test label-font mapping for all status types

### Property-Based Tests

**Backend:**
- Generate random tasks with different tenant_ids and verify claim operation works
- Generate random operations and verify behavior preservation

**Frontend:**
- Generate random SLA configurations and verify label styling
- Test various task states and verify UI consistency

### Integration Tests

**Backend:**
- Test full claim workflow from API call to database
- Test claim operation in multi-tenant context

**Frontend:**
- Test full approval workbench rendering
- Test SLA overview with various task configurations
- Test user interactions after fixes are applied