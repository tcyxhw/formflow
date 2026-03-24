# Bugfix Requirements Document

## Introduction

在首页点击"个人信息"后，登录状态被清除，无法展示用户信息。这是一个登录状态丢失的bug，影响用户查看个人资料。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 用户已登录并从首页点击"个人信息"导航到 /user/profile 页面 THEN 系统的登录状态被清除，页面无法展示用户信息
1.2 WHEN 路由守卫检查认证状态时，如果 authStore.userInfo 为空 THEN 系统会调用 getUserInfo() API，如果 API 返回 401 错误则调用 clearAuth() 清除登录状态

### Expected Behavior (Correct)

2.1 WHEN 用户已登录并从首页点击"个人信息"导航到 /user/profile 页面 THEN 系统 SHALL 正常展示用户信息，登录状态保持不变
2.2 WHEN 路由守卫检查认证状态时，如果 authStore.userInfo 为空 THEN 系统 SHALL 尝试获取用户信息，如果获取失败 SHALL 尝试刷新 token，刷新成功则继续展示用户信息，刷新失败才清除登录状态

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 用户已登录且 authStore.userInfo 已存在 THEN 系统 SHALL CONTINUE TO 正常展示用户信息
3.2 WHEN 用户访问需要认证的页面且 token 确实已过期 THEN 系统 SHALL CONTINUE TO 正确清除登录状态并跳转到登录页