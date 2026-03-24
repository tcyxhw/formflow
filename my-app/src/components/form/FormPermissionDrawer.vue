<template>
  <n-drawer v-model:show="innerVisible" :width="520" placement="right" :trap-focus="false">
    <n-drawer-content :title="drawerTitle" closable>
      <div v-if="!formId" class="empty-wrapper">
        <n-result status="warning" title="尚未保存表单" description="请先保存表单后再配置权限" />
      </div>
      <div v-else>
        <n-alert type="info" show-icon>
          权限将决定谁可以查看、填写或管理当前表单，请及时维护授权列表。
        </n-alert>

        <div class="permission-overview">
          <div class="overview-header">
            <n-text depth="3">我的权限</n-text>
            <n-tag v-if="overview?.is_owner" type="success" :bordered="false" size="small">
              表单拥有者
            </n-tag>
          </div>
          <n-spin :show="overviewLoading">
            <n-result
              v-if="overviewError"
              status="error"
              title="权限概览加载失败"
              :description="overviewError"
            >
              <template #footer>
                <n-button size="small" @click="loadOverview">重试</n-button>
              </template>
            </n-result>
            <n-empty v-else-if="!permissionChips.length" description="暂无授予权限" size="small" />
            <n-space v-else wrap>
              <n-tag
                v-for="item in permissionChips"
                :key="item.value"
                size="small"
                :type="item.type"
                :bordered="false"
              >
                {{ item.label }}
              </n-tag>
            </n-space>
          </n-spin>
        </div>

        <n-space justify="space-between" align="center" style="margin: 16px 0">
          <n-text depth="3">
            共 {{ permissions.length }} 条记录
          </n-text>
          <n-button type="primary" size="small" @click="openCreateModal">
            <template #icon>
              <Icon icon="carbon:add" />
            </template>
            新增授权
          </n-button>
        </n-space>

        <n-spin :show="loading">
          <n-result v-if="errorMessage" status="error" title="加载失败" :description="errorMessage">
            <template #footer>
              <n-button size="small" @click="loadPermissions">重试</n-button>
            </template>
          </n-result>

          <n-data-table
            v-else
            :columns="columns"
            :data="permissions"
            :bordered="false"
            :row-key="(row: FormPermission) => row.id"
            :empty="emptyPlaceholder"
          />
        </n-spin>
      </div>
    </n-drawer-content>
  </n-drawer>

  <!-- 新增授权弹窗 -->
  <n-modal v-model:show="showCreateModal" preset="dialog" title="新增权限" positive-text="保存" negative-text="取消"
           :positive-button-props="{ disabled: creating }" @positive-click="handleCreate">
    <n-form ref="createFormRef" :model="createForm" label-width="80" :rules="formRules">
      <n-form-item label="授权类型" path="grantType">
        <n-select v-model:value="createForm.grantType" :options="grantTypeOptions" />
      </n-form-item>
      
      <!-- 动态选择器：根据授权类型显示不同的选择器 -->
      <n-form-item v-if="createForm.grantType === 'user'" label="选择用户" path="granteeId">
        <n-select
          v-model:value="createForm.granteeId"
          :options="userOptions"
          :loading="loadingUsers"
          filterable
          remote
          clearable
          placeholder="搜索并选择用户"
          @search="handleSearchUsers"
        />
      </n-form-item>

      <n-form-item v-else-if="createForm.grantType === 'role'" label="选择角色" path="granteeId">
        <n-select
          v-model:value="createForm.granteeId"
          :options="roleOptions"
          :loading="loadingRoles"
          filterable
          clearable
          placeholder="选择角色"
        />
      </n-form-item>

      <n-form-item v-else-if="createForm.grantType === 'department'" label="选择部门" path="granteeId">
        <n-select
          v-model:value="createForm.granteeId"
          :options="departmentOptions"
          :loading="loadingDepartments"
          filterable
          clearable
          placeholder="选择部门"
        />
      </n-form-item>

      <n-form-item v-else-if="createForm.grantType === 'position'" label="选择岗位" path="granteeId">
        <n-select
          v-model:value="createForm.granteeId"
          :options="positionOptions"
          :loading="loadingPositions"
          filterable
          clearable
          placeholder="选择岗位"
        />
      </n-form-item>
      <n-form-item label="权限" path="permission">
        <n-select v-model:value="createForm.permission" :options="permissionOptions" />
      </n-form-item>
      <n-form-item label="生效时间" path="validFrom">
        <n-date-picker v-model:value="createForm.validFrom" type="datetime" clearable style="width: 100%" />
      </n-form-item>
      <n-form-item label="失效时间" path="validTo">
        <n-date-picker v-model:value="createForm.validTo" type="datetime" clearable style="width: 100%" />
      </n-form-item>
    </n-form>
  </n-modal>

  <!-- 编辑有效期弹窗 -->
  <n-modal v-model:show="showEditModal" preset="dialog" title="调整有效期" positive-text="保存" negative-text="取消"
           :positive-button-props="{ disabled: updating }" @positive-click="handleUpdate">
    <n-form ref="editFormRef" :model="editForm" label-width="80" :rules="timeRules">
      <n-form-item label="生效时间" path="validFrom">
        <n-date-picker v-model:value="editForm.validFrom" type="datetime" clearable style="width: 100%" />
      </n-form-item>
      <n-form-item label="失效时间" path="validTo">
        <n-date-picker v-model:value="editForm.validTo" type="datetime" clearable style="width: 100%" />
      </n-form-item>
    </n-form>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, h, reactive, ref, watch } from 'vue'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { NButton, NEmpty, NPopconfirm, NSpace, NTag } from 'naive-ui'
