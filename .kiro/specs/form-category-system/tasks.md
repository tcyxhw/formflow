# Implementation Plan: Form Category System

## Overview

This implementation plan breaks down the Form Category System feature into discrete, incremental coding tasks. The system adds category management and filtering capabilities to FormFlow, enabling users to organize forms by category and filter them during search. Implementation follows a backend-first approach: database models and services are established first, followed by API routes, then frontend components and state management.

---

## Tasks

### Phase 1: Database & Backend Models

- [x] 1. Create Category ORM model and database migration
  - Create `backend/app/models/category.py` with Category model
    - Fields: id, tenant_id, name, is_default, created_at, updated_at
    - Relationships: ForeignKey to Tenant, relationship to Form
    - Unique constraint on (tenant_id, name)
    - Inherit from TenantMixin and TimestampMixin
  - Create Alembic migration to add category table
  - Add category_id foreign key to Form model in migration
  - Create indexes on (tenant_id) and (tenant_id, category_id)
  - _Requirements: 4.1, 4.2, 8.1_

- [x] 2. Update Form model with category relationship
  - Modify `backend/app/models/form.py` to add category_id field
  - Add relationship to Category model
  - Ensure foreign key constraint with ON DELETE SET NULL
  - _Requirements: 4.2_

- [x] 3. Create database migration for existing tenants
  - Create Alembic migration script
  - Create default "Uncategorized" category for each existing tenant
  - Backfill all existing forms with default category_id
  - Add NOT NULL constraint to form.category_id after backfill
  - _Requirements: 8.1, 4.3_

### Phase 2: Backend Schemas & Services

- [x] 4. Create Pydantic schemas for category operations
  - Create `backend/app/schemas/category_schemas.py`
  - Define CategoryCreateRequest with name field (1-50 chars)
  - Define CategoryUpdateRequest with name field (1-50 chars)
  - Define CategoryResponse with id, name, is_default, created_at, updated_at
  - Define CategoryListResponse with items, total, page, page_size
  - _Requirements: 1.5, 5.1_

- [x] 5. Implement CategoryService with CRUD operations
  - Create `backend/app/services/category_service.py`
  - Implement `create_category(tenant_id, name)` with validation
    - Validate name length (1-50 characters)
    - Check for duplicate names within tenant
    - Raise appropriate exceptions (ValidationError, ConflictError)
  - Implement `get_categories(tenant_id, page, page_size)` with pagination
  - Implement `get_category(tenant_id, category_id)` with tenant isolation check
  - Implement `update_category(tenant_id, category_id, name)` with validation
  - Implement `delete_category(tenant_id, category_id)` with cascading logic
    - Prevent deletion of default category
    - Find all forms with this category
    - Reassign forms to default category
    - Delete category record
  - Implement `get_default_category(tenant_id)` helper
  - Implement `initialize_default_category(tenant_id)` for new tenants
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 8.1, 8.3, 8.4_

- [x] 6. Implement category validation and error handling
  - Add validation for category name (empty, length > 50)
  - Add duplicate name check within tenant scope
  - Add default category protection logic
  - Raise ValidationError for invalid names
  - Raise ConflictError for duplicate names
  - Raise PermissionError for cross-tenant access
  - _Requirements: 1.5, 1.6, 8.4_

- [x] 7. Update FormService to support category assignment
  - Modify `backend/app/services/form_service.py`
  - Update `create_form()` to assign default category if not provided
  - Update `update_form()` to support category_id parameter
  - Add category validation (ensure category belongs to tenant)
  - Update form response to include category information
  - _Requirements: 2.2, 2.5, 4.3, 4.5_

- [x] 8. Implement form filtering by category
  - Add `get_forms_by_category(tenant_id, category_id, page, page_size)` to FormService
  - Support category_id=None for "All Categories" filter
  - Return forms with category information (id, name)
  - Apply both tenant_id and category_id filters
  - _Requirements: 3.2, 3.3, 5.5_

### Phase 3: Backend API Routes

- [x] 9. Create categories API route file
  - Create `backend/app/api/v1/categories.py`
  - Set up router with prefix `/categories`
  - Import CategoryService and dependencies
  - Add tenant_id extraction from request context
  - _Requirements: 5.1, 5.6_

- [x] 10. Implement GET /api/v1/categories endpoint
  - List all categories for authenticated tenant with pagination
  - Query parameters: page (default 1), page_size (default 20)
  - Response: CategoryListResponse with items, total, page, page_size
  - Apply tenant isolation check
  - Handle errors: 401 Unauthorized, 403 Forbidden
  - _Requirements: 1.1, 5.1, 5.6, 7.1_

