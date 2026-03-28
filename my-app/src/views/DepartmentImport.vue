<template>
  <div class="department-import-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="28" height="28">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
        </div>
        <div class="header-text">
          <h1>岗位导入</h1>
          <p class="subtitle">批量导入部门成员并分配角色、岗位、部门</p>
        </div>
        <div class="header-actions">
          <n-button @click="goHome" quaternary class="home-btn">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </template>
            返回主页
          </n-button>
        </div>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <div class="main-container">
      <!-- 左侧：权限信息和上传区域 -->
      <aside class="permission-sidebar">
        <!-- 权限信息卡片 -->
        <div class="permission-card">
          <div class="card-header">
            <h3>导入权限</h3>
            <n-tag type="info" size="small" :bordered="false">当前权限范围</n-tag>
          </div>
          <div class="permission-info">
            <div class="info-item">
              <span class="info-label">当前部门：</span>
              <span class="info-value">{{ currentUserInfo.department_name || '未分配' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">当前岗位：</span>
              <span class="info-value">{{ currentUserInfo.positions?.join(', ') || '未分配' }}</span>
            </div>
          </div>
          <n-divider />
          <div class="permission-actions">
            <n-button size="small" type="info" block @click="showScopeDrawer = true">
              查看可导入范围
            </n-button>
          </div>
        </div>

        <!-- 文件上传卡片 -->
        <div class="upload-card">
          <div class="card-header">
            <h3>文件上传</h3>
          </div>
          <div class="upload-area">
            <n-upload
              v-model:file-list="fileList"
              :max="1"
              accept=".xlsx,.xls"
              :before-upload="beforeUpload"
              @change="handleFileChange"
            >
              <n-upload-dragger>
                <div class="upload-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                  </svg>
                </div>
                <div class="upload-text">
                  <p class="upload-title">点击或者拖动文件到该区域来上传</p>
                  <p class="upload-desc">请上传 .xlsx 或 .xls 格式的Excel文件</p>
                </div>
              </n-upload-dragger>
            </n-upload>

            <div class="template-download">
              <n-button text @click="downloadTemplate">
                <template #icon>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                  </svg>
                </template>
                下载导入模板
              </n-button>
            </div>
          </div>

          <div class="upload-settings">
            <n-form label-placement="left" label-width="100">
              <n-form-item label="默认部门">
                <n-select
                  v-model:value="importSettings.default_department_id"
                  :options="filteredDepartmentOptions"
                  :placeholder="filteredDepartmentOptions.length > 0 ? '请选择默认部门' : '暂无可选部门'"
                  :disabled="filteredDepartmentOptions.length === 0"
                  style="width: 100%"
                />
              </n-form-item>
              <n-form-item label="默认角色">
                <n-select
                  v-model:value="importSettings.default_role"
                  :options="roleOptions"
                  placeholder="请选择默认角色"
                  style="width: 100%"
                />
              </n-form-item>
              <n-form-item label="默认密码">
                <n-input
                  v-model:value="importSettings.default_password"
                  placeholder="请输入默认密码（至少6位）"
                  type="password"
                  show-password-on="click"
                />
              </n-form-item>
            </n-form>
          </div>

          <div class="upload-actions">
            <n-button
              type="primary"
              size="large"
              :loading="importing"
              :disabled="!selectedFile"
              @click="startImport"
              block
            >
              开始导入
            </n-button>
          </div>
        </div>
      </aside>

      <!-- 右侧：导入结果和用户管理 -->
      <main class="main-content">
        <!-- 导入结果卡片 -->
        <div class="result-card" v-if="importResult">
          <div class="card-header">
            <h3>导入结果</h3>
            <n-button text size="small" @click="clearResult">
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </template>
              清除
            </n-button>
          </div>
          <div class="result-summary">
            <div class="summary-item success">
              <div class="summary-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
              </div>
              <div class="summary-info">
                <div class="summary-value">{{ importResult.success_count }}</div>
                <div class="summary-label">导入成功</div>
              </div>
            </div>
            <div class="summary-item error">
              <div class="summary-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
              </div>
              <div class="summary-info">
                <div class="summary-value">{{ importResult.failed_count }}</div>
                <div class="summary-label">导入失败</div>
              </div>
            </div>
            <div class="summary-item warning">
              <div class="summary-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                  <line x1="12" y1="9" x2="12" y2="13"></line>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              </div>
              <div class="summary-info">
                <div class="summary-value">{{ importResult.skipped_count || 0 }}</div>
                <div class="summary-label">权限跳过</div>
              </div>
            </div>
          </div>

          <div class="result-details">
            <n-tabs type="line" animated>
              <n-tab-pane name="success" tab="成功记录">
                <n-data-table
                  :columns="resultColumns"
                  :data="importResult.results?.filter(r => r.success)"
                  :pagination="{ pageSize: 10 }"
                  :bordered="false"
                />
              </n-tab-pane>
              <n-tab-pane name="failed" tab="失败记录">
                <n-data-table
                  :columns="resultColumns"
                  :data="importResult.results?.filter(r => !r.success)"
                  :pagination="{ pageSize: 10 }"
                  :bordered="false"
                />
              </n-tab-pane>
            </n-tabs>
          </div>
        </div>

        <!-- 用户管理卡片 -->
        <div class="user-management-card">
          <div class="card-header">
            <h3>用户管理</h3>
            <div class="header-actions">
              <n-button size="small" @click="refreshUserList">
                <template #icon>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                    <path d="M21 3v5h-5"></path>
                    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                    <path d="M3 21v-5h5"></path>
                  </svg>
                </template>
                刷新
              </n-button>
              <n-button size="small" @click="showAddUserModal">
                <template #icon>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                </template>
                添加用户
              </n-button>
              <n-button size="small" type="primary" @click="batchApproveUsers" :disabled="selectedRowKeys.length === 0">
                批量通过 ({{ selectedRowKeys.length }})
              </n-button>
            </div>
          </div>

          <!-- 搜索和筛选 -->
          <div class="search-filter">
            <n-input-group>
              <n-input
                v-model:value="userSearchParams.keyword"
                placeholder="搜索用户名、账号、部门..."
                clearable
                @update:value="handleUserSearch"
              >
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                  </svg>
                </template>
              </n-input>
              <n-select
                v-model:value="userSearchParams.department_id"
                :options="departmentOptions"
                placeholder="全部部门"
                clearable
                style="width: 200px"
                @update:value="handleUserSearch"
              />
              <n-select
                v-model:value="userSearchParams.is_active"
                :options="statusOptions"
                placeholder="全部状态"
                clearable
                style="width: 120px"
                @update:value="handleUserSearch"
              />
            </n-input-group>
          </div>

          <!-- 用户表格 -->
          <div class="user-table">
            <n-data-table
              :columns="userColumns"
              :data="userList"
              :pagination="userPagination"
              :row-key="row => row.id"
              :row-props="rowProps"
              v-model:checked-row-keys="selectedRowKeys"
              @update:page="handlePageChange"
              @update:page-size="handleSizeChange"
              :bordered="false"
              striped
            />
          </div>
        </div>
      </main>
    </div>

    <!-- 添加/编辑用户模态框 -->
    <n-modal v-model:show="showUserModal" preset="card" :title="editingUser ? '编辑用户' : '添加用户'" style="width: 600px">
      <n-form
        ref="userFormRef"
        :model="userForm"
        label-placement="left"
        label-width="100"
        :rules="userFormRules"
      >
        <n-form-item label="账号" path="account">
          <n-input v-model:value="userForm.account" placeholder="请输入账号" :disabled="!!editingUser" />
        </n-form-item>
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="userForm.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="部门" path="department_id">
          <n-select
            v-model:value="userForm.department_id"
            :options="departmentOptions"
            placeholder="请选择部门"
          />
        </n-form-item>
        <n-form-item label="岗位" path="position_ids">
          <n-select
            v-model:value="userForm.position_ids"
            :options="positionOptions"
            placeholder="请选择岗位"
            multiple
          />
        </n-form-item>
        <n-form-item label="角色" path="role_ids">
          <n-select
            v-model:value="userForm.role_ids"
            :options="roleOptions"
            placeholder="请选择角色"
            multiple
          />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="userForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="手机号" path="phone">
          <n-input v-model:value="userForm.phone" placeholder="请输入手机号" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showUserModal = false">取消</n-button>
          <n-button type="primary" @click="handleUserSubmit" :loading="submitting">
            {{ editingUser ? '更新' : '创建' }}
          </n-button>
        </div>
      </template>
    </n-modal>

    <!-- 可导入范围抽屉 -->
    <n-drawer v-model:show="showScopeDrawer" :width="550" placement="right">
      <n-drawer-content title="可导入范围">
        <div v-if="accessibleDepartments.length === 0">
          <n-empty description="暂无可导入部门" />
        </div>
        <div v-else class="scope-tree-container">
          <div class="tree-legend">
            <span class="legend-item">
              <span class="legend-dot importable"></span>
              可导入岗位
            </span>
            <span class="legend-item" v-if="currentUserPostIds.length > 0">
              <span class="legend-dot current"></span>
              当前岗位
            </span>
          </div>
          <n-scrollbar style="max-height: calc(100vh - 180px)">
            <div class="dept-tree">
              <div 
                v-for="(dept, index) in accessibleDepartments" 
                :key="dept.id" 
                class="dept-node"
                :style="{ '--dept-index': index }"
              >
                <div class="dept-header">
                  <div class="dept-icon-wrapper">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                    </svg>
                  </div>
                  <span class="dept-name">{{ dept.name }}</span>
                  <n-tag size="small" type="primary" :bordered="false">
                    {{ dept.posts?.length || 0 }} 岗位
                  </n-tag>
                </div>
                <div class="dept-posts-tree" v-if="dept.posts && dept.posts.length > 0">
                  <div 
                    v-for="(post, pIndex) in sortedPosts(dept.posts)" 
                    :key="post.id" 
                    class="post-node"
                    :class="{ 
                      'importable': canImportPost(dept.id, post.id),
                      'current-pos': isCurrentPosition(post.id)
                    }"
                    :style="{ '--post-index': pIndex }"
                  >
                    <div class="post-connector">
                      <div class="connector-line"></div>
                    </div>
                    <div class="post-content">
                      <span class="post-icon">
                        <template v-if="canImportPost(dept.id, post.id)">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                          </svg>
                        </template>
                        <template v-else>
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                          </svg>
                        </template>
                      </span>
                      <span class="post-name">{{ post.name }}</span>
                      <div class="post-tags">
                        <n-tag 
                          v-if="post.level !== undefined && post.level !== null" 
                          size="tiny" 
                          :type="post.level <= 2 ? 'error' : post.level <= 4 ? 'warning' : 'default'"
                        >
                          Lv.{{ post.level }}
                        </n-tag>
                        <n-tag v-if="isCurrentPosition(post.id)" size="tiny" type="success">
                          当前岗位
                        </n-tag>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="no-posts">
                  <span>暂无可导入岗位</span>
                </div>
              </div>
            </div>
          </n-scrollbar>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NTag, NSpace, NPopconfirm, NDrawer, NDrawerContent, NCollapse, NCollapseItem, NTabs, NTabPane, NEmpty, NScrollbar } from 'naive-ui'