import { Icon } from '@iconify/vue'
import {
  listFormPermissions,
  createFormPermission,
  updateFormPermission,
  deleteFormPermission,
  getMyFormPermissions
} from '@/api/formPermission'
import { listUsers } from '@/api/user'
import { listRoles, listDepartments, listPositions } from '@/api/admin'
import type {
  FormPermission,
  FormPermissionOverview,
  GrantType,
  PermissionType
} from '@/types/formPermission'

interface Props {
  formId?: number | null
  show: boolean
  formName?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'update:show', value: boolean): void }>()

const innerVisible = ref(false)

watch(
  () => props.show,
  (newVal) => {
    innerVisible.value = newVal
  }
)

watch(
  () => innerVisible.value,
  (newVal) => {
    if (newVal !== props.show) {
      emit('update:show', newVal)
    }
  }
)

const permissions = ref<FormPermission[]>([])
const loading = ref(false)
const errorMessage = ref<string | null>(null)
const overview = ref<FormPermissionOverview | null>(null)
const overviewLoading = ref(false)
const overviewError = ref<string | null>(null)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const creating = ref(false)
const updating = ref(false)
const activePermissionId = ref<number | null>(null)

// 动态选择器数据
const userOptions = ref<Array<{ label: string; value: number }>>([])
const roleOptions = ref<Array<{ label: string; value: number }>>([])
const departmentOptions = ref<Array<{ label: string; value: number }>>([])
const positionOptions = ref<Array<{ label: string; value: number }>>([])

// 加载状态
const loadingUsers = ref(false)
const loadingRoles = ref(false)
const loadingDepartments = ref(false)
const loadingPositions = ref(false)

const createForm = reactive({
  grantType: 'user' as GrantType,
  granteeId: null as number | null,
  permission: 'view' as PermissionType,
  validFrom: null as number | null,
  validTo: null as number | null
})

const editForm = reactive({
  validFrom: null as number | null,
  validTo: null as number | null
})

const grantTypeOptions = [
  { label: '用户', value: 'user' },
  { label: '角色', value: 'role' },
  { label: '部门', value: 'department' },
  { label: '岗位', value: 'position' }
]

const permissionOptions = [
  { label: '查看', value: 'view' },
  { label: '填写', value: 'fill' },
  { label: '编辑', value: 'edit' },
  { label: '导出', value: 'export' },
  { label: '管理', value: 'manage' }
]

const createFormRef = ref<FormInst | null>(null)
const editFormRef = ref<FormInst | null>(null)

const formRules: FormRules = {
  grantType: [{ required: true, message: '请选择授权类型', trigger: 'change' }],
  granteeId: [{ 
    required: true, 
    type: 'number',
    message: '请选择授权对象', 
    trigger: ['blur', 'change'] 
  }],
  permission: [{ required: true, message: '请选择权限', trigger: 'change' }],
  validTo: [{
    validator: () => {
      if (createForm.validFrom && createForm.validTo && createForm.validTo < createForm.validFrom) {
        return new Error('失效时间不能早于生效时间')
      }
      return true
    },
    trigger: 'change'
  }]
}

const timeRules: FormRules = {
  validTo: [{
    validator: () => {
      if (editForm.validFrom && editForm.validTo && editForm.validTo < editForm.validFrom) {
        return new Error('失效时间不能早于生效时间')
      }
      return true
    },
    trigger: 'change'
  }]
}