- [x] 11. Implement POST /api/v1/categories endpoint
  - Create new category for authenticated tenant
  - Request body: CategoryCreateRequest with name
  - Response: CategoryResponse with 201 Created status
  - Validate name (1-50 characters)
  - Check for duplicate names within tenant
  - Handle errors: 400 Bad Request, 409 Conflict, 401 Unauthorized
  - _Requirements: 1.2, 1.5, 1.6, 5.2, 5.6_

- [x] 12. Implement PUT /api/v1/categories/{category_id} endpoint
  - Update category name for authenticated tenant
  - Path parameter: category_id
  - Request body: CategoryUpdateRequest with name
  - Response: CategoryResponse with updated data
  - Validate name (1-50 characters)
  - Check for duplicate names within tenant
  - Apply tenant isolation check
  - Handle errors: 400 Bad Request, 403 Forbidden, 404 Not Found, 409 Conflict
  - _Requirements: 1.3, 1.5, 1.6, 5.3, 5.6, 7.2_

- [x] 13. Implement DELETE /api/v1/categories/{category_id} endpoint
  - Delete category and reassign forms to default category
  - Path parameter: category_id
  - Response: 204 No Content on success
  - Prevent deletion of default category (400 Bad Request)
  - Apply tenant isolation check
  - Trigger cascading reassignment logic
  - Handle errors: 400 Bad Request, 403 Forbidden, 404 Not Found
  - _Requirements: 1.4, 5.4, 5.6, 7.2, 8.3, 8.4_

- [x] 14. Update forms API to support category filtering
  - Modify `backend/app/api/v1/forms.py` GET endpoint
  - Add optional query parameter: category_id
  - Support category_id=null for "All Categories"
  - Call FormService.get_forms_by_category() when category_id provided
  - Include category information in form response (id, name)
  - Apply tenant isolation check
  - _Requirements: 3.2, 3.3, 3.4, 5.5, 5.6, 7.4_

- [x] 15. Register categories router in main API
  - Update `backend/app/api/router.py` or `backend/app/main.py`
  - Include categories router with prefix `/api/v1`
  - Ensure router is registered before application startup
  - _Requirements: 5.1_

### Phase 4: Frontend Types & API Client

- [x] 16. Create category TypeScript types
  - Create `my-app/src/types/category.ts`
  - Define Category interface: id, name, is_default, created_at, updated_at
  - Define CategoryCreateRequest: name
  - Define CategoryUpdateRequest: name
  - Define CategoryResponse: Category
  - Define CategoryListResponse: items[], total, page, page_size
  - _Requirements: 5.1, 5.2_

- [x] 17. Create category API client functions
  - Create `my-app/src/api/category.ts`
  - Implement `listCategories(page?: number, pageSize?: number)` - GET /categories
  - Implement `createCategory(data: CategoryCreateRequest)` - POST /categories
  - Implement `updateCategory(id: number, data: CategoryUpdateRequest)` - PUT /categories/{id}
  - Implement `deleteCategory(id: number)` - DELETE /categories/{id}
  - Handle API errors and return typed responses
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

### Phase 5: Frontend State Management

- [x] 18. Create Pinia category store
  - Create `my-app/src/stores/useCategory.ts`
  - Define state: categories[], loading, error
  - Implement action `fetchCategories()` - calls listCategories API
  - Implement action `createCategory(name)` - calls createCategory API, updates state
  - Implement action `updateCategory(id, name)` - calls updateCategory API, updates state
  - Implement action `deleteCategory(id)` - calls deleteCategory API, updates state
  - Implement getter `defaultCategory` - returns category with is_default=true
  - Implement getter `categoryMap` - returns Map<id, Category> for quick lookup
  - Handle loading and error states
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.1_

- [x] 19. Implement store error handling and notifications
  - Add error state management to useCategoryStore
  - Display toast notifications on API errors
  - Handle specific error cases: 409 Conflict, 400 Bad Request, 403 Forbidden
  - Clear error state on successful operations
  - _Requirements: 6.4_

### Phase 6: Frontend Components

- [x] 20. Create CategoryDropdown component
  - Create `my-app/src/components/form/CategoryDropdown.vue`
  - Props: modelValue (number), disabled (boolean)
  - Emits: update:modelValue
  - Display NSelect with category options
  - Show loading state while fetching categories
  - Show empty state message if no categories
  - Fetch categories on component mount
  - _Requirements: 2.1, 2.3, 2.4, 6.1, 6.3_

- [x] 21. Create CategoryFilter component
  - Create `my-app/src/components/form/CategoryFilter.vue`
  - Props: modelValue (number | null)
  - Emits: update:modelValue
  - Display NSelect with "All Categories" option plus category list
  - Fetch categories on component mount
  - Persist filter selection to sessionStorage
  - Restore filter selection from sessionStorage on mount
  - _Requirements: 3.1, 3.5, 6.1_