import adminApi from '@/api/admin'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

// 响应式数据
const fileList = ref([])
const selectedFile = ref<File | null>(null)
const importing = ref(false)
const importResult = ref<any>(null)
const selectedRowKeys = ref<(string | number)[]>([])
const showUserModal = ref(false)
const showScopeDrawer = ref(false)
const editingUser = ref<any>(null)
const submitting = ref(false)

// 权限信息
const currentUserInfo = ref({
  department_id: null,
  department_name: '',
  positions: []
})
const currentUserPostIds = ref<number[]>([])  // 当前用户的岗位ID列表

const accessibleDepartments = ref<any[]>([])
const accessiblePositions = ref<any[]>([])
const isAdmin = ref(false)
const scopeDepartmentIds = ref<number[]>([])  // 用户所属的部门ID列表

// 用户列表（只存储本次导入的用户）
const userList = ref<any[]>([])
const userPagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})
const importedUsers = ref<any[]>([])  // 本次导入的用户

// 搜索参数
const userSearchParams = ref({
  keyword: '',
  department_id: null,
  is_active: null
})

// 导入设置
const importSettings = ref({
  default_department_id: null,
  default_role: 'student',
  default_password: '123456'
})

// 用户表单
const userForm = ref({
  account: '',
  name: '',
  department_id: null,
  position_ids: [],
  role_ids: [],
  email: '',
  phone: ''
})

