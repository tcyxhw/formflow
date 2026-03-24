# Design Document

## Overview

This design document outlines the implementation of a logout functionality for the FormFlow application. The feature enables users to securely end their authenticated sessions from the homepage, with proper server-side session cleanup and client-side state management.

### Design Goals

- Provide a visible and accessible logout button on the homepage
- Ensure secure server-side session termination
- Clear all client-side authentication state
- Redirect users to the login page after logout
- Handle error cases gracefully while maintaining security

### Scope

The implementation includes:
- Frontend logout button component and integration
- Backend logout endpoint enhancement
- State management updates
- Route protection updates

## Architecture

### System Context

The logout feature operates within the existing authentication architecture:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  FastAPI    │────▶│  Database   │
│   (Vue3)    │◀────│  Backend    │◀────│  (Postgres) │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │
        │                   │
   ┌─────────────┐     ┌─────────────┐
   │  Local      │     │   Redis     │
   │  Storage    │     │  (Sessions) │
   └─────────────┘     └─────────────┘
```

### Component Interactions

1. User clicks logout button on homepage
2. Frontend calls logout API endpoint
3. Backend invalidates refresh token and clears session data
4. Backend returns success response
5. Frontend clears local storage and Pinia state
6. Frontend redirects to login page

## Components and Interfaces

### Frontend Components

#### LogoutButton Component

**Location:** `my-app/src/components/LogoutButton.vue`

**Props:**
- `size`: Button size (small, medium, large)
- `type`: Button type (primary, default, text)

**Events:**
- `click`: Emitted when button is clicked

**Behavior:**
- Visible only when user is authenticated
- Calls auth store logout action on click
- Shows loading state during logout process

#### Homepage Integration

**Location:** `my-app/src/views/HomeView.vue`

**Changes:**
- Import and place LogoutButton component
- Position button in header or user menu area
- Ensure mobile responsiveness

### Backend Components

#### Auth Service Enhancement

**Location:** `backend/app/services/auth.py`

**New/Modified Methods:**
- `logout(user_id: int)`: Invalidates refresh token and clears session data

#### Auth Router Enhancement

**Location:** `backend/app/api/v1/auth.py`

**Endpoint:**
- `POST /api/v1/auth/logout` - Existing endpoint to be enhanced

**Request Headers:**
- `Authorization`: Bearer {access_token}
- `X-Tenant-ID`: {tenant_id}

**Response:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true
  }
}
```

### State Management

#### Auth Store Updates

**Location:** `my-app/src/stores/auth.ts`

**Modified Actions:**
- `logout()`: Enhanced to handle errors gracefully and ensure local cleanup

**State Changes:**
- Clear `accessToken`, `refreshToken`, `tokenExpiry`
- Clear `userInfo`, `userBasicInfo`
- Remove items from localStorage

### Route Protection

**Location:** `my-app/src/router/guards.ts`

**Updates:**
- Check auth state after logout action
- Redirect to login if accessing protected routes without valid token

## Data Models

### Frontend Types

```typescript
// my-app/src/types/auth.ts (existing, no changes needed)
interface LogoutResponse {
  success: boolean
}
```

### Backend Models

```python
# backend/app/schemas/auth.py (existing, no changes needed)
class LogoutResponse(BaseModel):
    success: bool
```

### Token Invalidation

**Database Changes:**
- Add `is_active` field to refresh token table (if not exists)
- Set `is_active = False` for user's refresh tokens on logout

**Redis Session Cleanup:**
- Remove session key from Redis
- Clear any cached user permissions

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing the acceptance criteria, I identified the following testable properties. Some criteria were combined or marked as redundant:

- **Combined**: Requirements 2.3 and 4.1 both test successful logout redirect behavior
- **Combined**: Requirements 3.1 and 5.4 both test immediate token invalidation
- **Combined**: Requirements 1.1 and 4.4 test button visibility in opposite states
- **Edge Cases**: Mobile responsiveness (1.3) and error handling (2.4) are covered by specific unit tests

### Property 1: Authenticated User Sees Logout Button

*For any* authenticated user viewing the homepage, the logout button SHALL be visible and accessible without requiring navigation to other pages.

**Validates: Requirements 1.1, 1.2**

### Property 2: Mobile Responsive Logout Button

*For any* user on a mobile device, the logout button SHALL remain accessible and tappable with adequate touch target size.

**Validates: Requirements 1.3**

### Property 3: Logout Triggers API Call

*For any* user click on the logout button, the frontend SHALL send a logout request to the backend API.

**Validates: Requirements 2.1**

### Property 4: Local Token Cleanup

*For any* logout operation (successful or failed), the frontend SHALL clear all stored authentication tokens from localStorage and memory.

**Validates: Requirements 2.2, 5.1**

### Property 5: Successful Logout Redirect

*For any* successful logout operation, the frontend SHALL navigate the user to the login page and clear all application state including Pinia stores.

**Validates: Requirements 2.3, 4.1, 4.2**

### Property 6: Protected Route Blocking

*For any* user who has logged out, the frontend SHALL prevent access to protected routes and redirect to login until re-authentication.

**Validates: Requirements 4.3**

### Property 7: Server-Side Token Invalidation