- [x] 22. Integrate CategoryDropdown into form builder
  - Modify `my-app/src/components/FormDesigner/FormSettings.vue` or form creation component
  - Add CategoryDropdown component to form settings
  - Bind to formDesigner store's category_id
  - Display category dropdown near form name field
  - Show tooltip explaining category purpose
  - Validate category selection before form save
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1, 6.2_

- [x] 23. Integrate CategoryFilter into form search/list
  - Modify `my-app/src/views/form/List.vue` or form list component
  - Add CategoryFilter component to filter panel
  - Bind to form list query parameters
  - Update form list query when category filter changes
  - Display category name in form list items
  - _Requirements: 3.1, 3.4, 3.5, 6.1_

- [x] 24. Update form list display to show category information
  - Modify form card/list item component to display category name
  - Show category as badge or label in form list
  - Handle case where category is null (show default category name)
  - _Requirements: 3.4_

### Phase 7: Testing & Validation

- [x] 25. Write backend unit tests for CategoryService
  - Create `backend/tests/test_category_service.py`
  - Test create_category with valid name
  - Test create_category with invalid name (empty, too long)
  - Test create_category with duplicate name (409 Conflict)
  - Test get_categories with pagination
  - Test get_category with tenant isolation
  - Test update_category with valid name
  - Test update_category with duplicate name
  - Test delete_category with cascading reassignment
  - Test delete_category prevents default category deletion
  - Test get_default_category returns correct category
  - Test initialize_default_category creates default category
  - _Requirements: 1.1-1.6, 8.1, 8.3, 8.4_

- [x] 26. Write property-based tests for category correctness
  - Create `backend/tests/test_category_properties.py`
  - **Property 1: Category Uniqueness Within Tenant**
    - Generate random tenant IDs and category names
    - Create category, attempt duplicate creation
    - Verify 409 Conflict error on duplicate
    - _Validates: Requirements 1.6_
  
  - **Property 2: Category Name Validation**
    - Generate category names of various lengths (0, 1, 50, 51+ chars)
    - Verify empty/long names rejected with 400 Bad Request
    - Verify valid names (1-50 chars) accepted
    - _Validates: Requirements 1.5_
  
  - **Property 3: Cascading Category Deletion**
    - Create category with multiple forms assigned
    - Delete category
    - Verify all forms reassigned to default category
    - Verify category record deleted
    - _Validates: Requirements 1.4, 4.4, 8.3_
  
  - **Property 4: Default Category Protection**
    - Attempt to delete default category
    - Verify 400 Bad Request error
    - Verify default category still exists
    - _Validates: Requirements 8.4_
  
  - **Property 5: Form Default Category Assignment**
    - Create form without explicit category
    - Verify form assigned to default category
    - _Validates: Requirements 4.3, 8.2_
  
  - **Property 6: Multi-Tenant Category Isolation**
    - Create categories in Tenant A and Tenant B
    - Attempt cross-tenant access from Tenant A
    - Verify 403 Forbidden error
    - Verify Tenant A can only see own categories
    - _Validates: Requirements 7.1, 7.2, 7.3_
  
  - **Property 7: Category Filtering Accuracy**
    - Create forms with different categories
    - Filter by category_id
    - Verify all returned forms have specified category
    - Verify no forms from other categories included
    - _Validates: Requirements 3.2, 5.5_
  
  - **Property 8: All Categories Filter**
    - Create forms with different categories
    - Query with category_id=null
    - Verify all forms returned regardless of category
    - _Validates: Requirements 3.3_
  
  - **Property 9: Category Information Persistence**
    - Create form with category assignment
    - Query form
    - Verify returned category_id matches assigned value
    - _Validates: Requirements 2.5, 4.5_
  
  - **Property 11: Default Category Initialization**
    - Create new tenant
    - Verify default category "Uncategorized" exists
    - Verify is_default flag set to true
    - _Validates: Requirements 8.1_
  
  - **Property 12: Category List Pagination**
    - Create multiple categories (> page_size)
    - Query with pagination
    - Verify response includes total, page, page_size
    - Verify only authenticated tenant's categories returned
    - _Validates: Requirements 5.1_

- [x] 27. Write frontend component tests
  - Create `my-app/src/components/form/__tests__/CategoryDropdown.spec.ts`
  - Test CategoryDropdown renders with categories
  - Test CategoryDropdown emits update:modelValue on selection
  - Test CategoryDropdown shows loading state
  - Test CategoryDropdown shows empty state
  - Create `my-app/src/components/form/__tests__/CategoryFilter.spec.ts`
  - Test CategoryFilter renders with "All Categories" option
  - Test CategoryFilter emits update:modelValue on selection
  - Test CategoryFilter persists selection to sessionStorage
  - _Requirements: 2.1, 2.4, 3.1, 3.5, 6.5_

