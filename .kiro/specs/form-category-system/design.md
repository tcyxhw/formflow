# Design Document: Form Category System

## Overview

The Form Category System provides a multi-tenant category management solution for organizing and filtering forms within FormFlow. This design enables users to create custom categories, assign them to forms during creation/editing, and filter forms by category during search. The system maintains strict tenant isolation and ensures data integrity through referential constraints and cascading reassignments.

### Key Design Principles

1. **Tenant Isolation**: All categories are scoped to tenants; cross-tenant access is prevented at the API and database levels
2. **Data Integrity**: Forms always have valid category assignments; deletion triggers cascading reassignment to default category
3. **User Experience**: Category selection is seamless in form builder and search interfaces with immediate UI updates
4. **Performance**: Efficient queries through proper database relationships and indexing

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue3)                         │
├─────────────────────────────────────────────────────────────┤
│  • CategoryDropdown (Form Builder)                          │
│  • CategoryFilter (Form Search)                             │
│  • useCategoryStore (Pinia)                                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│  API Routes:                                                │
│  • GET/POST /api/v1/categories                              │
│  • PUT/DELETE /api/v1/categories/{id}                       │
│  • GET /api/v1/forms?category_id={id}                       │
│                                                             │
│  Services:                                                  │
│  • CategoryService (CRUD, validation, cascading)            │
│  • FormService (category assignment, filtering)             │
│                                                             │
│  Schemas:                                                   │
│  • CategoryCreateRequest/Response                           │
│  • CategoryUpdateRequest                                    │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLAlchemy ORM
┌────────────────────▼────────────────────────────────────────┐
│              Database (PostgreSQL)                          │
├─────────────────────────────────────────────────────────────┤
│  Tables:                                                    │
│  • category (id, tenant_id, name, created_at, updated_at)   │
│  • form (id, tenant_id, category_id, ...)                   │
│                                                             │
│  Indexes:                                                   │
│  • (tenant_id, name) - unique constraint                    │
│  • (tenant_id, category_id) - for filtering                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Category Creation Flow:**
1. User submits category form → Frontend validates → API POST /categories
2. Backend validates (name length, uniqueness) → CategoryService.create()
3. ORM persists to database → Response returned to frontend
4. Frontend updates store and refreshes dropdown

**Form Assignment Flow:**
1. User selects category in form builder → Store updates formCategory
2. User saves form → API PUT /forms/{id} with category_id
3. Backend validates category belongs to tenant → FormService.update()
4. ORM persists category_id → Frontend receives confirmation

**Category Deletion Flow:**
1. User deletes category → API DELETE /categories/{id}
2. Backend checks if default category → Prevent if default
3. CategoryService.delete() → Finds all forms with this category
4. Reassigns forms to default category → Deletes category record
5. Frontend refreshes category list and form displays

---

## Database Schema

### Category Table

```sql
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name),
    INDEX idx_tenant_categories (tenant_id)
);
```

### Form Table Modifications

```sql
ALTER TABLE form ADD COLUMN category_id INTEGER REFERENCES category(id) ON DELETE SET NULL;
ALTER TABLE form ADD INDEX idx_form_category (tenant_id, category_id);
```

### Relationships

- **Category → Form**: One-to-Many (one category has many forms)
- **Tenant → Category**: One-to-Many (one tenant has many categories)
- **Cascade Behavior**: When category deleted, forms reassigned to default; when tenant deleted, all categories cascade deleted

### Migration Strategy

1. Create `category` table with `is_default` flag
2. Add `category_id` foreign key to `form` table
3. Create default "Uncategorized" category for each existing tenant
4. Backfill existing forms with default category_id
5. Add NOT NULL constraint to `form.category_id` (after backfill)

---

## Backend API Design

### Endpoints

#### 1. List Categories
```
GET /api/v1/categories?page=1&page_size=20
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}

Response 200:
{
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Uncategorized",
        "is_default": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### 2. Create Category
```
POST /api/v1/categories
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json

Request:
{
  "name": "HR Forms"
}

