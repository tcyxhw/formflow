<template>
  <div class="user-management-container">
    <!-- 页面头部 -->
    <div class="page-header-section">
      <div class="header-left">
        <h1 class="page-title">用户信息管理</h1>
        <div class="action-buttons">
          <n-button type="primary" @click="showAddUserModal = true">
            <template #icon>
              <n-icon><add-outline /></n-icon>
            </template>
            新增用户
          </n-button>
          <n-button @click="showImportModal = true">
            <template #icon>
              <n-icon><cloud-upload-outline /></n-icon>
            </template>
            批量导入
          </n-button>
          <n-button @click="downloadTemplate" :loading="downloading">
            <template #icon>
              <n-icon><download-outline /></n-icon>
            </template>
            下载模板
          </n-button>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <n-card class="filter-card">
      <n-space>
        <n-input
          v-model:value="filters.keyword"
          placeholder="搜索姓名/账号"
          clearable
          style="width: 200px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <n-icon><search-outline /></n-icon>
          </template>
        </n-input>

        <n-select
          v-model:value="filters.department_id"
          placeholder="选择部门"
          clearable
          style="width: 180px"
          :options="departmentOptions"
          @update:value="handleDepartmentChange"
        />

        <n-select
          v-model:value="filters.post_id"
          placeholder="选择岗位"
          clearable
          style="width: 180px"
          :options="postOptions"
          :disabled="!filters.department_id"
        />

        <n-button type="primary" @click="handleSearch">
          <template #icon>
            <n-icon><search-outline /></n-icon>
          </template>
          搜索
        </n-button>

        <n-button @click="handleReset">
          <template #icon>
            <n-icon><refresh-outline /></n-icon>
          </template>
          重置
        </n-button>
      </n-space>
    </n-card>

    <!-- 用户列表 -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-key="rowKey"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <!-- 批量导入对话框 -->
    <n-modal
      v-model:show="showImportModal"
      preset="card"
      title="批量导入用户"
      style="width: 900px"
      :mask-closable="false"
    >
      <!-- 步骤1: 上传文件 -->
      <div v-if="importStep === 'upload'">
        <n-upload
          v-model:file-list="fileList"
          :max="1"
          accept=".xlsx,.xls"
          :before-upload="beforeUpload"
          @change="handleFileChange"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 12px">
              <n-icon size="48" :depth="3">
                <archive-outline />
              </n-icon>
            </div>
            <n-text style="font-size: 16px">
              点击或者拖动文件到该区域来上传
            </n-text>
            <n-p depth="3" style="margin: 8px 0 0 0">
              请上传 .xlsx 或 .xls 格式的Excel文件
            </n-p>
          </n-upload-dragger>
        </n-upload>

        <n-space justify="end" style="margin-top: 16px">
          <n-button @click="showImportModal = false">取消</n-button>
          <n-button
            type="primary"
            :loading="previewing"
            :disabled="!selectedFile"
            @click="handlePreview"
          >
            预览
          </n-button>
        </n-space>
      </div>

      <!-- 步骤2: 预览确认 -->
      <div v-if="importStep === 'preview'">
        <n-descriptions bordered :column="3" style="margin-bottom: 16px">
          <n-descriptions-item label="总行数">
            {{ previewData?.rows?.length || 0 }}
          </n-descriptions-item>
          <n-descriptions-item label="有效记录">
            <n-tag type="success">{{ previewData?.valid_count || 0 }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="无效记录">
            <n-tag type="error">{{ previewData?.invalid_count || 0 }}</n-tag>
          </n-descriptions-item>
        </n-descriptions>

        <n-data-table
          :columns="previewColumns"
          :data="previewData?.rows || []"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: ImportPreviewRow) => row.row_number"
          :row-class-name="getPreviewRowClassName"
        />

        <n-space justify="end" style="margin-top: 16px">
          <n-button @click="importStep = 'upload'">上一步</n-button>
          <n-button @click="handleCancelImport">取消</n-button>
          <n-button
            type="primary"
            :loading="confirming"
            :disabled="selectedImportRows.length === 0"
            @click="handleConfirmImport"
          >
            确认导入 ({{ selectedImportRows.length }})
          </n-button>
        </n-space>
      </div>
    </n-modal>

    <!-- 新增/编辑用户对话框 -->
    <n-modal
      v-model:show="showAddUserModal"
      preset="card"
      :title="editingUser ? '编辑用户' : '新增用户'"
      style="width: 600px"
      :mask-closable="false"
    >
      <n-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item label="账号" path="account">
          <n-input
            v-model:value="userForm.account"
            placeholder="请输入账号"
            :disabled="!!editingUser"
          />
        </n-form-item>

        <n-form-item label="姓名" path="name">
          <n-input v-model:value="userForm.name" placeholder="请输入姓名" />
        </n-form-item>

        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="userForm.email" placeholder="请输入邮箱" />
        </n-form-item>

        <n-form-item label="手机号" path="phone">
          <n-input v-model:value="userForm.phone" placeholder="请输入手机号" />
        </n-form-item>

        <n-form-item label="部门" path="department_id">
          <n-select
            v-model:value="userForm.department_id"
            placeholder="请选择部门"
            :options="departmentOptions"
            @update:value="handleFormDepartmentChange"
          />
        </n-form-item>

        <n-form-item label="岗位" path="post_id">
          <n-select
            v-model:value="userForm.post_id"
            placeholder="请选择岗位"
            :options="formPostOptions"
            :disabled="!userForm.department_id"
          />
        </n-form-item>

        <n-form-item label="角色" path="role">
          <n-select
            v-model:value="userForm.role"
            placeholder="请选择角色"
            :options="roleOptions"
          />
        </n-form-item>

        <n-form-item label="状态" path="is_active">
          <n-switch v-model:value="userForm.is_active" />
        </n-form-item>
      </n-form>

      <n-space justify="end">
        <n-button @click="handleCancelEdit">取消</n-button>
        <n-button type="primary" :loading="saving" @click="handleSaveUser">
          保存
        </n-button>
      </n-space>
    </n-modal>

    <!-- 用户详情抽屉 -->
    <n-drawer v-model:show="showDetailDrawer" :width="500" placement="right">
      <n-drawer-content title="用户详情">
        <n-descriptions v-if="detailUser" label-placement="left" :column="1" bordered>
          <n-descriptions-item label="账号">{{ detailUser.account }}</n-descriptions-item>
          <n-descriptions-item label="姓名">{{ detailUser.name }}</n-descriptions-item>
          <n-descriptions-item label="邮箱">{{ detailUser.email || '-' }}</n-descriptions-item>
          <n-descriptions-item label="手机号">{{ detailUser.phone || '-' }}</n-descriptions-item>
          <n-descriptions-item label="部门">{{ detailUser.department_name || '-' }}</n-descriptions-item>
          <n-descriptions-item label="岗位">
            {{ detailUser.positions?.join(', ') || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="角色">
            {{ formatRole(detailUser.roles || [detailUser.role]) }}
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="detailUser.is_active ? 'success' : 'default'" size="small">
              {{ detailUser.is_active ? '启用' : '禁用' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ detailUser.created_at || '-' }}
          </n-descriptions-item>
        </n-descriptions>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import {
  NCard,
  NButton,
  NIcon,
  NSpace,
  NInput,
  NSelect,
  NDataTable,
  NModal,
  NUpload,
  NUploadDragger,
  NText,
  NP,
  NTag,
  NDescriptions,
  NDescriptionsItem,
  NForm,
  NFormItem,
  NSwitch,
  NDrawer,
  NDrawerContent,
  useMessage,
  useDialog
} from 'naive-ui'
import type { DataTableColumns, UploadFileInfo, FormInst, FormRules } from 'naive-ui'
import {
  AddOutline,
  CloudUploadOutline,
  DownloadOutline,
  SearchOutline,
  RefreshOutline,
  ArchiveOutline,
  CreateOutline,
  TrashOutline
} from '@vicons/ionicons5'
import {
  getUsers,
  updateUser,
  deleteUser,
  getManageableScope,
  previewImportUsers,
  confirmImportUsers,
  downloadImportTemplate,
  listDepartments,
  listPositions,
  listRoles
} from '@/api/admin'
import type {
  UserListItem,
  UserListQuery,
  ManageableDepartment,
  ImportPreviewRow,
  ImportPreviewResponse
} from '@/api/admin'

const message = useMessage()
const dialog = useDialog()

// ========== 状态管理 ==========
const loading = ref(false)
const saving = ref(false)
const downloading = ref(false)
const previewing = ref(false)
const confirming = ref(false)

// 用户详情抽屉
const showDetailDrawer = ref(false)
const detailUser = ref<UserListItem | null>(null)

// 筛选条件
const filters = reactive({
  keyword: '',
  department_id: null as number | null,
  post_id: null as number | null
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})

// 表格数据
const tableData = ref<UserListItem[]>([])

// 部门和岗位选项
const departments = ref<ManageableDepartment[]>([])
const departmentOptions = computed(() =>
  departments.value.map(d => ({ label: d.name, value: d.id }))
)
const postOptions = computed(() => {
  const dept = departments.value.find(d => d.id === filters.department_id)
  return dept?.posts.map(p => ({ label: p.name, value: p.id })) || []
})

// 角色选项
const roleOptions = [
  { label: '管理员', value: 'admin' },
  { label: '教师', value: 'teacher' },
  { label: '学生', value: 'student' }
]

// ========== 批量导入状态 ==========
const showImportModal = ref(false)
const importStep = ref<'upload' | 'preview'>('upload')
const fileList = ref<UploadFileInfo[]>([])
const selectedFile = ref<File | null>(null)
const previewData = ref<ImportPreviewResponse | null>(null)
const selectedImportRows = ref<number[]>([])

// ========== 用户表单状态 ==========
const showAddUserModal = ref(false)
const editingUser = ref<UserListItem | null>(null)
const userFormRef = ref<FormInst | null>(null)
const userForm = reactive({
  account: '',
  name: '',
  email: null as string | null,
  phone: null as string | null,
  department_id: null as number | null,
  post_id: null as number | null,
  role: 'student',
  is_active: true
})

const formPostOptions = computed(() => {
  const dept = departments.value.find(d => d.id === userForm.department_id)
  return dept?.posts.map(p => ({ label: p.name, value: p.id })) || []
})

const userFormRules: FormRules = {
  account: [
    { required: true, message: '请输入账号', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// ========== 表格列定义 ==========
const columns: DataTableColumns<UserListItem> = [
  { title: '姓名', key: 'name', width: 100 },
  { title: '账号', key: 'account', width: 120 },
  { title: '部门', key: 'department_name', width: 150, ellipsis: { tooltip: true } },
  { 
    title: '岗位', 
    key: 'positions', 
    width: 120, 
    ellipsis: { tooltip: true },
    render: (row) => {
      if (row.positions && row.positions.length > 0) {
        return row.positions.join(', ')
      }
      return '-'
    }
  },
  {
    title: '角色',
    key: 'roles',
    width: 80,
    render: (row) => {
      const roleMap: Record<string, string> = {
        admin: '管理员',
        系统管理员: '管理员',
        租户管理员: '管理员',
        teacher: '教师',
        student: '学生'
      }
      if (row.roles && row.roles.length > 0) {
        return row.roles.map(r => roleMap[r] || r).join(', ')
      }
      return row.role ? (roleMap[row.role] || row.role) : '-'
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row) => h(
      NTag,
      { type: row.is_active ? 'success' : 'default', size: 'small' },
      { default: () => (row.is_active ? '启用' : '禁用') }
    )
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render: (row) => h(NSpace, {}, {
      default: () => [
        h(NButton, {
          size: 'small',
          onClick: () => handleViewDetail(row)
        }, { default: () => '详情' }),
        h(NButton, {
          size: 'small',
          onClick: () => handleEdit(row)
        }, { default: () => '编辑' }),
        h(NButton, {
          size: 'small',
          type: 'error',
          onClick: () => handleDelete(row)
        }, { default: () => '删除' })
      ]
    })
  }
]

// ========== 预览表格列定义 ==========
const previewColumns = [
  { title: '行号', key: 'row_number', width: 60 },
  { title: '账号', key: 'account', width: 100 },
  { title: '姓名', key: 'name', width: 80 },
  { title: '部门', key: 'department', width: 100 },
  { title: '岗位', key: 'post', width: 100 },
  { title: '角色', key: 'role', width: 80 },
  {
    title: '状态',
    key: 'is_valid',
    width: 80,
    render: (row: ImportPreviewRow) => h(
      NTag,
      { type: row.is_valid ? 'success' : 'error', size: 'small' },
      { default: () => (row.is_valid ? '有效' : '无效') }
    )
  },
  {
    title: '错误信息',
    key: 'errors',
    render: (row: ImportPreviewRow) => row.errors?.join('; ') || '-'
  },
  {
    title: '导入',
    key: 'import',
    width: 60,
    render: (row: ImportPreviewRow) => {
      if (!row.is_valid) return '-'
      return h('input', {
        type: 'checkbox',
        checked: selectedImportRows.value.includes(row.row_number),
        onChange: (e: Event) => {
          const checked = (e.target as HTMLInputElement).checked
          if (checked) {
            selectedImportRows.value.push(row.row_number)
          } else {
            const idx = selectedImportRows.value.indexOf(row.row_number)
            if (idx > -1) selectedImportRows.value.splice(idx, 1)
          }
        }
      })
    }
  }
]

// ========== 数据加载 ==========
const loadUsers = async () => {
  loading.value = true
  try {
    const params: UserListQuery = {
      page: pagination.page,
      size: pagination.pageSize
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.department_id) params.department_id = filters.department_id
    if (filters.post_id) params.post_id = filters.post_id

    const res = await getUsers(params)
    tableData.value = res.data.items
    pagination.itemCount = res.data.total
  } catch (error) {
    console.error('加载用户列表失败:', error)
    message.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const loadManageableScope = async () => {
  try {
    const res = await getManageableScope()
    departments.value = res.data.departments
  } catch (error) {
    console.error('加载可管理范围失败:', error)
  }
}

// ========== 筛选与分页 ==========
const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleReset = () => {
  filters.keyword = ''
  filters.department_id = null
  filters.post_id = null
  handleSearch()
}

const handleDepartmentChange = () => {
  filters.post_id = null
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadUsers()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadUsers()
}

const rowKey = (row: UserListItem) => row.id

// ========== 用户详情 ==========
const handleViewDetail = (row: UserListItem) => {
  detailUser.value = row
  showDetailDrawer.value = true
}

const formatRole = (roles: string[] | undefined) => {
  if (!roles || roles.length === 0) return '-'
  const roleMap: Record<string, string> = {
    admin: '管理员',
    系统管理员: '管理员',
    租户管理员: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return roles.map(r => roleMap[r] || r).join(', ')
}

// ========== 用户编辑 ==========
const handleEdit = (row: UserListItem) => {
  editingUser.value = row
  userForm.account = row.account
  userForm.name = row.name
  userForm.email = row.email
  userForm.phone = row.phone
  userForm.department_id = row.department_id
  userForm.post_id = row.post_id
  userForm.role = row.role
  userForm.is_active = row.is_active
  showAddUserModal.value = true
}

const handleFormDepartmentChange = () => {
  userForm.post_id = null
}

const handleCancelEdit = () => {
  showAddUserModal.value = false
  editingUser.value = null
  resetUserForm()
}

const resetUserForm = () => {
  userForm.account = ''
  userForm.name = ''
  userForm.email = null
  userForm.phone = null
  userForm.department_id = null
  userForm.post_id = null
  userForm.role = 'student'
  userForm.is_active = true
}

const handleSaveUser = async () => {
  try {
    await userFormRef.value?.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      await updateUser(editingUser.value.id, {
        name: userForm.name,
        email: userForm.email,
        phone: userForm.phone,
        department_id: userForm.department_id,
        post_id: userForm.post_id,
        role: userForm.role,
        is_active: userForm.is_active
      })
      message.success('更新成功')
    }

    showAddUserModal.value = false
    editingUser.value = null
    resetUserForm()
    loadUsers()
  } catch (error) {
    console.error('保存用户失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// ========== 用户删除 ==========
const handleDelete = (row: UserListItem) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除用户"${row.name}"（${row.account}）吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deleteUser(row.id)
        message.success('删除成功')
        loadUsers()
      } catch (error) {
        console.error('删除用户失败:', error)
        message.error('删除失败')
      }
    }
  })
}

// ========== 批量导入 ==========
const beforeUpload = (data: { file: UploadFileInfo }) => {
  const file = data.file.file
  if (!file) return false

  const isExcel =
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'application/vnd.ms-excel' ||
    file.name.endsWith('.xlsx') ||
    file.name.endsWith('.xls')

  if (!isExcel) {
    message.error('只能上传Excel文件')
    return false
  }
  return true
}

const handleFileChange = (data: { file: UploadFileInfo }) => {
  if (data.file.file) {
    selectedFile.value = data.file.file
  }
}

const handlePreview = async () => {
  if (!selectedFile.value) {
    message.error('请先选择文件')
    return
  }

  previewing.value = true
  try {
    const res = await previewImportUsers(selectedFile.value)
    previewData.value = res.data
    selectedImportRows.value = res.data.rows
      .filter(r => r.is_valid)
      .map(r => r.row_number)
    importStep.value = 'preview'
  } catch (error) {
    console.error('预览失败:', error)
    message.error('预览失败')
  } finally {
    previewing.value = false
  }
}

const handleCancelImport = () => {
  showImportModal.value = false
  importStep.value = 'upload'
  fileList.value = []
  selectedFile.value = null
  previewData.value = null
  selectedImportRows.value = []
}

const handleConfirmImport = async () => {
  if (!previewData.value || selectedImportRows.value.length === 0) {
    message.error('请选择要导入的记录')
    return
  }

  confirming.value = true
  try {
    await confirmImportUsers({
      preview_key: previewData.value.preview_key,
      user_ids: selectedImportRows.value.map(String)
    })
    message.success(`成功导入 ${selectedImportRows.value.length} 条记录`)
    handleCancelImport()
    loadUsers()
  } catch (error) {
    console.error('确认导入失败:', error)
    message.error('导入失败')
  } finally {
    confirming.value = false
  }
}

const getPreviewRowClassName = (row: ImportPreviewRow) => {
  return row.is_valid ? 'valid-row' : 'invalid-row'
}

// ========== 下载模板 ==========
const downloadTemplate = async () => {
  downloading.value = true
  try {
    const blob = await downloadImportTemplate()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '批量用户导入模板.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
    message.success('模板下载成功')
  } catch (error) {
    console.error('下载模板失败:', error)
    message.error('模板下载失败')
  } finally {
    downloading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  loadUsers()
  loadManageableScope()
})
</script>

<style scoped lang="scss">
.user-management-container {
  padding: 24px;
}

.page-header-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 4px 12px rgba(0, 0, 0, 0.03);
  border: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.02em;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-card,
.table-card {
  margin-top: 16px;
}

:deep(.valid-row) {
  background-color: #f6ffed;
}

:deep(.invalid-row) {
  background-color: #fff2f0;
}
</style>
