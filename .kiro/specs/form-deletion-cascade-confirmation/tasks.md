# Implementation Plan: Form Deletion with Cascade Confirmation

## Overview

This implementation plan breaks down the form deletion cascade confirmation feature into sequential, executable tasks. The feature enhances the form deletion workflow to support cascade deletion of associated flow definitions through a user-friendly confirmation dialog. Implementation follows a backend-first approach, establishing the API contract and service layer before frontend integration.

## Tasks

- [x] 1. Enhance FormService with cascade deletion detection and logic
  - [x] 1.1 Add `_get_associated_flow_definitions()` helper method to FormService
    - Query FlowDefinition records for the given form_id
    - Return list of flow definition metadata (id, name, version)
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 1.2 Write property test for flow definition detection
    - **Property 1: Flow Definition Detection**
    - **Validates: Requirements 1.1, 1.2**
    - Generate random forms with 0-N flow definitions
    - Verify detection returns correct count and metadata
  
  - [x] 1.3 Add `_cascade_delete_flow_definitions()` helper method to FormService
    - Delete FlowNode records for associated flow definitions
    - Delete FlowRoute records for associated flow definitions
    - Delete FlowSnapshot records for associated flow definitions
    - Delete FlowDraft records for associated flow definitions
    - Delete FlowDefinition records
    - Implement transaction with rollback on failure
    - Return count of deleted flow definitions
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 1.4 Write property test for cascade deletion atomicity
    - **Property 3: Cascade Deletion Atomicity**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - Generate random form with random flow definitions
    - Trigger cascade deletion and verify all related records deleted
    - Verify form no longer exists in database
  
  - [x] 1.5 Enhance `delete_form()` method in FormService
    - Add `cascade` parameter (default: False)
    - Validate user authorization (form owner check)
    - Validate form status is "draft"
    - Query for associated flow definitions
    - If flow definitions exist and cascade=False, raise BusinessError with 409 status
    - If cascade=True, call `_cascade_delete_flow_definitions()`
    - Delete FormVersion records
    - Delete Form record
    - Log deletion action with cascade flag
    - Return appropriate response metadata
    - _Requirements: 3.1, 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3_
  
  - [ ]* 1.6 Write property test for authorization validation
    - **Property 5: Authorization Validation**
    - **Validates: Requirements 4.1, 4.2**
    - Generate random user and form with different owner
    - Attempt deletion as non-owner
    - Verify authorization error returned and form not deleted
  
  - [ ]* 1.7 Write property test for form status validation
    - **Property 6: Form Status Validation**
    - **Validates: Requirements 4.3, 4.4**
    - Generate forms with random statuses (draft, published, archived)
    - Attempt deletion on each
    - Verify only draft forms can be deleted
  
  - [ ]* 1.8 Write property test for transaction rollback on failure
    - **Property 4: Transaction Rollback on Failure**
    - **Validates: Requirements 3.4, 5.1, 5.2**
    - Generate form with flow definitions
    - Simulate constraint violation during deletion
    - Verify transaction rolled back and form still exists
  
  - [ ]* 1.9 Write property test for audit trail logging
    - **Property 12: Audit Trail Logging**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - Generate random cascade deletion
    - Verify log entry contains form_id, user_id, tenant_id, timestamp, cascade flag

- [x] 2. Implement error handling and response schemas
  - [x] 2.1 Create Pydantic response schemas for cascade deletion
    - Create `FlowDefinitionMetadata` schema with id, name, version fields
    - Create `CascadeDeleteConflictResponse` schema with form_id, form_name, flow_definition_count, flow_definitions
    - Create `CascadeDeleteSuccessResponse` schema with form_id, form_name, deleted_flow_definitions, timestamp
    - _Requirements: 3.1, 5.1, 5.2_
  
  - [x] 2.2 Implement error handling in FormService.delete_form()
    - Catch IntegrityError and convert to BusinessError with 500 status
    - Catch OperationalError and convert to DatabaseError with 500 status
    - Ensure session is properly reset after failed transaction
    - Log error details for debugging
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 2.3 Write unit tests for error handling
    - Test IntegrityError handling during cascade deletion
    - Test OperationalError handling during cascade deletion
    - Test database state unchanged after failed transaction
    - Test session properly reset after rollback
    - _Requirements: 5.1, 5.2_

