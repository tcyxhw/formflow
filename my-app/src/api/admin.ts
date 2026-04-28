import request from '@/utils/request'

export interface Department {
  id: number
  name: string
  type: string
  parent_id: number | null
}

export interface Position {
  id: number
  name: string
}

export interface DepartmentPost {
  id: number
  department_id: number
  department_name: string
  post_id: number
  post_name: string
  is_head: boolean
}

interface ListResponse {
  items: Department[]
  total: number
}

interface PositionListResponse {
  items: Position[]
  total: number
}

interface DepartmentPostListResponse {
  items: DepartmentPost[]
  total: number
}

export const departmentApi = {
  list(params?: { keyword?: string; page?: number; size?: number }) {
    return request.get('/api/v1/admin/departments/list', { params }) as Promise<{ data: ListResponse }>
  },

  create(data: { name: string; type?: string; parent_id?: number | null }) {
    return request.post('/api/v1/admin/departments', data) as Promise<{ data: Department }>
  },

  delete(departmentId: number) {
    return request.delete(`/api/v1/admin/departments/${departmentId}`)
  }
}

export const positionApi = {
  list(params?: { keyword?: string; page?: number; size?: number }) {
    return request.get('/api/v1/admin/positions/list', { params }) as Promise<{ data: PositionListResponse }>
  },

  create(data: { name: string }) {
    return request.post('/api/v1/admin/positions', data) as Promise<{ data: Position }>
  },

  delete(positionId: number) {
    return request.delete(`/api/v1/admin/positions/${positionId}`)
  }
}

export const departmentPostApi = {
  list(departmentId?: number) {
    return request.get('/api/v1/admin/department-posts/list', { 
      params: departmentId ? { department_id: departmentId } : {} 
    }) as Promise<{ data: DepartmentPostListResponse }>
  },

  create(data: { department_id: number; post_id: number; is_head?: boolean }) {
    return request.post('/api/v1/admin/department-posts', data) as Promise<{ data: DepartmentPost }>
  },

  delete(departmentPostId: number) {
    return request.delete(`/api/v1/admin/department-posts/${departmentPostId}`)
  }
}

export const listDepartments = (params?: { keyword?: string; page?: number; size?: number }) => {
  return request.get('/api/v1/admin/departments/list', { params }) as Promise<{ data: ListResponse }>
}

export const listPositions = (params?: { keyword?: string; page?: number; size?: number }) => {
  return request.get('/api/v1/admin/positions/list', { params }) as Promise<{ data: PositionListResponse }>
}

export const listRoles = (params?: { keyword?: string; page?: number; size?: number }) => {
  return request.get('/api/v1/admin/roles/list', { params })
}

export const listGroups = (params?: { keyword?: string; page?: number; size?: number }) => {
  return request.get('/api/v1/admin/groups/list', { params })
}