const columns: DataTableColumns<FormPermission> = [
  { title: '授权类型', key: 'grant_type', render: row => renderTag(row.grant_type) },
  { title: '授权对象', key: 'grantee_name', render: row => row.grantee_name || `ID: ${row.grantee_id}` },
  { title: '权限', key: 'permission', render: row => renderPermission(row.permission) },
  {
    title: '生效时间',
    key: 'valid_from',
    render: row => row.valid_from ? new Date(row.valid_from).toLocaleString() : '—'
  },
  {
    title: '失效时间',
    key: 'valid_to',
    render: row => {
      if (!row.valid_from && !row.valid_to) {
        return h(NTag, { size: 'small', bordered: false, type: 'success' }, { default: () => '永久有效' })
      }
      return row.valid_to ? new Date(row.valid_to).toLocaleString() : '永久有效'
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    render: row => h(NSpace, {}, {
      default: () => [
        h(
          NButton,
          {
            size: 'small',
            tertiary: true,
            onClick: () => openEditModal(row)
          },
          { default: () => '调整有效期' }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id) },
          {
            default: () => '确认删除该授权？',
            trigger: () => h(
              NButton,
              { size: 'small', type: 'error', quaternary: true },
              { default: () => '删除' }
            )
          }
        )
      ]
    })
  }
]

const emptyPlaceholder = () => h(
  NEmpty,
  { description: '暂未配置权限' },
  {
    footer: () => h(
      NButton,
      { text: true, size: 'small', onClick: openCreateModal },
      { default: () => '立即新增' }
    )
  }
)

const drawerTitle = computed(() => props.formName ? `表单权限 · ${props.formName}` : '表单权限配置')

const mapTimestamp = (value: number | null) => (value ? new Date(value).toISOString() : null)

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback

const loadPermissions = async () => {
  if (!props.formId) {
    permissions.value = []
    return
  }
  try {
    loading.value = true
    errorMessage.value = null
    const res = await listFormPermissions(props.formId)
    permissions.value = res.data?.items || []
  } catch (error: any) {
    // 403 表示没有 MANAGE 权限，这是正常情况
    if (error?.response?.status === 403) {
      permissions.value = []
      errorMessage.value = null
    } else {
      errorMessage.value = resolveErrorMessage(error, '权限数据加载失败')
    }
  } finally {
    loading.value = false
  }
}

const loadOverview = async () => {
  if (!props.formId) {
    overview.value = null
    return
  }
  try {
    overviewLoading.value = true
    overviewError.value = null
    const res = await getMyFormPermissions(props.formId)
    overview.value = res.data || null
  } catch (error) {
    overviewError.value = resolveErrorMessage(error, '权限概览加载失败')
  } finally {
    overviewLoading.value = false
  }
}

type ChipType = 'warning' | 'success' | 'info'

const permissionChips = computed((): Array<{ value: PermissionType; label: string; type: ChipType }> => {
  if (!overview.value) {
    return []
  }
  
  // 根据后端返回的权限字段构建权限列表
  const permissions: PermissionType[] = []
  if (overview.value.can_manage) permissions.push('manage')
  if (overview.value.can_edit) permissions.push('edit')
  if (overview.value.can_export) permissions.push('export')
  if (overview.value.can_fill) permissions.push('fill')
  if (overview.value.can_view) permissions.push('view')
  
  return permissions.map((perm) => ({
    value: perm,
    label: permissionOptions.find((item) => item.value === perm)?.label ?? perm,
    type: (perm === 'manage' ? 'warning' : perm === 'edit' ? 'error' : perm === 'export' ? 'info' : perm === 'fill' ? 'success' : 'default') as ChipType
  }))
})

const refreshPermissionData = async () => {
  await Promise.all([loadPermissions(), loadOverview()])
}

const openCreateModal = () => {
  if (!props.formId) {
    console.warn('请先保存表单')
    return
  }
  createForm.grantType = 'user'
  createForm.granteeId = null
  createForm.permission = 'view'
  createForm.validFrom = null
  createForm.validTo = null
  showCreateModal.value = true
}

const handleCreate = async () => {
  if (!props.formId) {
    console.warn('请先保存表单')
    return false
  }
  try {
    await createFormRef.value?.validate()
    creating.value = true
    await createFormPermission(props.formId, {
      grant_type: createForm.grantType,
      grantee_id: createForm.granteeId as number,
      permission: createForm.permission,
      valid_from: mapTimestamp(createForm.validFrom),
      valid_to: mapTimestamp(createForm.validTo)
    })
    console.log('新增成功')
    showCreateModal.value = false
    await loadPermissions()
    return true
  } catch (error) {
    console.error('新增失败', error)
    return false
  } finally {
    creating.value = false
  }
}

