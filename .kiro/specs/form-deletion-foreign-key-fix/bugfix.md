# Bugfix Requirements Document

## Introduction

When users attempt to delete a form through the form management UI, the system fails with a `ForeignKeyViolation` error if the form has associated flow definitions. The database correctly prevents orphaned references, but the application doesn't handle this gracefully. Users receive a cryptic database error instead of a clear, actionable message. The fix should either prevent deletion when flow definitions exist or cascade-delete related flow definitions, depending on business requirements.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user attempts to delete a form that has associated flow_definition records THEN the system crashes with `sqlalchemy.exc.PendingRollbackError` and `psycopg2.errors.ForeignKeyViolation`

1.2 WHEN a user attempts to delete a form that has associated flow_definition records THEN the API returns a generic 500 error instead of a meaningful error message

1.3 WHEN a user attempts to delete a form that has associated flow_definition records THEN the database transaction is left in a failed state, requiring manual intervention

### Expected Behavior (Correct)

2.1 WHEN a user attempts to delete a form that has associated flow_definition records THEN the system SHALL return a 400 error with a clear message indicating the form cannot be deleted due to existing flow definitions

2.2 WHEN a user attempts to delete a form that has associated flow_definition records THEN the system SHALL gracefully handle the constraint violation without crashing

2.3 WHEN a user attempts to delete a form that has associated flow_definition records THEN the database transaction SHALL be properly rolled back without leaving the session in a failed state

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user attempts to delete a form with status "draft" and NO associated flow_definition records THEN the system SHALL CONTINUE TO successfully delete the form and all its related versions

3.2 WHEN a user attempts to delete a form with status other than "draft" THEN the system SHALL CONTINUE TO return an error indicating only draft forms can be deleted

3.3 WHEN a user attempts to delete a form they do not own THEN the system SHALL CONTINUE TO return an authorization error

3.4 WHEN a user successfully deletes a form THEN the system SHALL CONTINUE TO log the deletion action for audit purposes