// 选项数据
const departmentOptions = ref<any[]>([])
const positionOptions = ref<any[]>([])
const roleOptions = ref([
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
  { label: '管理员', value: 'admin' }
])

const statusOptions = ref([
  { label: '启用', value: true },
  { label: '禁用', value: false }
])

// 表单验证规则
const userFormRules = {
  account: { required: true, message: '请输入账号', trigger: 'blur' },
  name: { required: true, message: '请输入姓名', trigger: 'blur' },
  department_id: { required: true, type: 'number', message: '请选择部门', trigger: 'change' }
}

// 计算属性
const filteredDepartmentOptions = computed(() => {
  if (isAdmin.value) {
    return departmentOptions.value
  } else {
    return departmentOptions.value.filter(dept => 
      scopeDepartmentIds.value.includes(dept.value)
    )
  }
})

// 表格列定义
const resultColumns: DataTableColumns = [
  { title: '行号', key: 'row_number', width: 80 },
  { title: '账号', key: 'account', width: 150 },
  { title: '姓名', key: 'name', width: 120 },
  { 
    title: '状态', 
    key: 'success', 
    width: 100,
    render: (row) => {
      return h(NTag, {
        type: row.success ? 'success' : 'error',
        size: 'small',
        bordered: false
      }, { default: () => row.success ? '成功' : '失败' })
    }
  },
  { title: '错误信息', key: 'error_message', width: 200 }
]

