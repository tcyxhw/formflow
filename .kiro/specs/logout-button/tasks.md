# Implementation Plan: logout-button

## Overview

This implementation plan outlines the steps to add logout functionality to the FormFlow application. The feature includes a backend API endpoint for session termination, a frontend logout button component, auth store updates, and comprehensive testing.

## Tasks

- [ ] 1. Implement backend logout endpoint
  - [ ] 1.1 Enhance auth service with logout method
    - Add `logout(user_id: int)` method to `backend/app/services/auth.py`
    - Implement refresh token invalidation in database
    - Clear server-side session data from Redis
    - _Requirements: 3.1, 3.2, 5.4_

  - [ ] 1.2 Enhance auth router with logout endpoint
    - Add/enhance `POST /api/v1/auth/logout` endpoint in `backend/app/api/v1/auth.py`
    - Add authentication dependency check
    - Return success response with proper schema
    - _Requirements: 3.3, 5.3_

  - [ ]* 1.3 Write unit tests for backend logout
    - Test logout with valid token returns success
    - Test logout invalidates refresh token in database
    - Test logout with invalid token returns 401
    - Test logout without authentication returns 401
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.3_

  - [ ]* 1.4 Write property tests for backend logout
    - **Property 7: Server-Side Token Invalidation**
    - **Property 8: Backend Returns Success Response**
    - **Property 9: Invalidated Token Rejection**
    - **Property 10: Auth Required for Logout**
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.3, 5.4_

- [ ] 2. Create frontend logout button component
  - [ ] 2.1 Create LogoutButton.vue component
    - Create `my-app/src/components/LogoutButton.vue`
    - Add size and type props for flexibility
    - Implement click event emission
    - Add loading state during logout process
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.2 Write unit tests for LogoutButton component
    - Test button renders when authenticated
    - Test button does not render when not authenticated
    - Test clicking logout calls auth store action
    - Test mobile responsiveness
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.3 Write property tests for LogoutButton
    - **Property 1: Authenticated User Sees Logout Button**
    - **Property 2: Mobile Responsive Logout Button**
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 3. Update auth store with logout action
  - [ ] 3.1 Enhance auth store logout method
    - Update `my-app/src/stores/auth.ts`
    - Add API call to logout endpoint
    - Clear accessToken, refreshToken, tokenExpiry from state
    - Clear userInfo, userBasicInfo from state
    - Remove all auth items from localStorage
    - Handle errors gracefully (clear local state anyway)
    - _Requirements: 2.1, 2.2, 2.4, 5.1_

  - [ ]* 3.2 Write unit tests for auth store logout
    - Test store clears all tokens and user data
    - Test store handles API errors correctly
    - Test store handles network errors correctly
    - _Requirements: 2.2, 2.4, 5.1_

  - [ ]* 3.3 Write property tests for auth store
    - **Property 3: Logout Triggers API Call**
    - **Property 4: Local Token Cleanup**
    - _Requirements: 2.1, 2.2, 5.1_

- [ ] 4. Integrate logout button into homepage
  - [ ] 4.1 Update HomeView.vue to include logout button
    - Import LogoutButton component in `my-app/src/views/HomeView.vue`
    - Place button in header or user menu area
    - Ensure proper positioning and styling
    - _Requirements: 1.1, 1.2_

  - [ ] 4.2 Update route guards for post-logout protection
    - Update `my-app/src/router/guards.ts`
    - Check auth state after logout action
    - Redirect to login if accessing protected routes without valid token
    - _Requirements: 4.3, 5.2_

  - [ ]* 4.3 Write integration tests for logout flow
    - Test complete logout flow: click → API → cleanup → redirect
    - Test logout with network failure
    - Test concurrent logout attempts
    - Test logout during token refresh
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Final verification
  - [ ] 6.1 Verify logout button visibility when authenticated
    - **Property 1: Authenticated User Sees Logout Button**
    - _Requirements: 1.1_

  - [ ] 6.2 Verify successful logout redirect
    - **Property 5: Successful Logout Redirect**
    - _Requirements: 2.3, 4.1_

  - [ ] 6.3 Verify protected route blocking
    - **Property 6: Protected Route Blocking**
    - **Property 11: Already Logged Out Handling**
    - _Requirements: 4.3, 5.2_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Backend uses Python/FastAPI, frontend uses TypeScript/Vue3