- [x] 3. Update DELETE /api/v1/forms/{form_id} endpoint
  - [x] 3.1 Add `cascade` query parameter to delete form route
    - Accept optional `cascade` boolean query parameter (default: false)
    - Pass cascade flag to FormService.delete_form()
    - _Requirements: 2.6, 3.1_
  
  - [x] 3.2 Update route response handling for cascade scenarios
    - Return 409 Conflict with CascadeDeleteConflictResponse when flow definitions exist and cascade=false
    - Return 200 OK with CascadeDeleteSuccessResponse when cascade deletion succeeds
    - Return 200 OK with standard response when standard deletion succeeds
    - Return 400 Bad Request for form status errors
    - Return 403 Forbidden for authorization errors
    - Return 500 Internal Server Error for cascade deletion failures
    - _Requirements: 3.1, 5.1, 5.2_
  
  - [ ]* 3.3 Write unit tests for route parameter handling
    - Test cascade parameter is correctly parsed
    - Test cascade=true triggers cascade deletion
    - Test cascade=false (default) returns 409 when flow definitions exist
    - _Requirements: 2.6, 3.1_

- [x] 4. Checkpoint - Ensure all backend tests pass
  - Ensure all backend unit tests pass
  - Ensure all backend property tests pass
  - Verify no regressions in existing form deletion tests
  - Ask the user if questions arise

- [x] 5. Create CascadeDeleteConfirmDialog Vue component
  - [x] 5.1 Create CascadeDeleteConfirmDialog.vue component
    - Define Props interface with visible, formId, formName, flowDefinitionCount, flowDefinitions, loading
    - Define Emits interface with update:visible, confirm, cancel events
    - Render modal dialog with form name and flow definition count
    - Display list of flow definitions to be deleted
    - Render "Cancel" and "Confirm Delete" buttons
    - Show loading state during deletion
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 5.2 Write property test for cascade confirmation dialog display
    - **Property 7: Cascade Confirmation Dialog Display**
    - **Validates: Requirements 2.1, 2.2**
    - Generate random 409 responses with flow definition metadata
    - Render component with response data
    - Verify dialog is displayed with correct form name and count
  
  - [x] 5.3 Implement dialog cancel action
    - Emit 'update:visible' event with false value
    - Emit 'cancel' event
    - Close dialog without triggering deletion
    - _Requirements: 2.5_
  
  - [ ]* 5.4 Write property test for dialog cancel action
    - **Property 8: Dialog Cancel Action**
    - **Validates: Requirements 2.5**
    - Generate random dialog state
    - Simulate cancel click
    - Verify dialog closes and no API call made
  
  - [x] 5.5 Implement dialog confirm action
    - Emit 'confirm' event
    - Emit 'update:visible' event with false value
    - _Requirements: 2.6_
  
  - [ ]* 5.6 Write property test for dialog confirm action
    - **Property 9: Dialog Confirm Action**
    - **Validates: Requirements 2.6**
    - Generate random dialog state
    - Simulate confirm click
    - Verify confirm event emitted

- [x] 6. Enhance FormManagement.vue component
  - [x] 6.1 Add cascade deletion state management
    - Add `showCascadeDialog` ref for dialog visibility
    - Add `cascadeDialogData` ref for flow definition metadata
    - Add `deleteLoading` ref for loading state
    - _Requirements: 2.1, 2.2_
  
  - [x] 6.2 Enhance `handleDeleteForm()` method
    - Wrap deleteForm() call in try-catch
    - Catch 409 Conflict response and extract flow definition metadata
    - Set cascadeDialogData and show cascade dialog
    - Handle other error codes (4002, 4003, 5001) with appropriate error notifications
    - _Requirements: 2.1, 5.3, 5.4_
  
  - [ ]* 6.3 Write unit tests for delete handler error handling
    - Test 409 response triggers cascade dialog display
    - Test 4002 response shows form status error notification
    - Test 4003 response shows authorization error notification
    - Test 5001 response shows cascade deletion failure notification
    - _Requirements: 5.3, 5.4_
  
  - [x] 6.4 Implement `handleCascadeConfirm()` method
    - Call deleteForm() with cascade=true parameter
    - Show loading state during deletion
    - Display success notification on completion
    - Close cascade dialog
    - Refresh form list
    - Handle errors with error notification
    - _Requirements: 2.6, 6.1, 6.3, 6.4_
  
  - [ ]* 6.5 Write property test for success notification and list refresh
    - **Property 10: Success Notification and List Refresh**
    - **Validates: Requirements 6.1, 6.3, 6.4**
    - Generate random successful deletion response
    - Verify success notification displayed
    - Verify form list refresh triggered
    - Verify deleted form not in refreshed list
  
  - [x] 6.6 Implement `handleCascadeCancel()` method
    - Close cascade dialog
    - Clear cascadeDialogData
    - _Requirements: 2.5_
  
  - [ ]* 6.7 Write property test for error handling and UI state recovery
    - **Property 11: Error Handling and UI State Recovery**
    - **Validates: Requirements 5.3, 5.4**
    - Generate random failed deletion response
    - Verify error notification displayed
    - Verify dialog remains open for retry