- [x] 28. Write frontend store tests
  - Create `my-app/src/stores/__tests__/useCategory.spec.ts`
  - Test fetchCategories action
  - Test createCategory action updates state
  - Test updateCategory action updates state
  - Test deleteCategory action updates state
  - Test defaultCategory getter
  - Test categoryMap getter
  - Test error handling
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 29. Checkpoint - Ensure all backend tests pass
  - Run pytest for all category tests
  - Verify all unit tests pass
  - Verify all property-based tests pass (minimum 100 iterations)
  - Verify no regressions in existing tests
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: All_

- [x] 30. Checkpoint - Ensure all frontend tests pass
  - Run npm run test for all category tests
  - Verify all component tests pass
  - Verify all store tests pass
  - Verify no regressions in existing tests
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: All_

### Phase 8: Integration & Verification

- [x] 31. Write integration tests for category workflow
  - Create `backend/tests/test_category_integration.py`
  - Test end-to-end category creation workflow
  - Test end-to-end form creation with category assignment
  - Test end-to-end form filtering by category
  - Test end-to-end category deletion with cascading reassignment
  - Test multi-tenant isolation across workflows
  - _Requirements: 1.1-1.6, 2.1-2.5, 3.1-3.5, 4.1-4.5, 5.1-5.6, 7.1-7.4, 8.1-8.4_

- [x] 32. Verify database migration and schema
  - Run Alembic migration: `alembic upgrade head`
  - Verify category table created with correct schema
  - Verify form table has category_id foreign key
  - Verify indexes created on (tenant_id) and (tenant_id, category_id)
  - Verify default categories created for existing tenants
  - Verify all existing forms have category_id assigned
  - _Requirements: 4.1, 4.2, 8.1_

- [x] 33. Verify API endpoints with manual testing
  - Test GET /api/v1/categories returns paginated list
  - Test POST /api/v1/categories creates category
  - Test PUT /api/v1/categories/{id} updates category
  - Test DELETE /api/v1/categories/{id} deletes category
  - Test GET /api/v1/forms?category_id={id} filters forms
  - Test error cases: 400, 403, 404, 409 responses
  - Test tenant isolation: cross-tenant access returns 403
  - Use Swagger UI at /api/v1/docs for manual testing
  - _Requirements: 5.1-5.6_

- [x] 34. Verify frontend components in browser
  - Test CategoryDropdown renders in form builder
  - Test CategoryDropdown displays all categories
  - Test CategoryDropdown selection updates form
  - Test CategoryFilter renders in form list
  - Test CategoryFilter displays "All Categories" option
  - Test CategoryFilter selection filters form list
  - Test category names display in form list items
  - Test filter selection persists across page navigation
  - _Requirements: 2.1-2.5, 3.1-3.5, 6.1-6.5_

- [x] 35. Final checkpoint - Ensure all tests pass
  - Run full test suite: `pytest` (backend) and `npm run test` (frontend)
  - Verify all unit tests pass
  - Verify all property-based tests pass
  - Verify all integration tests pass
  - Verify no regressions in existing functionality
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: All_

---

## Implementation Notes

### Backend Implementation Order
1. Create Category model and migration (Task 1-3)
2. Create schemas and CategoryService (Task 4-8)
3. Create API routes (Task 9-15)
4. Write tests (Task 25-26)
5. Verify integration (Task 31-35)

### Frontend Implementation Order
1. Create types and API client (Task 16-17)
2. Create Pinia store (Task 18-19)
3. Create components (Task 20-24)
4. Write tests (Task 27-28)
5. Verify integration (Task 34-35)

### Key Design Decisions
- **Cascading Reassignment**: Forms are reassigned to default category on deletion, not deleted
- **Default Category Protection**: Default category cannot be deleted to ensure forms always have valid assignment
- **Tenant Isolation**: Enforced at both API and database levels for security
- **Session-Based Filter**: Category filter persists in sessionStorage for UX continuity
- **Pagination**: All list endpoints support pagination for scalability

### Testing Strategy
- Property-based tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Minimum 100 iterations for property-based tests
- All tests must pass before proceeding to next phase

### Error Handling
- 400 Bad Request: Invalid input (empty name, name too long, default category deletion)
- 403 Forbidden: Cross-tenant access or permission denied
- 404 Not Found: Category or form not found
- 409 Conflict: Duplicate category name within tenant
- 401 Unauthorized: Missing or invalid authentication token

