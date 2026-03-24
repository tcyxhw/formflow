# 表单填写工作区设计文档

## 概述

表单填写工作区是FormFlow系统的核心用户界面，为用户提供统一的表单访问入口。本设计实现了基于权限的表单列表展示、实时搜索过滤、分页加载、状态筛选和快捷导航等功能。系统通过集成现有的表单权限系统，确保用户只能访问其被授权的表单，同时提供流畅的用户体验。

设计遵循前后端分离架构，后端提供RESTful API接口，前端使用Vue3组合式API构建响应式界面。权限检查在后端进行，前端根据权限状态动态调整UI展示。

## 架构

### 系统架构图

```mermaid
graph TB
    subgraph "前端层 - Vue3"
        A[FillWorkspace.vue] --> B[FormCard组件]
        A --> C[SearchBar组件]
        A --> D[FilterPanel组件]
        A --> E[QuickAccess组件]
        A --> F[useFillWorkspace组合函数]
    end
    
    subgraph "API层 - FastAPI"
        G[/api/v1/forms/fillable] --> H[FormWorkspaceService]
        I[/api/v1/forms/:id/quick-access] --> H
    end
    
    subgraph "服务层"
        H --> J[FormPermissionService]
        H --> K[FormService]
        J --> L[(PostgreSQL)]
        K --> L
    end
    
    F --> G
    F --> I
    
    style A fill:#e1f5ff
    style G fill:#fff4e1
    style H fill:#f0e1ff
```

### 数据流向

1. **表单列表加载流程**:
   - 用户访问工作区 → 前端发起GET请求 → 后端查询用户权限 → 过滤可填写表单 → 返回分页数据 → 前端渲染列表

2. **搜索过滤流程**:
   - 用户输入关键词 → 前端防抖处理 → 发起带搜索参数的请求 → 后端执行模糊匹配 → 返回过滤结果 → 更新列表显示

3. **权限检查流程**:
   - 用户点击表单 → 前端导航 → 后端拦截请求 → 验证FILL权限 → 允许/拒绝访问 → 返回表单或403错误

## 组件与接口

### 后端API接口

#### 1. 获取可填写表单列表

**端点**: `GET /api/v1/forms/fillable`

**描述**: 返回当前用户有权填写的表单列表，支持搜索、筛选、排序和分页。

**请求参数**:
```python
class FillableFormsQuery(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(default=None, description="搜索关键词")
    status: Optional[str] = Field(default=None, description="表单状态筛选")
    category: Optional[str] = Field(default=None, description="表单类别筛选")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向: asc/desc")
```

**响应数据**:
```python
class FillableFormItem(BaseModel):
    id: int
    name: str
    category: Optional[str]
    status: str
    owner_name: str
    created_at: datetime
    updated_at: datetime
    submit_deadline: Optional[datetime]
    is_expired: bool
    is_closed: bool
    can_fill: bool
    description: Optional[str]

class FillableFormsResponse(BaseModel):
    items: List[FillableFormItem]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**权限要求**: 已认证用户

**业务逻辑**:
1. 验证用户身份和租户上下文
2. 调用`FormPermissionService.get_user_fillable_forms()`获取有FILL权限的表单ID列表
3. 根据表单ID列表查询表单详情
4. 应用搜索关键词过滤（标题、描述）
5. 应用状态和类别筛选
6. 执行排序和分页
7. 计算每个表单的状态标识（是否过期、是否关闭）
8. 返回分页结果

#### 2. 添加/移除快捷入口

**端点**: `POST /api/v1/forms/{form_id}/quick-access`

**描述**: 将表单添加到用户的快捷入口列表。

**请求体**: 无

**响应**: 
```python
{
    "code": 0,
    "message": "已添加到快捷入口",
    "data": {"form_id": 123}
}
```

**端点**: `DELETE /api/v1/forms/{form_id}/quick-access`

**描述**: 从快捷入口列表移除表单。

**响应**: 
```python
{
    "code": 0,
    "message": "已从快捷入口移除"
}
```

#### 3. 获取快捷入口列表

**端点**: `GET /api/v1/forms/quick-access`

**描述**: 获取用户的快捷入口表单列表。

**响应数据**:
```python
class QuickAccessResponse(BaseModel):
    items: List[FillableFormItem]
