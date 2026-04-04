// src/types/user.ts
/**
 * 用户相关类型定义 - 对应后端 app/schemas/user.py
 */

// 用户基础信息
export interface UserBase {
  account: string
  name: string
  email?: string
  phone?: string
  avatar_url?: string
  department_id?: number
}

// 创建用户
export interface UserCreate extends UserBase {
  password: string        // 密码 6-50字符
}

// 更新用户
export interface UserUpdate {
  name?: string           // 2-50字符
  email?: string
  phone?: string          // 1[3-9]\d{9}
  department_id?: number
  is_active?: boolean
}

// 数据库中的用户
export interface UserInDB extends UserBase {
  id: number
  tenant_id: number
  is_active: boolean
  created_at: string
  updated_at?: string
}

// 用户响应（包含关联信息）
export interface UserResponse extends UserInDB {
  department_name?: string
  roles: string[]
  positions: string[]
}

// 用户扩展信息
export interface UserProfile {
  identity_no?: string      // 学号/工号
  identity_type?: 'student' | 'teacher' | 'admin'
  entry_year?: number       // 1900-2100
  grade?: string
  major?: string
  supervisor_id?: number
  title?: string
  research_area?: string
  office?: string
  emergency_contact?: string
  emergency_phone?: string
}

// 完整的用户信息（用于/me接口）
export interface UserInfo extends UserResponse {
  profile?: UserProfile
  department?: {
    id: number
    name: string
    type: string
  }
  roles?: string[]  // 系统角色（后端返回字符串数组）
  positions?: string[]  // 岗位（后端返回字符串数组）
  permissions?: string[]    // 权限列表
}

// 修改密码
export interface PasswordChange {
  old_password: string      // 原密码
  new_password: string      // 新密码，最少6位
}

// 用户基本信息（兼容旧版本）
export interface UserBasicInfo {
  id: number
  account: string
  name: string
  email?: string
  tenant_id: number
  identity_type: string
  positions: string[]
}

// 部门信息
export interface Department {
  id: number
  tenant_id: number
  name: string
  parent_id: number | null
  type: string
  is_root: boolean
  sort_order: number
}

// 岗位信息
export interface Position {
  id: number
  tenant_id: number
  name: string
}

// 部门-岗位关系
export interface DepartmentPost {
  id: number
  tenant_id: number
  department_id: number
  post_id: number
  is_head: boolean
}

// 用户-部门-岗位关系
export interface UserDepartmentPost {
  id: number
  tenant_id: number
  user_id: number
  department_id: number
  post_id: number | null
}