const openEditModal = (row: FormPermission) => {
  activePermissionId.value = row.id
  editForm.validFrom = row.valid_from ? Date.parse(row.valid_from) : null
  editForm.validTo = row.valid_to ? Date.parse(row.valid_to) : null
  showEditModal.value = true
}

const handleUpdate = async () => {
  if (!props.formId || !activePermissionId.value) {
    return false
  }
  try {
    await editFormRef.value?.validate()
    updating.value = true
    await updateFormPermission(props.formId, activePermissionId.value, {
      valid_from: mapTimestamp(editForm.validFrom),
      valid_to: mapTimestamp(editForm.validTo)
    })
    console.log('更新成功')
    showEditModal.value = false
    await loadPermissions()
    return true
  } catch (error) {
    console.error('更新失败', error)
    return false
  } finally {
    updating.value = false
  }
}

const handleDelete = async (permissionId: number) => {
  if (!props.formId) return
  try {
    await deleteFormPermission(props.formId, permissionId)
    console.log('已删除')
    await loadPermissions()
  } catch (error) {
    console.error('删除失败', error)
  }
}

const renderTag = (value: string) => {
  const label = grantTypeOptions.find(item => item.value === value)?.label || value
  return h(
    NTag,
    { size: 'small', bordered: false },
    { default: () => label }
  )
}

const renderPermission = (value: string) => {
  const label = permissionOptions.find(item => item.value === value)?.label || value
  return h(
    NTag,
    { size: 'small', bordered: false, type: value === 'manage' ? 'warning' : 'success' },
    { default: () => label }
  )
}

watch(
  () => props.show,
  value => {
    if (value) {
      refreshPermissionData()
    }
  },
  { immediate: false }
)

watch(
  () => props.formId,
  value => {
    if (value && props.show) {
      refreshPermissionData()
    }
  }
)

defineExpose({ loadPermissions, loadOverview })

// 加载数据的方法
const loadUsers = async (keyword?: string) => {
  loadingUsers.value = true
  try {
    const res = await listUsers({ keyword, page: 1, size: 50 })
    userOptions.value = res.data.items.map((user) => ({
      label: `${user.name} (${user.account})`,
      value: user.id
    }))
  } catch (error) {
    console.error('加载用户列表失败', error)
  } finally {
    loadingUsers.value = false
  }
}

const loadRoles = async () => {
  loadingRoles.value = true
  try {
    const res = await listRoles({ page: 1, size: 100 })
    roleOptions.value = res.data.items.map((role) => ({
      label: role.name,
      value: role.id
    }))
  } catch (error) {
    console.error('加载角色列表失败', error)
  } finally {
    loadingRoles.value = false
  }
}

const loadDepartments = async () => {
  loadingDepartments.value = true
  try {
    const res = await listDepartments({ page: 1, size: 100 })
    departmentOptions.value = res.data.items.map((dept) => ({
      label: dept.name,
      value: dept.id
    }))
  } catch (error) {
    console.error('加载部门列表失败', error)
  } finally {
    loadingDepartments.value = false
  }
}

const loadPositions = async () => {
  loadingPositions.value = true
  try {
    const res = await listPositions({ page: 1, size: 100 })
    positionOptions.value = res.data.items.map((pos) => ({
      label: pos.name,
      value: pos.id
    }))
  } catch (error) {
    console.error('加载岗位列表失败', error)
  } finally {
    loadingPositions.value = false
  }
}

// 搜索用户（远程搜索）
const handleSearchUsers = (query: string) => {
  if (query) {
    loadUsers(query)
  }
}

// 监听 grantType 变化，自动加载对应数据并清空选择
watch(
  () => createForm.grantType,
  (newType, oldType) => {
    if (!newType) return
    
    // 当授权类型改变时，清空之前选择的对象ID
    if (oldType && newType !== oldType) {
      createForm.granteeId = null
      // 清除表单验证错误
      createFormRef.value?.restoreValidation()
    }
    
    switch (newType) {
      case 'user':
        if (userOptions.value.length === 0) {
          loadUsers()
        }
        break
      case 'role':
        if (roleOptions.value.length === 0) {
          loadRoles()
        }
        break
      case 'department':
        if (departmentOptions.value.length === 0) {
          loadDepartments()
        }
        break
      case 'position':
        if (positionOptions.value.length === 0) {
          loadPositions()
        }
        break
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.permission-overview {
  margin: 16px 0;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.overview-header {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.empty-wrapper {
  padding: 24px 0;
}
</style>