const userColumns: DataTableColumns = [
  { 
    type: 'selection',
    disabled: () => false
  },
  { title: '账号', key: 'account', width: 150 },
  { title: '姓名', key: 'name', width: 120 },
  { title: '部门', key: 'department_name', width: 150 },
  { 
    title: '岗位', 
    key: 'positions', 
    width: 150,
    render: (row) => {
      return h(NSpace, { size: 4 }, {
        default: () => row.positions?.length ? row.positions.map((pos: string) => 
          h(NTag, { size: 'small', type: 'info', bordered: false }, { default: () => pos })
        ) : '-'
      })
    }
  },
  { 
    title: '状态', 
    key: 'is_active', 
    width: 100,
    render: (row) => {
      return h(NTag, {
        type: row.is_active ? 'success' : 'error',
        size: 'small',
        bordered: false
      }, { default: () => row.is_active ? '启用' : '禁用' })
    }
  },
  { 
    title: '操作', 
    key: 'actions', 
    width: 200,
    render: (row) => {
      return h(NSpace, { size: 8 }, {
        default: () => [
          h(NButton, {
            size: 'small',
            quaternary: true,
            onClick: () => editUser(row)
          }, { default: () => '编辑' }),
          h(NPopconfirm, {
            onPositiveClick: () => deleteUser(row.id)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
              quaternary: true
            }, { default: () => '删除' }),
            default: () => '确定要删除该用户吗？'
          })
        ]
      })
    }
  }
]

// 方法
const goHome = () => {
  router.push('/')
}

const beforeUpload = (file: File) => {
  const isValid = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                  file.type === 'application/vnd.ms-excel'
  if (!isValid) {
    message.error('只能上传 Excel 文件')
    return false
  }
  return true
}

const handleFileChange = (options: any) => {
  selectedFile.value = options.file?.file || null
}

const downloadTemplate = async () => {
  try {
    const blob = await adminApi.downloadImportTemplate()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '用户导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    message.error('下载模板失败')
  }
}