*For any* logout request with valid authentication, the backend SHALL invalidate the user's refresh token immediately and clear server-side session data.

**Validates: Requirements 3.1, 3.2, 5.4**

### Property 8: Backend Returns Success Response

*For any* valid logout request, the backend SHALL return a success response to the frontend.

**Validates: Requirements 3.3**

### Property 9: Invalidated Token Rejection

*For any* user attempting to use an invalidated token after logout, the backend SHALL reject the request with a 401 authentication error.

**Validates: Requirements 3.4, 5.3**

### Property 10: Auth Required for Logout

*For any* logout request without valid authentication, the backend SHALL reject the request with a 401 error.

**Validates: Requirements 5.3**

### Property 11: Already Logged Out Handling

*For any* user without valid tokens, the frontend SHALL redirect to the login page without displaying an error.

**Validates: Requirements 5.2**

## Error Handling

### Frontend Error Handling

#### Network Errors

- **Scenario:** Network connectivity loss during logout request
- **Handling:** Clear local state and redirect to login anyway
- **User Feedback:** Show toast notification if possible

#### Backend Errors

- **Scenario:** Backend returns error response
- **Handling:** Log error, clear local state, redirect to login
- **User Feedback:** Show error message briefly before redirect

#### Token Refresh During Logout

- **Scenario:** Token expires during logout process
- **Handling:** Attempt refresh, if fails then clear and redirect
- **User Feedback:** Transparent to user

### Backend Error Handling

#### Invalid Token

- **Scenario:** Access token is invalid or expired
- **Handling:** Return 401 Unauthorized
- **Security:** Do not invalidate refresh token if request is invalid

#### Missing Authentication

- **Scenario:** No authorization header provided
- **Handling:** Return 401 Unauthorized
- **Security:** Require authentication for logout

#### Server Errors

- **Scenario:** Internal server error during logout
- **Handling:** Log error, attempt to invalidate token anyway
- **Response:** Return 500 with error message

## Testing Strategy

### Unit Testing

#### Frontend Tests

**Test File:** `my-app/tests/unit/logout.spec.ts`

**Test Cases:**
1. Logout button renders when authenticated
2. Logout button does not render when not authenticated
3. Clicking logout calls auth store logout action
4. Auth store clears all tokens and user data
5. Router redirects to login after logout
6. Mobile responsiveness of logout button

**Example Test:**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LogoutButton from '@/components/LogoutButton.vue'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/stores/auth')

describe('LogoutButton', () => {
  it('renders when user is authenticated', () => {
    const authStore = useAuthStore()
    authStore.isLoggedIn = true
    
    const wrapper = mount(LogoutButton)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('does not render when user is not authenticated', () => {
    const authStore = useAuthStore()
    authStore.isLoggedIn = false
    
    const wrapper = mount(LogoutButton)
    expect(wrapper.find('button').exists()).toBe(false)
  })
})
```

#### Backend Tests

**Test File:** `backend/tests/test_auth.py`

**Test Cases:**
1. Logout with valid token returns success
2. Logout invalidates refresh token in database
3. Logout with invalid token returns 401
4. Logout without authentication returns 401
5. Logged out token cannot access protected resources

**Example Test:**
```python
def test_logout_invalidates_token(db_session, client, test_user, test_refresh_token):
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_access_token}"}
    )
    assert response.status_code == 200
    
    # Verify token is invalidated
    token = db_session.query(RefreshToken).filter_by(
        user_id=test_user.id
    ).first()
    assert token.is_active == False
```

### Property-Based Testing

**Library:** Hypothesis (Python) / Fast-Check (TypeScript)

**Property Tests:**

1. **Token Cleanup Property**
   - *For any* user state, after logout the auth store should have no tokens
   - **Validates: Requirements 2.2, 4.2**

2. **Redirect Property**
   - *For any* successful logout, the current route should be login
   - **Validates: Requirements 2.3, 4.1**

3. **Session Invalidation Property**
   - *For any* valid logout request, the backend should invalidate the session
   - **Validates: Requirements 3.1, 3.2**

**Configuration:**
- Minimum 100 iterations per property test
- Tag format: `Feature: logout-button, Property {number}: {property_name}`

### Integration Testing

**Test Scenarios:**

1. **Complete Logout Flow**
   - User clicks logout → API call → Token invalidation → Local cleanup → Redirect
   - Verify all steps complete successfully

2. **Logout with Network Failure**
   - User clicks logout → Network error → Local cleanup → Redirect
   - Verify user is logged out locally even if server unreachable

3. **Concurrent Logout Attempts**
   - Multiple logout clicks → Single API call → Proper cleanup
   - Verify no race conditions

4. **Logout During Token Refresh**
   - Token expires during logout → Refresh succeeds → Logout completes
   - Verify smooth handling of edge case

### Test Coverage Requirements

- **Unit Tests:** Minimum 80% coverage for logout-related code
- **Property Tests:** All correctness properties must have corresponding property tests
- **Integration Tests:** Critical paths must have integration test coverage

### Test Execution

```bash
# Frontend tests
npm run test

# Backend tests
pytest

# Run with coverage
pytest --cov=app.api.v1.auth --cov-report=term-missing
```