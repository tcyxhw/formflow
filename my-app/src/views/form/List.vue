<template>
    <div class="form-list-page">
      <!-- 页面头部 -->
      <n-page-header>
        <template #title>表单管理</template>
        <template #extra>
          <n-space>
            <n-button @click="showTemplateModal = true">
              <template #icon>
                <n-icon><Icon icon="carbon:document-add" /></n-icon>
              </template>
              从模板创建
            </n-button>
            <n-button type="primary" @click="handleCreate">
              <template #icon>
                <n-icon><Icon icon="carbon:add" /></n-icon>
              </template>
              创建表单
            </n-button>
          </n-space>
        </template>
      </n-page-header>
      
      <!-- 筛选栏 -->
      <n-card class="filter-card">
        <n-space>
          <n-input
            v-model:value="filters.keyword"
            placeholder="搜索表单名称"
            clearable
            style="width: 240px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <Icon icon="carbon:search" />
            </template>
          </n-input>
          
          <n-select
            v-model:value="filters.category"
            placeholder="分类"
            clearable
            style="width: 150px"
            :options="categoryOptions"
            @update:value="handleSearch"
          />
          
          <n-select
            v-model:value="filters.status"
            placeholder="状态"
            clearable
            style="width: 150px"
            :options="statusOptions"
            @update:value="handleSearch"
          />
          
          <n-button @click="handleSearch">
            <template #icon>
              <Icon icon="carbon:filter" />
            </template>
            筛选
          </n-button>
          
          <n-button @click="handleReset">
            <template #icon>
              <Icon icon="carbon:reset" />
            </template>
            重置
          </n-button>
        </n-space>
      </n-card>
      
      <!-- 表单列表 -->
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
      
      <FormPermissionDrawer
        v-model:show="showPermissionDrawer"
        :form-id="currentForm?.id ?? null"
        :form-name="currentForm?.name"
      />
      
      <!-- 模板选择弹窗 -->
      <n-modal
        v-model:show="showTemplateModal"
        preset="card"
        title="选择表单模板"
        style="width: 800px"
      >
        <n-spin :show="loadingTemplates">
          <div class="template-grid">
            <div
              v-for="template in templates"
              :key="template.id"
              class="template-card"
              @click="handleSelectTemplate(template)"
            >
              <div class="template-icon">
                <Icon icon="carbon:document" />
              </div>
              <div class="template-info">
                <div class="template-name">{{ template.name }}</div>
                <div class="template-desc">{{ template.description }}</div>
              </div>
            </div>
          </div>
        </n-spin>
      </n-modal>
      
      <!-- 从模板创建弹窗 -->
      <n-modal
        v-model:show="showCreateFromTemplate"
        preset="dialog"
        title="创建表单"
        positive-text="创建"
        negative-text="取消"
        @positive-click="handleConfirmCreateFromTemplate"
      >
        <n-form ref="createFormRef" :model="createFormData">
          <n-form-item
            label="表单名称"
            path="name"
            :rule="{ required: true, message: '请输入表单名称', trigger: 'blur' }"
          >
            <n-input
              v-model:value="createFormData.name"
              placeholder="请输入表单名称"
            />
          </n-form-item>
        </n-form>
      </n-modal>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, onMounted, h, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import { useMessage, useDialog } from 'naive-ui'
  import type { DataTableColumns } from 'naive-ui'
  import { NSpace, NButton, NTag } from 'naive-ui'
  import { Icon } from '@iconify/vue'
  import * as formApi from '@/api/form'
  import FormPermissionDrawer from '@/components/form/FormPermissionDrawer.vue'
  import type {
    FormResponse,
    FormListQuery,
    FormTemplateSummary,
    FormListResponse
  } from '@/types/form'
  import { FormStatus } from '@/types/form'

  const router = useRouter()
  const message = useMessage()
  const dialog = useDialog()

  const loading = ref(false)
  const loadingTemplates = ref(false)
  const showTemplateModal = ref(false)
  const showCreateFromTemplate = ref(false)
  const showPermissionDrawer = ref(false)
  const currentForm = ref<FormResponse | null>(null)

  interface FilterState {
    keyword: string
    category: string | null
    status: FormStatus | null
  }

  const filters = reactive<FilterState>({
    keyword: '',
    category: null,
    status: null,
  })

  interface PaginationState {
    page: number
    pageSize: number
    itemCount: number
    showSizePicker: boolean
    pageSizes: number[]
  }

  const pagination = reactive<PaginationState>({
    page: 1,
    pageSize: 20,
    itemCount: 0,
    showSizePicker: true,
    pageSizes: [10, 20, 50, 100],
  })

  const tableData = ref<FormResponse[]>([])
  const templates = ref<FormTemplateSummary[]>([])
  const selectedTemplate = ref<FormTemplateSummary | null>(null)
  const createFormData = reactive({
    name: '',
  })

  const pendingQuery = computed<FormListQuery>(() => ({
    page: pagination.page,
    page_size: pagination.pageSize,
    keyword: filters.keyword || undefined,
    category: filters.category || undefined,
    status: filters.status || undefined,
  }))

  const resolveErrorMessage = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback

  // 分类选项
  const categoryOptions = [
    { label: '请假申请', value: 'leave' },
    { label: '活动报名', value: 'activity' },
    { label: '问卷调查', value: 'survey' },
    { label: '其他', value: 'other' },
  ]

  // 状态选项
  const statusOptions = [
    { label: '草稿', value: FormStatus.DRAFT },
    { label: '已发布', value: FormStatus.PUBLISHED },
    { label: '已归档', value: FormStatus.ARCHIVED },
  ]

  type TagType = 'default' | 'info' | 'success' | 'warning' | 'error'
  const statusTagMap: Record<FormStatus, { text: string; type: TagType }> = {
    [FormStatus.DRAFT]: { text: '草稿', type: 'default' },
    [FormStatus.PUBLISHED]: { text: '已发布', type: 'success' },
    [FormStatus.ARCHIVED]: { text: '已归档', type: 'warning' }
  }

  const toFormStatus = (value: string | null | undefined): FormStatus => {
    if (value === FormStatus.PUBLISHED || value === FormStatus.ARCHIVED || value === FormStatus.DRAFT) {
      return value
    }
    return FormStatus.DRAFT
  }

  // 表格列定义
  const columns: DataTableColumns<FormResponse> = [
    {
      title: '表单名称',
      key: 'name',
      ellipsis: { tooltip: true },
    },
    {
      title: '分类',
      key: 'category',
      width: 100,
      render: (row) => row.category || '-',
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (row) => {
        const statusKey = toFormStatus(row.status as string)
        const status = statusTagMap[statusKey] || statusTagMap[FormStatus.DRAFT]
        return h(
          NTag,
          { type: status.type, size: 'small' },
          { default: () => status.text }
        )
      },
    },
    {
      title: '版本',
      key: 'current_version',
      width: 80,
      render: (row) => row.current_version || '0',
    },
    {
      title: '提交数',
      key: 'total_submissions',
      width: 100,
      render: (row) => row.total_submissions || 0,
    },
    {
      title: '创建时间',
      key: 'created_at',
      width: 180,
      render: (row) => new Date(row.created_at).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 240,
      fixed: 'right',
      render: (row) => {
        return h(
          NSpace,
          {},
          {
            default: () => [
              h(
                NButton,
                {
                  size: 'small',
                  onClick: () => handleEdit(row),
                },
                { default: () => '编辑' }
              ),
              h(
                NButton,
                {
                  size: 'small',
                  onClick: () => handleClone(row),
                },
                { default: () => '克隆' }
              ),
              h(
                NButton,
                {
                  size: 'small',
                  type: 'warning',
                  tertiary: true,
                  onClick: () => handleManagePermission(row),
                },
                { default: () => '权限' }
              ),
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  disabled: row.status !== FormStatus.DRAFT,
                  onClick: () => handleDelete(row),
                },
                { default: () => '删除' }
              ),
            ],
          }
        )
      },
    },
  ]

  // 加载列表
  const loadList = async () => {
    try {
      loading.value = true
      const res = await formApi.listForms(pendingQuery.value)
      const list: FormListResponse = res.data
      tableData.value = list.items
      pagination.itemCount = list.total
    } catch (error) {
      message.error(resolveErrorMessage(error, '加载失败'))
    } finally {
      loading.value = false
    }
  }

  // 加载模板
  const loadTemplates = async () => {
    try {
      loadingTemplates.value = true
      const res = await formApi.listTemplates()
      templates.value = res.data
    } catch (error) {
      message.error(resolveErrorMessage(error, '加载模板失败'))
    } finally {
      loadingTemplates.value = false
    }
  }

  // 创建表单
  const handleCreate = () => {
    router.push('/form/designer')
  }

  // 编辑表单
  const handleEdit = (row: FormResponse) => {
    router.push({
      path: '/form/designer',
      query: { id: row.id },
    })
  }

  // 克隆表单
  const handleClone = (row: FormResponse) => {
    const cloneName = ref(`${row.name} (副本)`)

    dialog.create({
      title: '克隆表单',
      positiveText: '确定',
      negativeText: '取消',
      showIcon: false,
      content: () => {
        return h('div', [
          h('p', { style: { marginBottom: '12px' } }, '请输入新表单的名称：'),
          h('n-input', {
            value: cloneName.value,
            'onUpdate:value': (val: string) => {
              cloneName.value = val
            },
            placeholder: '请输入表单名称',
          })
        ])
      },
      onPositiveClick: async () => {
        try {
          await formApi.cloneForm(row.id, cloneName.value)
          message.success('克隆成功')
          loadList()
        } catch (error) {
          message.error(resolveErrorMessage(error, '克隆失败'))
        }
      },
    })
  }

  // 删除表单
  const handleDelete = (row: FormResponse) => {
    dialog.warning({
      title: '确认删除',
      content: `确定要删除表单「${row.name}」吗？`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await formApi.deleteForm(row.id)
          message.success('删除成功')
          loadList()
        } catch (error) {
          message.error(resolveErrorMessage(error, '删除失败'))
        }
      },
    })
  }

  // 选择模板
  const handleSelectTemplate = (template: FormTemplateSummary) => {
    selectedTemplate.value = template
    createFormData.name = template.name
    showTemplateModal.value = false
    showCreateFromTemplate.value = true
  }

  // 确认从模板创建
  const handleConfirmCreateFromTemplate = async () => {
    if (!createFormData.name) {
      message.error('请输入表单名称')
      return false
    }
    if (!selectedTemplate.value) {
      message.error('请先选择模板')
      return false
    }

    try {
      const res = await formApi.createFromTemplate(
        selectedTemplate.value.id,
        createFormData.name
      )
      message.success('创建成功')
      router.push({
        path: '/form/designer',
        query: { id: res.data.id },
      })
    } catch (error) {
      message.error(resolveErrorMessage(error, '创建失败'))
      return false
    }
  }

  // 搜索
  const handleSearch = () => {
    pagination.page = 1
    loadList()
  }

  // 重置
  const handleReset = () => {
    filters.keyword = ''
    filters.category = null
    filters.status = null
    handleSearch()
  }

  // 分页
  const handlePageChange = (page: number) => {
    pagination.page = page
    loadList()
  }

  const handlePageSizeChange = (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    loadList()
  }

  const rowKey = (row: FormResponse) => row.id

  onMounted(() => {
    loadList()
    loadTemplates()
  })
  </script>
  
  <style scoped lang="scss">
  .form-list-page {
    padding: 24px;
  }
  
  .filter-card,
  .table-card {
    margin-top: 16px;
  }
  
  .template-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    max-height: 500px;
    overflow-y: auto;
  }
  
  .template-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      border-color: #18a058;
      background: #f0fdf4;
    }
    
    .template-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      background: #f0fdf4;
      border-radius: 8px;
      font-size: 24px;
      color: #18a058;
    }
    
    .template-info {
      flex: 1;
      
      .template-name {
        font-size: 15px;
        font-weight: 500;
        color: #1f2937;
        margin-bottom: 4px;
      }
      
      .template-desc {
        font-size: 13px;
        color: #6b7280;
      }
    }
  }
  </style>