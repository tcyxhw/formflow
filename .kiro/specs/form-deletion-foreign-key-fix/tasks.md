# Implementation Plan

## Phase 1: Exploratory Bug Condition Testing

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Form Deletion with Flow Definitions
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: For deterministic bugs, scope the property to the concrete failing case(s) to ensure reproducibility
  - Test implementation details from Bug Condition in design:
    - Create a form with status "draft"
    - Create a flow definition for that form
    - Attempt to delete the form
    - Assert that deletion fails with a 400 error (not 500)
    - Assert error message contains "flow definitions"
  - The test assertions should match the Expected Behavior Properties from design:
    - Deletion should return 400 error with clear message
    - Transaction should be properly rolled back
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause:
    - Current behavior: 500 error with generic message
    - Expected behavior: 400 error with specific message about flow definitions
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3_

## Phase 2: Preservation Testing

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Form Deletion Without Flow Definitions
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs:
    - Deleting draft forms without flow definitions succeeds
    - Deleting published forms returns appropriate error
    - Deleting forms without permission returns authorization error
    - Deleting forms removes all associated versions
    - Deletion is logged for audit purposes
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For all draft forms without flow definitions, deletion succeeds
    - For all published forms, deletion fails with appropriate error
    - For all forms without permission, deletion fails with authorization error
    - For all deleted forms, all associated versions are removed
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

## Phase 3: Implementation

- [x] 3. Fix for form deletion with flow definitions

  - [x] 3.1 Implement the fix
    - Add flow definition check before form deletion in `backend/app/services/form_service.py`
    - Query for existing flow_definition records for the form
    - Raise BusinessError with clear message if flow definitions exist
    - Import FlowDefinition model from app.models.workflow
    - Implementation details:
      - Check: `db.query(FlowDefinition).filter(FlowDefinition.form_id == form_id).first()`
      - If found, raise: `BusinessError("Cannot delete form with existing flow definitions. Please delete the associated flow definitions first.")`
      - This ensures proper error handling and transaction rollback
    - _Bug_Condition: isBugCondition(input) where form has associated flow_definition records_
    - _Expected_Behavior: Return 400 error with clear message, properly rollback transaction_
    - _Preservation: Forms without flow definitions continue to delete successfully, all other form operations unaffected_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Form Deletion with Flow Definitions
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify that deletion now returns 400 error with specific message
    - Verify that transaction is properly rolled back
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Form Deletion Without Flow Definitions
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - Verify that forms without flow definitions still delete successfully
    - Verify that all other deletion behaviors are unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

## Phase 4: Checkpoint

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
