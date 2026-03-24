# 个人信息页面登录状态丢失 Bugfix 设计

## Overview

本设计文档针对"在首页点击个人信息后登录状态被清除"的bug进行根因分析和修复方案设计。

**Bug 现象**：用户已登录（token存在），从首页点击"个人信息"导航到 `/user/profile` 页面时，登录状态被清除，页面无法展示用户信息。

**根本原因**：路由守卫的 `checkAuth()` 方法在 `userInfo` 为空时调用 `getUserInfo()` API，该API在返回401错误时直接调用 `clearAuth()` 清除登录状态，而没有先尝试刷新token。

**修复策略**：修改 `getUserInfo()` 方法，在收到401错误时先尝试刷新token，刷新成功后再重试获取用户信息，刷新失败才清除登录状态。

## Glossary

- **Bug_Condition (C)**：触发bug的条件 - 当用户已登录（有token）但userInfo为空时，访问需要认证的页面
- **Property (P)**：期望的正确行为 - 即使userInfo获取失败，也应该先尝试刷新token，刷新成功则继续展示用户信息，刷新失败才清除登录状态
- **Preservation**：需要保持不变的行为 - token确实过期时正确清除登录状态并跳转登录页
- **authStore.checkAuth()**：路由守卫中用于检查认证状态的异步方法
- **authStore.getUserInfo()**：获取当前用户信息的API调用方法
- **authStore.refreshAccessToken()**：刷新访问令牌的API调用方法

## Bug Details

### Bug Condition

当用户已登录（有有效的accessToken或refreshToken）但 `userInfo` 为空时，访问需要认证的页面（如 `/user/profile`），路由守卫会调用 `checkAuth()` 方法，该方法尝试调用 `getUserInfo()` API。如果API返回401错误，当前实现会直接调用 `clearAuth()` 清除登录状态，导致用户被强制登出。

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type { hasToken: boolean, userInfo: UserInfo | null }
  OUTPUT: boolean
  
  RETURN input.hasToken = true                    // 用户有token（已登录）
         AND input.userInfo = null                // 但userInfo为空
         AND getUserInfo() returns 401            // API调用返回401
         AND clearAuth() is called                // 导致登录状态被清除