Response 201:
{
  "data": {
    "id": 2,
    "name": "HR Forms",
    "is_default": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}

Response 400 (validation error):
{
  "detail": "Category name must be 1-50 characters"
}

Response 409 (duplicate):
{
  "detail": "Category with this name already exists for your tenant"
}
```

#### 3. Update Category
```
PUT /api/v1/categories/{category_id}
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json

Request:
{
  "name": "Human Resources"
}

Response 200:
{
  "data": {
    "id": 2,
    "name": "Human Resources",
    "is_default": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}

Response 403 (not owner's tenant):
{
  "detail": "Access denied"
}
```

#### 4. Delete Category
```
DELETE /api/v1/categories/{category_id}
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}

Response 204 (success, no content)

Response 400 (default category):
{
  "detail": "Cannot delete the default category"
}

Response 403 (not owner's tenant):
{
  "detail": "Access denied"
}
```

#### 5. List Forms with Category Filter
```
GET /api/v1/forms?category_id={category_id}&page=1&page_size=20
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}

Response 200:
{
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Employee Onboarding",
        "category_id": 2,
        "category_name": "Human Resources",
        "status": "published",
        "created_at": "2024-01-10T00:00:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
```

### Request/Response Schemas

```python
# Pydantic schemas
class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class CategoryUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class CategoryResponse(BaseModel):
    id: int
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CategoryListResponse(BaseModel):
    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
```

### Error Handling

| Error | Status | Cause |
|-------|--------|-------|
| Empty/invalid name | 400 | Name validation failed |
| Name too long | 400 | Name exceeds 50 characters |
| Duplicate name | 409 | Category name exists in tenant |
| Default category deletion | 400 | Attempting to delete default category |
| Cross-tenant access | 403 | Accessing category from different tenant |
| Category not found | 404 | Category ID doesn't exist |

---

## Frontend Components

### Component Architecture

```
FormBuilder/
├── CategoryDropdown.vue
│   ├── Props: modelValue, categories, disabled
│   ├── Emits: update:modelValue
│   └── Features: tooltip, empty state, loading
│
FormSearch/
├── CategoryFilter.vue
│   ├── Props: modelValue, categories
│   ├── Emits: update:modelValue
│   └── Features: "All Categories" option, filter persistence
│
Stores/
└── useCategoryStore.ts
    ├── State: categories, loading, error
    ├── Actions: fetchCategories, createCategory, deleteCategory
    └── Getters: categoryMap, defaultCategory
```

### CategoryDropdown Component

```typescript
// src/components/form/CategoryDropdown.vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { NSelect, NButton, NSpace, NEmpty } from 'naive-ui'
import { useCategoryStore } from '@/stores/useCategory'

interface Props {
  modelValue?: number
  disabled?: boolean
}

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const categoryStore = useCategoryStore()
const showCreateModal = ref(false)
const newCategoryName = ref('')

const categoryOptions = computed(() => {
  return categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id,
  }))
})

const handleCategoryChange = (value: number) => {
  emit('update:modelValue', value)
}

const handleCreateCategory = async () => {
  await categoryStore.createCategory(newCategoryName.value)
  newCategoryName.value = ''
  showCreateModal.value = false
}
</script>

<template>
  <div class="category-dropdown">
    <NSelect
      :value="modelValue"
      :options="categoryOptions"
      :disabled="disabled || categoryStore.loading"
      placeholder="Select a category"
      @update:value="handleCategoryChange"
    />
    <NEmpty v-if="categoryOptions.length === 0" description="No categories found" />
  </div>
</template>
```

### CategoryFilter Component

```typescript
// src/components/form/CategoryFilter.vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NSelect } from 'naive-ui'
import { useCategoryStore } from '@/stores/useCategory'

interface Props {
  modelValue?: number | null
}

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const categoryStore = useCategoryStore()

const categoryOptions = computed(() => [
  { label: 'All Categories', value: null },
  ...categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id,
  })),
])

const handleFilterChange = (value: number | null) => {
  emit('update:modelValue', value)
  // Persist to session storage
  sessionStorage.setItem('selectedCategoryFilter', String(value ?? ''))
}

onMounted(() => {
  categoryStore.fetchCategories()
})
</script>

<template>
  <NSelect
    :value="modelValue"
    :options="categoryOptions"
    placeholder="Filter by category"
    clearable
    @update:value="handleFilterChange"
  />