- [x] 7. Update API client layer
  - [x] 7.1 Enhance deleteForm() function in src/api/form.ts
    - Add optional `options` parameter with cascade property
    - Build query string with cascade=true when option is set
    - Send DELETE request with query parameters
    - Return response with proper typing
    - _Requirements: 2.6, 3.1_
  
  - [ ]* 7.2 Write unit tests for API client
    - Test deleteForm() without cascade parameter
    - Test deleteForm() with cascade=true parameter
    - Test query string is correctly formatted
    - _Requirements: 2.6, 3.1_

- [ ] 8. Implement backward compatibility verification
  - [ ] 8.1 Verify standard deletion for forms without flow definitions
    - Test delete request on form with no flow definitions
    - Verify no cascade dialog displayed
    - Verify standard deletion completes successfully
    - _Requirements: 8.1, 8.2_
  
  - [ ]* 8.2 Write property test for backward compatibility - no dialog for forms without flow definitions
    - **Property 13: Backward Compatibility - No Dialog for Forms Without Flow Definitions**
    - **Validates: Requirements 8.1, 8.2**
    - Generate random form without flow definitions
    - Trigger delete and verify no dialog shown
  
  - [ ] 8.3 Verify non-draft form rejection
    - Test delete request on published form
    - Verify error returned regardless of flow definitions
    - _Requirements: 8.3_
  
  - [ ]* 8.4 Write property test for backward compatibility - non-draft form rejection
    - **Property 14: Backward Compatibility - Non-Draft Form Rejection**
    - **Validates: Requirements 8.3**
    - Generate forms with random statuses
    - Verify only draft forms can be deleted
  
  - [ ] 8.5 Verify authorization rejection
    - Test delete request from non-owner user
    - Verify error returned regardless of flow definitions
    - _Requirements: 8.4_
  
  - [ ]* 8.6 Write property test for backward compatibility - authorization rejection
    - **Property 15: Backward Compatibility - Authorization Rejection**
    - **Validates: Requirements 8.4**
    - Generate random non-owner user
    - Verify authorization error returned

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all backend tests pass
  - Ensure all frontend tests pass
  - Ensure all property tests pass
  - Verify no regressions in existing functionality
  - Ask the user if questions arise

- [ ] 10. Integration testing
  - [ ] 10.1 Test end-to-end cascade deletion workflow
    - Create form with associated flow definitions
    - Initiate delete request
    - Verify 409 response with flow definition metadata
    - Verify cascade dialog displays correctly
    - Confirm cascade deletion
    - Verify form and flow definitions deleted
    - Verify form list refreshed
    - _Requirements: 1.1, 2.1, 2.2, 2.6, 3.1, 6.1, 6.3, 6.4_
  
  - [ ] 10.2 Test end-to-end standard deletion workflow
    - Create form without flow definitions
    - Initiate delete request
    - Verify form deleted without dialog
    - Verify form list refreshed
    - _Requirements: 8.1, 8.2_
  
  - [ ] 10.3 Test error scenarios
    - Test cascade deletion with constraint violation
    - Verify error notification displayed
    - Verify form not deleted
    - Verify database state unchanged
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all backend tests pass
  - Ensure all frontend tests pass
  - Ensure all integration tests pass
  - Verify all requirements are covered
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Backend implementation must complete before frontend integration
- All cascade deletion operations must be atomic (all-or-nothing)
- Property tests validate universal correctness properties across randomized inputs
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation and early error detection
