# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - getUserInfo 401直接清除登录状态
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: 模拟用户有token但userInfo为空，getUserInfo()返回401的场景
  - Test that when getUserInfo() returns 401, authStore.clearAuth() should NOT be called (from Bug Condition in design)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "getUserInfo() calls clearAuth() on 401, causing login state lost")
  - _Requirements: 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Token确实过期时正确清除登录状态
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs
  - When both accessToken and refreshToken are expired/invalid, clearAuth() should be called (from Preservation Requirements)
  - Write property-based test: for all inputs where refreshToken is expired, authStore.isLoggedIn should be false after checkAuth
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - _Requirements: 3.1, 3.2_

- [x] 3. Fix for getUserInfo 401错误时直接清除登录状态

  - [x] 3.1 Implement the fix
    - 修改 auth.ts 中的 getUserInfo() 方法
    - 移除401错误时直接调用 clearAuth() 的逻辑
    - 401错误应该抛出，由调用者(checkAuth)处理刷新逻辑
    - 只保留通用的错误日志记录
    - _Bug_Condition: isBugCondition(input) where input.hasToken=true AND input.userInfo=null AND getUserInfo() returns 401_
    - _Expected_Behavior: getUserInfo() should NOT call clearAuth() on 401, let caller handle refresh_
    - _Preservation: When refreshToken is expired, clearAuth() should still be called correctly_
    - _Requirements: 2.1, 2.2, 3.1, 3.2_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - getUserInfo不再直接清除登录状态
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Token过期时仍正确清除登录状态
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.1, 3.2_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.