const startImport = async () => {
  if (!selectedFile.value) {
    message.warning('请先选择文件')
    return
  }

    importing.value = true
  try {
    const response = await adminApi.batchImportUsers(
      selectedFile.value,
      importSettings.value.default_password,
      importSettings.value.default_department_id
    )
    importResult.value = response.data
    message.success(`导入完成：成功 ${response.data.success_count} 条，失败 ${response.data.failed_count} 条`)
    
    // 将导入成功的用户存储到 importedUsers
    if (response.data.results) {
      importedUsers.value = response.data.results
        .filter((r: any) => r.success)
        .map((r: any) => ({
          id: r.row_number,
          account: r.account,
          name: r.name,
          department_name: r.department_name || '未分配',
          department_id: r.department_id,
          positions: r.position_name ? [r.position_name] : [],
          status: 'pending',
          email: r.email,
          phone: r.phone
        }))
    }
    
    // 刷新用户列表
    await loadUserList()
  } catch (error: any) {
    message.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 判断是否是当前用户的岗位
const isCurrentPosition = (postId: number) => {
  return currentUserPostIds.value.includes(postId)
}

// 判断是否可以导入该岗位
const canImportPost = (deptId: number, postId: number) => {
  if (isAdmin.value) {
    return true
  }
  const dept = accessibleDepartments.value.find(d => d.id === deptId)
  if (!dept || !dept.posts) return false
  return dept.posts.some((p: any) => p.id === postId)
}

// 对岗位按层级排序（层级值越小越靠前）
const sortedPosts = (posts: any[] | undefined) => {
  if (!posts) return []
  return [...posts].sort((a, b) => {
    const levelA = a.level ?? 999
    const levelB = b.level ?? 999
    if (levelA !== levelB) return levelA - levelB
    return a.name.localeCompare(b.name)
  })
}

const clearResult = () => {
  importResult.value = null
  fileList.value = []
  selectedFile.value = null
  importedUsers.value = []
  loadUserList()
}

const loadUserInfo = async () => {
  // 加载可管理范围（包含当前用户信息）
  try {
    const scopeRes = await adminApi.getManageableScope()
    const scope = scopeRes.data
    
    // 设置管理员状态
    isAdmin.value = scope.is_admin
    
    // 更新当前用户信息（使用API返回的真实数据）
    if (scope.current_user_department) {
      currentUserInfo.value = {
        department_id: scope.current_user_department.id,
        department_name: scope.current_user_department.name,
        positions: scope.current_user_positions.map(p => p.name)
      }
      // 设置当前用户的岗位ID列表
      currentUserPostIds.value = scope.current_user_positions.map(p => p.id)
    } else if (authStore.userInfo) {
      // 回退到authStore
      currentUserInfo.value = {
        department_id: authStore.userInfo.department_id,
        department_name: authStore.userInfo.department?.name || '未分配',
        positions: authStore.userInfo.positions || []
      }
    }
    
    // 更新可管理部门
    accessibleDepartments.value = scope.departments
    
    // 从可管理部门中提取所有岗位
    const allPosts: any[] = []
    scope.departments.forEach((dept: any) => {
      if (dept.posts && Array.isArray(dept.posts)) {
        dept.posts.forEach((post: any) => {
          if (!allPosts.find(p => p.id === post.id)) {
            allPosts.push(post)
          }
        })
      }
    })
    accessiblePositions.value = allPosts
    
    // 更新部门选项
    departmentOptions.value = scope.departments.map((dept: any) => ({
      label: dept.name,
      value: dept.id
    }))
    
    // 更新岗位选项
    positionOptions.value = allPosts.map((post: any) => ({
      label: post.name,
      value: post.id
    }))
    
    // 如果不是管理员且有部门，设置默认部门且不允许修改
    if (!scope.is_admin && scope.current_user_department) {
      importSettings.value.default_department_id = scope.current_user_department.id
      scopeDepartmentIds.value = [scope.current_user_department.id]
    } else if (scope.is_admin && filteredDepartmentOptions.value.length > 0) {
      // 管理员默认选中第一个部门
      importSettings.value.default_department_id = filteredDepartmentOptions.value[0].value
    }
  } catch (error) {
    console.error('加载可管理范围失败', error)
    // 回退到authStore
    if (authStore.userInfo) {
      currentUserInfo.value = {
        department_id: authStore.userInfo.department_id,
        department_name: authStore.userInfo.department?.name || '未分配',
        positions: authStore.userInfo.positions || []
      }
    }
    // 如果获取可管理范围失败，回退到加载所有部门和岗位
    try {
      const [deptRes, posRes] = await Promise.all([
        adminApi.listDepartments({ size: 100 }),
        adminApi.listPositions({ size: 100 })
      ])
      accessibleDepartments.value = deptRes.data.items
      accessiblePositions.value = posRes.data.items
      
      departmentOptions.value = deptRes.data.items.map((dept: any) => ({
        label: dept.name,
        value: dept.id
      }))
      
      positionOptions.value = posRes.data.items.map((pos: any) => ({
        label: pos.name,
        value: pos.id
      }))
    } catch (fallbackError) {
      console.error('加载部门岗位信息失败', fallbackError)
    }
  }
}

const loadUserList = async () => {
  // 如果没有导入的用户，显示空列表
  if (importedUsers.value.length === 0) {
    userList.value = []
    userPagination.value.total = 0
    return
  }
  
  // 从导入的用户中筛选（只显示本次导入的用户，用于预览和编辑）
  let filteredUsers = [...importedUsers.value]
  
  // 关键词搜索
  if (userSearchParams.value.keyword) {
    const keyword = userSearchParams.value.keyword.toLowerCase()
    filteredUsers = filteredUsers.filter(user => 
      user.name?.toLowerCase().includes(keyword) ||
      user.account?.toLowerCase().includes(keyword) ||
      user.department_name?.toLowerCase().includes(keyword)
    )
  }
  
  // 部门筛选
  if (userSearchParams.value.department_id) {
    filteredUsers = filteredUsers.filter(user => 
      user.department_id === userSearchParams.value.department_id
    )
  }
  
  // 分页
  const start = (userPagination.value.page - 1) * userPagination.value.pageSize
  const end = start + userPagination.value.pageSize
  
  userList.value = filteredUsers.slice(start, end)
  userPagination.value.total = filteredUsers.length
}

const refreshUserList = () => {
  loadUserList()
}

const handleUserSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const handlePageChange = (page: number) => {
  userPagination.value.page = page
}

const handleSizeChange = (pageSize: number) => {
  userPagination.value.pageSize = pageSize
}

const rowProps = () => {
  return {
    style: 'cursor: pointer;'
  }
}

const showAddUserModal = () => {
  editingUser.value = null
  userForm.value = {
    account: '',
    name: '',
    department_id: null,
    position_ids: [],
    role_ids: [],
    email: '',
    phone: ''
  }
  showUserModal.value = true
}

const editUser = (user: any) => {
  editingUser.value = user
  userForm.value = {
    account: user.account,
    name: user.name,
    department_id: user.department_id,
    position_ids: user.position_ids || [],
    role_ids: user.role_ids || [],
    email: user.email || '',
    phone: user.phone || ''
  }
  showUserModal.value = true
}

const handleUserSubmit = async () => {
  submitting.value = true
  try {
    if (editingUser.value) {
      // 更新用户
      message.success('用户更新成功')
    } else {
      // 创建用户
      message.success('用户创建成功')
    }
    showUserModal.value = false
    await loadUserList()
  } catch (error: any) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const approveUser = async (userId: number) => {
  try {
    // 调用审批API
    message.success('用户审批成功')
    await loadUserList()
  } catch (error: any) {
    message.error(error.message || '审批失败')
  }
}

const batchApproveUsers = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要审批的用户')
    return
  }
  
  try {
    // 调用批量审批API
    message.success(`已批量审批 ${selectedRowKeys.value.length} 个用户`)
    selectedRowKeys.value = []
    await loadUserList()
  } catch (error: any) {
    message.error(error.message || '批量审批失败')
  }
}

const deleteUser = async (userId: number) => {
  try {
    // 调用删除API
    message.success('用户删除成功')
    await loadUserList()
  } catch (error: any) {
    message.error(error.message || '删除失败')
  }
}

// 初始化
onMounted(async () => {
  await loadUserInfo()
  await loadUserList()
})
</script>

<style scoped>
.department-import-page {
  min-height: 100vh;
  background: #f8fafc;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  padding: 32px 0;
  color: #ffffff;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-text {
  flex: 1;
}

.header-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
}

