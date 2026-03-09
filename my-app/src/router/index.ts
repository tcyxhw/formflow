/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { setupRouterGuards } from './guards'

// 公开路由
const publicRoutes: RouteRecordRaw[] = [
  {
    path: '/tenant-select',
    name: 'TenantSelect',
    component: () => import('@/views/auth/TenantSelect.vue'),
    meta: { title: '选择学校' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面不存在' }
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: { title: '无权限' }
  }
]

// 需要认证的路由
const authRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页' }
  },
  
  // ========== 表单相关路由（已更新）==========
  {
    path: '/form',
    name: 'Form',
    meta: { title: '表单管理' },
    children: [
      {
        path: 'list',
        name: 'FormList',
        component: () => import('@/views/form/List.vue'),
        meta: { title: '表单列表' }
      },
      {
        path: 'designer',
        name: 'FormDesigner',
        component: () => import('@/views/form/Designer.vue'),
        meta: { title: '表单设计器' }
      },
      {
        path: ':id/preview',
        name: 'FormPreview',
        component: () => import('@/views/form/Preview.vue'),
        meta: { title: '表单预览' }
      },
      {
        path: ':id/fill',
        name: 'FormFill',
        component: () => import('@/views/form/Fill.vue'),
        meta: { title: '填写表单' }
      },
    ]
  },
  
  // 提交记录路由（保持不变）
  {
    path: '/submissions',
    name: 'SubmissionList',
    component: () => import('@/views/submissions/SubmissionListView.vue'),
    meta: { title: '提交列表' }
  },
  {
    path: '/submissions/:id',
    name: 'SubmissionDetail',
    component: () => import('@/views/submissions/SubmissionDetailView.vue'),
    meta: { title: '提交详情' }
  },
  
  // 审批相关路由（保持不变）
  {
    path: '/approvals',
    name: 'ApprovalList',
    component: () => import('@/views/approvals/ApprovalListView.vue'),
    meta: { title: '待审批' }
  },
  
  // 活动管理路由
  {
    path: '/activities',
    name: 'ActivityList',
    component: () => import('@/views/activity/ActivityList.vue'),
    meta: { title: '活动管理' }
  },
  {
    path: '/activity/create',
    name: 'ActivityCreate',
    component: () => import('@/views/activity/ActivityCreate.vue'),
    meta: { title: '创建活动' }
  },
  {
    path: '/activity/:id',
    name: 'ActivityDetail',
    component: () => import('@/views/activity/ActivityDetail.vue'),
    meta: { title: '活动详情' }
  },
  {
    path: '/activity/:id/edit',
    name: 'ActivityEdit',
    component: () => import('@/views/activity/ActivityCreate.vue'),
    meta: { title: '编辑活动' }
  },
  {
    path: '/activity/:id/manage',
    name: 'ActivityManage',
    component: () => import('@/views/activity/ActivityManage.vue'),
    meta: { title: '活动管理' }
  },
  {
    path: '/activity/:id/awards',
    name: 'ActivityAwards',
    component: () => import('@/views/activity/ActivityAwards.vue'),
    meta: { title: '评分评奖' }
  },
  {
    path: '/my-activities',
    name: 'MyActivities',
    component: () => import('@/views/activity/MyActivities.vue'),
    meta: { title: '我的活动' }
  },
  {
    path: '/my-credits',
    name: 'MyCredits',
    component: () => import('@/views/activity/MyCredits.vue'),
    meta: { title: '我的学分' }
  },
  {
    path: '/verify/:code',
    name: 'CertificateVerify',
    component: () => import('@/views/activity/CertificateVerify.vue'),
    meta: { title: '证书验证', public: true }
  }
]

// 404路由（必须放最后）
const notFoundRoute: RouteRecordRaw = {
  path: '/:pathMatch(.*)*',
  redirect: '/404'
}

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    ...publicRoutes,
    ...authRoutes,
    notFoundRoute
  ],
  scrollBehavior: () => ({ top: 0 })
})

// 设置路由守卫
setupRouterGuards(router)

export default router