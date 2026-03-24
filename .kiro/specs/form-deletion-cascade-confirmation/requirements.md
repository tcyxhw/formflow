# Requirements Document: Form Deletion with Cascade Confirmation

## Introduction

Currently, when users attempt to delete a form that has associated flow definitions, the system returns a 400 error preventing deletion. This feature enhances the user experience by allowing users to delete forms with associated flow definitions through a confirmation dialog. The dialog clearly indicates what will be deleted (the form and its flow definitions), and upon confirmation, both the form and its associated flow definitions are cascade-deleted in a single transaction.

## Glossary

- **Form**: A data collection template that users can fill out and submit
- **Flow_Definition**: An approval workflow configuration associated with a form that defines the approval process
- **Cascade_Delete**: Deleting a parent record and automatically deleting all associated child records in a single transaction
- **Confirmation_Dialog**: A modal UI component that requires explicit user confirmation before performing a destructive action
- **Draft_Status**: The initial state of a form before it is published
- **Tenant**: An isolated organizational unit in the multi-tenant system
- **Transaction**: A database operation that either completes entirely or rolls back entirely

## Requirements

### Requirement 1: Detect Forms with Associated Flow Definitions

**User Story:** As a form owner, I want the system to detect when my form has associated flow definitions, so that I can be informed before attempting deletion.

#### Acceptance Criteria

1. WHEN a user initiates a delete action on a form, THE Form_Service SHALL query the database to check if any Flow_Definition records exist for that form
2. WHEN Flow_Definition records exist for the form, THE Form_Service SHALL return metadata indicating the count and details of associated flow definitions
3. WHEN no Flow_Definition records exist for the form, THE Form_Service SHALL proceed with standard deletion logic

### Requirement 2: Display Cascade Deletion Confirmation Dialog

**User Story:** As a form owner, I want to see a confirmation dialog before deleting a form with flow definitions, so that I understand the consequences of my action.

#### Acceptance Criteria

1. WHEN the frontend receives a response indicating associated flow definitions exist, THE Form_Management_UI SHALL display a confirmation dialog
2. THE Confirmation_Dialog SHALL display the form name and the count of associated flow definitions
3. THE Confirmation_Dialog SHALL clearly state that both the form and all associated flow definitions will be permanently deleted
4. THE Confirmation_Dialog SHALL provide two action buttons: "Cancel" and "Confirm Delete"
5. WHEN the user clicks "Cancel", THE Dialog SHALL close without performing any deletion
6. WHEN the user clicks "Confirm Delete", THE Frontend SHALL send a cascade deletion request to the backend

### Requirement 3: Cascade Delete Form and Flow Definitions

**User Story:** As a form owner, I want to delete a form and its associated flow definitions in a single operation, so that I can clean up related data efficiently.

#### Acceptance Criteria

1. WHEN a user confirms cascade deletion, THE Form_Service SHALL delete all Flow_Definition records associated with the form in a single transaction
2. WHEN all Flow_Definition records are deleted, THE Form_Service SHALL delete all FormVersion records associated with the form
3. WHEN all related records are deleted, THE Form_Service SHALL delete the Form record itself
4. IF any deletion step fails, THE Form_Service SHALL rollback the entire transaction and return an error
5. WHEN cascade deletion completes successfully, THE Form_Service SHALL return a success response with the deleted form ID

### Requirement 4: Validate Authorization and Form Status

**User Story:** As a system administrator, I want to ensure only authorized users can delete forms, so that data integrity is maintained.

#### Acceptance Criteria

1. WHEN a user attempts to delete a form, THE Form_Service SHALL verify the user is the form owner
2. IF the user is not the form owner, THEN THE Form_Service SHALL return an authorization error and abort the deletion
3. WHEN a user attempts to delete a form, THE Form_Service SHALL verify the form status is "draft"
4. IF the form status is not "draft", THEN THE Form_Service SHALL return an error indicating only draft forms can be deleted

### Requirement 5: Handle Cascade Deletion Errors

**User Story:** As a user, I want clear error messages when cascade deletion fails, so that I can understand what went wrong.

#### Acceptance Criteria

1. IF a database constraint violation occurs during cascade deletion, THEN THE Form_Service SHALL catch the exception and return a 500 error with a descriptive message
2. IF a transaction rollback occurs, THEN THE Form_Service SHALL ensure the database session is properly reset
3. WHEN cascade deletion fails, THE Frontend SHALL display an error message to the user
4. WHEN cascade deletion fails, THE Form_Management_UI SHALL remain in a valid state allowing the user to retry or cancel

### Requirement 6: Display Success Confirmation

**User Story:** As a form owner, I want to see a success message after deleting a form, so that I know the operation completed.

#### Acceptance Criteria

1. WHEN cascade deletion completes successfully, THE Frontend SHALL display a success notification message
2. THE Success_Message SHALL indicate that the form and its associated flow definitions have been deleted
3. WHEN the success message is displayed, THE Form_Management_UI SHALL refresh the form list to reflect the deletion
4. WHEN the form list is refreshed, THE deleted form SHALL no longer appear in the list

### Requirement 7: Maintain Audit Trail

**User Story:** As a system administrator, I want to maintain an audit trail of form deletions, so that I can track data changes.

#### Acceptance Criteria

1. WHEN a form is cascade-deleted, THE Form_Service SHALL log the deletion action with the form ID, user ID, and tenant ID
2. THE Log_Entry SHALL include a timestamp of when the deletion occurred
3. THE Log_Entry SHALL indicate that the deletion included associated flow definitions

### Requirement 8: Preserve Existing Deletion Behavior

**User Story:** As a form owner, I want existing deletion behavior to remain unchanged for forms without flow definitions, so that the system remains stable.

#### Acceptance Criteria

1. WHEN a user deletes a form with no associated flow definitions, THE Form_Service SHALL continue to use the existing deletion logic
2. WHEN a user deletes a form without flow definitions, THE Frontend SHALL NOT display a confirmation dialog
3. WHEN a user attempts to delete a non-draft form, THE Form_Service SHALL continue to return an error
4. WHEN a user attempts to delete a form they do not own, THE Form_Service SHALL continue to return an authorization error