```

### 前端组件设计

#### 1. FillWorkspace.vue (主容器组件)

**职责**:
- 管理工作区整体布局
- 协调子组件交互
- 处理路由导航

**状态管理**:
```typescript
interface WorkspaceState {
    forms: FillableFormItem[]
    loading: boolean
    error: string | null
    pagination: PaginationState
    filters: FilterState
    searchKeyword: string
}
```

**关键方法**:
- `loadForms()`: 加载表单列表
- `handleSearch(keyword: string)`: 处理搜索
- `handleFilter(filters: FilterState)`: 处理筛选
- `handlePageChange(page: number)`: 处理分页
- `navigateToForm(formId: number)`: 导航到表单填写页

#### 2. FormCard.vue (表单卡片组件)

**Props**:
```typescript
interface FormCardProps {
    form: FillableFormItem
    isQuickAccess: boolean
}
```

**功能**:
- 显示表单基本信息（标题、类别、创建时间）
- 根据状态显示不同的视觉标识
- 提供操作按钮（填写、查看详情、添加快捷入口）
- 鼠标悬停显示完整描述

#### 3. SearchBar.vue (搜索栏组件)

**Props**:
```typescript
interface SearchBarProps {
    modelValue: string
    placeholder: string
    debounce: number
}
```

**功能**:
- 实时搜索输入
- 防抖处理（默认300ms）
- 清除按钮
- ESC键清除

#### 4. FilterPanel.vue (筛选面板组件)

**Props**:
```typescript
interface FilterPanelProps {
    modelValue: FilterState
    categories: string[]
}
```

**功能**:
- 状态筛选（待填写、进行中、已截止）
- 类别筛选
- 时间范围筛选
- 清除所有筛选

#### 5. QuickAccess.vue (快捷入口组件)

**功能**:
- 显示快捷入口表单列表
- 支持拖拽排序
- 快速导航到表单
- 移除快捷入口

### 前端API客户端

```typescript
// src/api/workspace.ts
export interface FillableFormsQuery {
    page?: number
    page_size?: number
    keyword?: string
    status?: string
    category?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
}

export const getFillableForms = (
    params?: FillableFormsQuery
): Promise<Response<FillableFormsResponse>> => {
    return request.get('/api/v1/forms/fillable', { params })
}

export const addQuickAccess = (formId: number): Promise<Response<void>> => {
    return request.post(`/api/v1/forms/${formId}/quick-access`)
}

export const removeQuickAccess = (formId: number): Promise<Response<void>> => {
    return request.delete(`/api/v1/forms/${formId}/quick-access`)
}

export const getQuickAccessForms = (): Promise<Response<QuickAccessResponse>> => {
    return request.get('/api/v1/forms/quick-access')
}
```

### 组合式函数

```typescript
// src/composables/useFillWorkspace.ts
export function useFillWorkspace() {
    const forms = ref<FillableFormItem[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const pagination = reactive({
        page: 1,
        pageSize: 20,
        total: 0,
        totalPages: 0
    })
    
    const filters = reactive({
        keyword: '',
        status: null,
        category: null,
        sortBy: 'created_at',
        sortOrder: 'desc'
    })
    
    const loadForms = async () => {
        loading.value = true
        error.value = null
        try {
            const { data } = await getFillableForms({
                page: pagination.page,
                page_size: pagination.pageSize,
                ...filters
            })
            forms.value = data.items
            pagination.total = data.total
            pagination.totalPages = data.total_pages
        } catch (e) {
            error.value = '加载表单列表失败'
        } finally {
            loading.value = false
        }
    }
    
    const debouncedSearch = useDebounceFn((keyword: string) => {
        filters.keyword = keyword
        pagination.page = 1
        loadForms()
    }, 300)
    
    return {
        forms,
        loading,
        error,
        pagination,
        filters,
        loadForms,
        debouncedSearch
    }
}
```

## 数据模型

### 数据库模型扩展

需要新增用户快捷入口表：

```python
class UserQuickAccess(DBBaseModel):
    """用户快捷入口表"""
    __tablename__ = "user_quick_access"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "form_id", name="uq_user_quick_access"),
        Index("idx_user_quick_access", "user_id", "tenant_id"),
    )
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="用户ID")
    form_id = Column(Integer, ForeignKey("form.id"), nullable=False, comment="表单ID")
    sort_order = Column(Integer, default=0, comment="排序顺序")
```

### Pydantic Schema

```python
# backend/app/schemas/workspace_schemas.py

class FillableFormsQuery(BaseModel):
    """可填写表单查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(default=None, max_length=100, description="搜索关键词")
    status: Optional[str] = Field(default=None, description="表单状态筛选")
    category: Optional[str] = Field(default=None, description="表单类别筛选")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="排序方向")


class FillableFormItem(BaseModel):
    """可填写表单项"""
    id: int
    name: str
    category: Optional[str]
    status: str
    owner_name: str
    created_at: datetime
    updated_at: datetime
    submit_deadline: Optional[datetime]
    is_expired: bool
    is_closed: bool
    can_fill: bool
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class FillableFormsResponse(BaseModel):
    """可填写表单列表响应"""
    items: List[FillableFormItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class QuickAccessResponse(BaseModel):
    """快捷入口响应"""
    items: List[FillableFormItem]
```

### TypeScript类型定义

```typescript
// my-app/src/types/workspace.ts

export interface FillableFormItem {
    id: number
    name: string
    category: string | null
    status: string
    owner_name: string
    created_at: string
    updated_at: string
    submit_deadline: string | null
    is_expired: boolean
    is_closed: boolean
    can_fill: boolean
    description: string | null
}

export interface FillableFormsResponse {
    items: FillableFormItem[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface FillableFormsQuery {
    page?: number
    page_size?: number
    keyword?: string
    status?: string
    category?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
}

export interface FilterState {
    keyword: string
    status: string | null
    category: string | null
    sortBy: string
    sortOrder: 'asc' | 'desc'
}

export interface PaginationState {
    page: number
    pageSize: number
    total: number
    totalPages: number
}
```