END FUNCTION
```

### Examples

**示例1：正常流程（当前有bug的行为）**
- 用户已登录，token存储在localStorage中
- 从首页点击"个人信息"导航到 /user/profile
- 路由守卫调用 checkAuth()，发现 userInfo 为空
- checkAuth() 调用 getUserInfo() API
- 由于某种原因（如token刚好过期边缘）API返回401
- getUserInfo() 捕获401错误，调用 clearAuth()
- 登录状态被清除，页面跳转到登录页

**示例2：期望的正确行为**
- 用户已登录，token存储在localStorage中
- 从首页点击"个人信息"导航到 /user/profile
- 路由守卫调用 checkAuth()，发现 userInfo 为空
- checkAuth() 调用 getUserInfo() API
- API返回401，getUserInfo() 不直接清除登录状态
- checkAuth() 捕获错误，尝试调用 refreshAccessToken()
- 刷新成功，重新调用 getUserInfo()
- 用户信息获取成功，页面正常展示

**示例3：token确实过期（应保持不变）**
- 用户的refreshToken也已过期
- 访问需要认证的页面
- checkAuth() 尝试刷新token失败
- 正确清除登录状态并跳转到登录页

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 用户已登录且 userInfo 已存在时，系统应继续正常展示用户信息
- 用户的 accessToken 和 refreshToken 都已过期时，系统应正确清除登录状态并跳转到登录页
- 登录页面、注册页面、租户选择页面等公开页面的访问行为应保持不变

**Scope:**
所有不涉及 userInfo 获取失败的场景都应该完全不受此修复影响，包括：
- userInfo 已存在于内存中的所有操作
- 直接调用 API 的操作（如 Profile.vue 中的 loadUserInfo）
- token 确实过期需要清除登录的场景

## Hypothesized Root Cause

基于代码分析，最可能的问题原因如下：

1. **getUserInfo() 直接清除登录状态**
   - 在 `auth.ts` 的 `getUserInfo()` 方法中，当捕获到401错误时直接调用 `this.clearAuth()`
   - 这导致即使token只是暂时无效（可以刷新），也会被强制登出

2. **checkAuth() 错误处理不完善**
   - `checkAuth()` 方法在调用 `getUserInfo()` 失败后，虽然有尝试刷新token的逻辑
   - 但由于 `getUserInfo()` 已经调用了 `clearAuth()`，刷新token后状态已被破坏

3. **request.ts 拦截器也会清除登录状态**
   - HTTP拦截器在收到401错误时也会调用 `authStore.clearAuth()`
   - 这与 `getUserInfo()` 的行为形成双重保险，但过于激进

4. **Profile.vue 页面重复获取用户信息**
   - Profile.vue 在 `onMounted` 时调用 `loadUserInfo()`（直接调用API）
   - 这与路由守卫的 `checkAuth()` 形成竞争，可能导致多次调用

## Correctness Properties

Property 1: Bug Condition - 用户已登录但userInfo为空时不应直接清除登录状态

_For any_ 输入满足以下条件：用户已登录（有token）但 userInfo 为空，访问需要认证的页面时，fixed 的 getUserInfo() 方法 SHALL NOT 直接调用 clearAuth()，而是先尝试刷新token，刷新成功则重试获取用户信息，刷新失败才清除登录状态。

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - token确实过期时正确清除登录状态

_For any_ 输入满足以下条件：用户的 accessToken 和 refreshToken 都已过期或无效，fixed 的代码 SHALL 产生与原始代码相同的行为，正确清除登录状态并跳转到登录页。

**Validates: Requirements 3.1, 3.2**

## Fix Implementation

### Changes Required

**文件**: `my-app/src/stores/auth.ts`

**函数**: `getUserInfo()`

**Specific Changes**:

1. **修改 getUserInfo() 方法**
   - 移除401错误时直接调用 `clearAuth()` 的逻辑
   - 401错误应该抛出，由调用者（checkAuth）处理刷新逻辑
   - 只保留通用的错误日志记录

2. **修改 checkAuth() 方法**
   - 确保 getUserInfo() 失败后先尝试刷新token
   - 刷新成功后重新获取用户信息
   - 刷新失败才返回false（让路由守卫处理跳转）

3. **可选：修改 request.ts 拦截器**
   - 对于 `/api/v1/auth/currentUser` 的401错误，不直接清除登录状态
   - 让 authStore 的刷新逻辑统一处理

## Testing Strategy

### Validation Approach

测试策略采用两阶段方法：首先在未修复的代码上暴露问题，然后验证修复后行为正确且不破坏现有功能。

### Exploratory Bug Condition Checking

**Goal**: 在实现修复之前，编写测试用例来复现bug，确认根因分析正确。

**Test Plan**: 编写测试模拟以下场景：用户有token但userInfo为空，调用getUserInfo()返回401，观察登录状态是否被错误清除。

**Test Cases**:
1. **Token边缘过期场景**：模拟token刚好过期，getUserInfo返回401（未修复代码会清除登录状态）
2. **并发请求场景**：同时有多个请求需要认证，验证状态一致性
3. **刷新后重试场景**：验证刷新token后能否正确获取用户信息

**Expected Counterexamples**:
- getUserInfo() 在401时直接调用 clearAuth()，导致登录状态丢失
- checkAuth() 的刷新逻辑因为状态已被清除而失效

### Fix Checking

**Goal**: 验证对于所有满足bug条件的输入，修复后的代码产生期望的正确行为。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := getUserInfo_fixed(input)
  IF result = 401 THEN
    // 应该先尝试刷新，不直接清除登录状态
    ASSERT authStore.isLoggedIn = true
    refreshed := refreshAccessToken()
    IF refreshed THEN
      result2 := getUserInfo_fixed(input)
      ASSERT result2 = success
    END IF
  END IF
END FOR
```

### Preservation Checking

**Goal**: 验证对于所有不满足bug条件的输入，修复后的代码产生与原始代码相同的结果。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  // 场景1：userInfo已存在
  IF input.userInfo IS NOT NULL THEN
    ASSERT getUserInfo_fixed(input) = getUserInfo_original(input)
  END IF
  
  // 场景2：token确实过期
  IF input.refreshToken IS EXPIRED THEN
    ASSERT authStore.isLoggedIn = false  // 应该正确清除登录状态
  END IF
END FOR
```

**Testing Approach**: 属性测试适合用于验证preserve行为，因为可以自动生成各种边界条件。

**Test Plan**: 观察未修复代码在以下场景的行为，然后编写测试确保修复后行为一致。

**Test Cases**:
1. **userInfo已存在场景**：验证userInfo不会在修复后丢失
2. **token确实过期场景**：验证token过期时仍然正确清除登录状态
3. **刷新token失败场景**：验证刷新失败时正确清除登录状态

### Unit Tests

- 测试 getUserInfo() 在401错误时的行为
- 测试 checkAuth() 的完整流程（包含刷新逻辑）
- 测试 refreshAccessToken() 成功和失败的场景

### Property-Based Tests

- 生成随机的token状态组合，验证登录状态一致性
- 生成随机的API响应，验证错误处理正确性

### Integration Tests

- 测试完整的登录 -> 访问Profile页面流程
- 测试token刷新后继续访问需要认证的页面
- 测试token过期后被正确重定向到登录页