</template>
```

### Pinia Store

```typescript
// src/stores/useCategory.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { listCategories, createCategory, updateCategory, deleteCategory } from '@/api/category'
import type { Category } from '@/types/category'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const defaultCategory = computed(() => 
    categories.value.find(cat => cat.is_default)
  )

  const categoryMap = computed(() => {
    const map = new Map<number, Category>()
    categories.value.forEach(cat => map.set(cat.id, cat))
    return map
  })

  const fetchCategories = async () => {
    loading.value = true
    try {
      const response = await listCategories()
      categories.value = response.data.items
      error.value = null
    } catch (err) {
      error.value = 'Failed to load categories'
    } finally {
      loading.value = false
    }
  }

  const createCategoryItem = async (name: string) => {
    try {
      const response = await createCategory({ name })
      categories.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = 'Failed to create category'
      throw err
    }
  }

  const updateCategoryItem = async (id: number, name: string) => {
    try {
      const response = await updateCategory(id, { name })
      const index = categories.value.findIndex(cat => cat.id === id)
      if (index !== -1) {
        categories.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = 'Failed to update category'
      throw err
    }
  }

  const deleteCategoryItem = async (id: number) => {
    try {
      await deleteCategory(id)
      categories.value = categories.value.filter(cat => cat.id !== id)
    } catch (err) {
      error.value = 'Failed to delete category'
      throw err
    }
  }

  return {
    categories,
    loading,
    error,
    defaultCategory,
    categoryMap,
    fetchCategories,
    createCategoryItem,
    updateCategoryItem,
    deleteCategoryItem,
  }
})
```

---

## Implementation Strategy

### Backend Implementation Order

1. **Models** (app/models/category.py)
   - Create Category ORM model with TenantMixin and TimestampMixin
   - Add category_id foreign key to Form model

2. **Schemas** (app/schemas/category_schemas.py)
   - CategoryCreateRequest, CategoryUpdateRequest
   - CategoryResponse, CategoryListResponse

3. **Services** (app/services/category_service.py)
   - CategoryService with CRUD operations
   - Validation logic (name length, uniqueness)
   - Cascading deletion logic
   - Default category initialization

4. **API Routes** (app/api/v1/categories.py)
   - GET /categories (list with pagination)
   - POST /categories (create)
   - PUT /categories/{id} (update)
   - DELETE /categories/{id} (delete)
   - Tenant isolation checks on all endpoints

5. **Form Service Updates** (app/services/form_service.py)
   - Update form creation to assign default category
   - Update form filtering to support category_id parameter
   - Update form response to include category information

6. **Database Migration** (alembic/versions/)
   - Create category table
   - Add category_id to form table
   - Create default categories for existing tenants
   - Add indexes and constraints

### Frontend Implementation Order

1. **Types** (src/types/category.ts)
   - Category interface
   - API request/response types

2. **API Client** (src/api/category.ts)
   - listCategories(), createCategory(), updateCategory(), deleteCategory()

3. **Pinia Store** (src/stores/useCategory.ts)
   - useCategoryStore with state and actions

4. **Components**
   - CategoryDropdown.vue (form builder integration)
   - CategoryFilter.vue (form search integration)

5. **Form Builder Integration**
   - Add CategoryDropdown to form creation/editing
   - Update formDesigner store to include category_id
   - Validate category selection before save

6. **Form Search Integration**
   - Add CategoryFilter to form list page
   - Update form list query to include category_id filter
   - Display category name in form list items

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Category Uniqueness Within Tenant

For any tenant, creating a category with a name that already exists in that tenant should be rejected with a 409 Conflict error.

**Validates: Requirements 1.6**

### Property 2: Category Name Validation

For any category creation request, if the name is empty or exceeds 50 characters, the request should be rejected with a 400 Bad Request error.

**Validates: Requirements 1.5**

### Property 3: Cascading Category Deletion

For any category that is deleted, all forms previously assigned to that category should be reassigned to the tenant's default category, and the category record should be removed.

**Validates: Requirements 1.4, 4.4, 8.3**

### Property 4: Default Category Protection

For any tenant, attempting to delete the default category should be rejected with a 400 Bad Request error.

**Validates: Requirements 8.4**

### Property 5: Form Default Category Assignment

For any form created without an explicit category assignment, the form should be automatically assigned to the tenant's default category.

**Validates: Requirements 4.3, 8.2**

### Property 6: Multi-Tenant Category Isolation

For any user from Tenant A, accessing or modifying categories should only affect categories belonging to Tenant A. Attempting to access a category from Tenant B should return a 403 Forbidden error.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 7: Category Filtering Accuracy

For any form list query with a category_id filter, all returned forms should have the specified category_id, and no forms from other categories should be included.

**Validates: Requirements 3.2, 5.5**

### Property 8: All Categories Filter

For any form list query with category_id=null or "All Categories" selected, all forms regardless of category assignment should be returned.

**Validates: Requirements 3.3**

### Property 9: Category Information Persistence

For any form saved with a category assignment, querying the form should return the same category_id that was assigned.

**Validates: Requirements 2.5, 4.5**

### Property 10: Category Dropdown Consistency

For any form builder session, the category dropdown should display all categories for the tenant, and selecting a category should update the form's category assignment in the UI immediately without requiring a page refresh.

**Validates: Requirements 2.1, 2.4, 6.5**

### Property 11: Default Category Initialization

For any new tenant created in the system, a default category named "Uncategorized" should be automatically created and marked as the default.

**Validates: Requirements 8.1**

### Property 12: Category List Pagination

For any GET request to /api/v1/categories, the response should include paginated results with total count, current page, and page size, containing only categories for the authenticated tenant.

**Validates: Requirements 5.1**

---

## Error Handling

### Backend Error Scenarios

| Scenario | HTTP Status | Response |
|----------|------------|----------|
| Invalid category name (empty) | 400 | `{"detail": "Category name must be 1-50 characters"}` |
| Category name too long | 400 | `{"detail": "Category name must be 1-50 characters"}` |
| Duplicate category name | 409 | `{"detail": "Category with this name already exists"}` |
| Delete default category | 400 | `{"detail": "Cannot delete the default category"}` |
| Cross-tenant access | 403 | `{"detail": "Access denied"}` |
| Category not found | 404 | `{"detail": "Category not found"}` |
| Unauthorized | 401 | `{"detail": "Not authenticated"}` |

### Frontend Error Handling

- Display toast notifications for API errors
- Disable form submission if category is required but not selected
- Show loading states during API calls
- Gracefully handle empty category lists with helpful messaging
- Persist filter selections in session storage for UX continuity

---

## Testing Strategy

### Unit Testing

**Backend Unit Tests:**
- Category validation (name length, uniqueness)
- Default category initialization
- Cascading deletion logic
- Tenant isolation checks
- Category CRUD operations

**Frontend Unit Tests:**
- CategoryDropdown component rendering
- CategoryFilter component rendering
- useCategoryStore actions and getters
- API client functions

### Property-Based Testing

**Property Test Configuration:**
- Minimum 100 iterations per test
- Use fast-check (JavaScript) and Hypothesis (Python)
- Tag format: `Feature: form-category-system, Property {number}: {property_text}`

**Backend Property Tests:**
1. **Property 1**: Generate random tenant IDs and category names; verify duplicate names are rejected
2. **Property 2**: Generate category names of various lengths; verify validation rules
3. **Property 3**: Generate categories with forms; delete category and verify reassignment
4. **Property 4**: Attempt to delete default category; verify rejection
5. **Property 5**: Create forms without category; verify default assignment
6. **Property 6**: Generate cross-tenant access attempts; verify 403 responses
7. **Property 7**: Generate forms with categories; filter and verify accuracy
8. **Property 8**: Query with null category filter; verify all forms returned
9. **Property 9**: Save forms with categories; query and verify persistence
10. **Property 11**: Create new tenant; verify default category exists
11. **Property 12**: Query categories with pagination; verify correct structure

**Frontend Property Tests:**
1. **Property 10**: Simulate category selection; verify UI updates immediately

### Integration Testing

- End-to-end form creation with category assignment
- End-to-end form filtering by category
- Category management workflow (create, update, delete)
- Multi-tenant isolation verification
- Database migration verification

---

## Design Decisions and Rationales

### Decision 1: Separate Category Table vs. String Field

**Decision**: Create a separate `category` table with foreign key relationship.

**Rationale**: 
- Enables category reuse across multiple forms
- Supports category management (CRUD operations)
- Allows efficient filtering and aggregation
- Maintains referential integrity
- Supports future features like category permissions or analytics

### Decision 2: Default Category Approach

**Decision**: Create an "Uncategorized" default category per tenant; prevent its deletion.

**Rationale**:
- Ensures forms always have valid category assignments
- Simplifies cascading deletion logic
- Provides fallback for orphaned forms
- Improves UX by avoiding null category states

### Decision 3: Cascading Reassignment vs. Cascade Delete

**Decision**: Reassign forms to default category instead of deleting them.

**Rationale**:
- Preserves form data and submission history
- Prevents accidental data loss
- Maintains referential integrity without orphaned records
- Better user experience (forms don't disappear)

### Decision 4: Tenant Isolation Strategy

**Decision**: Enforce tenant isolation at both API and database levels.

**Rationale**:
- Defense in depth (multiple layers of protection)
- Prevents accidental cross-tenant data access
- Simplifies query logic (always filter by tenant_id)
- Aligns with existing FormFlow architecture

### Decision 5: Session-Based Filter Persistence

**Decision**: Persist category filter selection in session storage (not database).

**Rationale**:
- Lightweight and fast (no server round-trip)
- Scoped to current session (doesn't affect other users)
- Automatically cleared on logout
- Aligns with stateless API design