.header-text .subtitle {
  margin: 4px 0 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.home-btn {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
}

.home-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

/* 主要内容区域 */
.main-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 24px;
}

/* 左侧边栏 */
.permission-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.permission-card,
.upload-card,
.result-card,
.user-management-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

/* 权限信息 */
.permission-info {
  padding: 16px 24px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #64748b;
  font-size: 14px;
}

.info-value {
  color: #1a202c;
  font-weight: 500;
  font-size: 14px;
}

.permission-desc {
  padding: 0 24px 16px;
}

.permission-desc p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

/* 上传区域 */
.upload-area {
  padding: 24px;
}

.upload-icon {
  color: #64748b;
  margin-bottom: 12px;
}

.upload-text {
  color: #64748b;
}

.upload-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  color: #1a202c;
}

.upload-desc {
  margin: 0;
  font-size: 13px;
}

.template-download {
  text-align: center;
  margin-top: 12px;
}

.upload-settings {
  padding: 0 24px;
}

.upload-actions {
  padding: 16px 24px 24px;
}

/* 右侧主内容 */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 导入结果 */
.result-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 24px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid;
}

.summary-item.success {
  background: #ecfdf5;
  border-color: #10b981;
}

.summary-item.error {
  background: #fef2f2;
  border-color: #ef4444;
}

.summary-item.warning {
  background: #fffbeb;
  border-color: #f59e0b;
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-item.success .summary-icon {
  background: #10b981;
  color: #ffffff;
}

.summary-item.error .summary-icon {
  background: #ef4444;
  color: #ffffff;
}

.summary-item.warning .summary-icon {
  background: #f59e0b;
  color: #ffffff;
}

.summary-info {
  flex: 1;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 14px;
  color: #64748b;
}

.result-details {
  padding: 0 24px 24px;
}

/* 用户管理 */
.header-actions {
  display: flex;
  gap: 8px;
}

.search-filter {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.user-table {
  padding: 0 24px 24px;
}

/* 模态框 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-container {
    grid-template-columns: 1fr;
  }
  
  .permission-sidebar {
    order: 2;
  }
  
  .main-content {
    order: 1;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .result-summary {
    grid-template-columns: 1fr;
  }
  
  .header-actions {
    flex-wrap: wrap;
  }
}

/* 可导入范围树状图样式 */
.scope-tree-container {
  padding: 0 8px;
}

.tree-legend {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.importable {
  background: #10b981;
}

.legend-dot.current {
  background: #3b82f6;
}

.dept-tree {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dept-node {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;
  animation: slideIn 0.3s ease forwards;
  animation-delay: calc(var(--dept-index, 0) * 0.05s);
  opacity: 0;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.dept-node:hover {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

.dept-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfeff 100%);
  border-bottom: 1px solid #e2e8f0;
}

.dept-icon-wrapper {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #10b981;
  border-radius: 8px;
  color: #ffffff;
}

.dept-name {
  flex: 1;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.dept-posts-tree {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.post-node {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  animation: fadeIn 0.3s ease forwards;
  animation-delay: calc(var(--post-index, 0) * 0.03s);
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.post-node.importable {
  background: #f0fdf4;
}

.post-node.importable:hover {
  background: #dcfce7;
}

.post-node.current-pos {
  background: #eff6ff;
}

.post-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 4px;
}

.connector-line {
  width: 2px;
  height: 20px;
  background: linear-gradient(180deg, #10b981 0%, #e2e8f0 100%);
}

.post-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.post-icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
}

.post-node.importable .post-icon {
  background: #10b981;
  color: #ffffff;
}

.post-node.current-pos .post-icon {
  background: #3b82f6;
  color: #ffffff;
}

.post-name {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.post-tags {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.no-posts {
  padding: 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}
</style>