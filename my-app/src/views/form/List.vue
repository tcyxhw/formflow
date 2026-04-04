  <template>
    <div class="form-list-page">
      <!-- 页面头部区域 -->
      <div class="page-header-section">
        <div class="header-left">
          <h1 class="page-title">表单管理</h1>
          <div class="action-buttons">
            <n-button class="action-btn" @click="goHome">
              <template #icon>
                <n-icon><Icon icon="carbon:home" /></n-icon>
              </template>
              返回主页
            </n-button>
            <n-button class="action-btn" @click="showTemplateModal = true">
              <template #icon>
                <n-icon><Icon icon="carbon:document-add" /></n-icon>
              </template>
              从模板创建
            </n-button>
            <n-button class="action-btn primary-action" type="primary" @click="handleCreate">
              <template #icon>
                <n-icon><Icon icon="carbon:add" /></n-icon>
              </template>
              创建表单
            </n-button>
          </div>
        </div>
      </div>
      
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

      <!-- 级联删除确认弹窗 -->
      <CascadeDeleteConfirmDialog
        v-model:visible="showCascadeDialog"
        :form-id="cascadeDialogData?.form_id || 0"
        :form-name="cascadeDialogData?.form_name || ''"
        :flow-definition-count="cascadeDialogData?.flow_definition_count || 0"
        :flow-definitions="cascadeDialogData?.flow_definitions || []"
        :loading="deleteLoading"
        @confirm="handleCascadeConfirm"
        @cancel="handleCascadeCancel"
      />

      <!-- 表单详情弹窗 -->
      <n-modal
        v-model:show="showDetailModal"
        preset="card"
        :title="detailFormName + ' - 表单详情'"
        class="form-detail-modal"
        style="width: 1100px; max-height: 85vh;"
        :mask-closable="true"
      >
        <n-spin :show="detailLoading">
          <n-tabs type="line" animated class="detail-tabs">
            <!-- 表单字段 -->
            <n-tab-pane name="fields" tab="表单字段">
              <div class="fields-container">
                <n-empty v-if="!detailFields.length" description="暂无字段配置" />
                <div v-else class="field-grid">
                  <div
                    v-for="(field, index) in detailFields"
                    :key="field.id"
                    class="field-card"
                    :class="{ 'is-required': field.required }"
                    :style="{ animationDelay: `${index * 50}ms` }"
                  >
                    <div class="field-card-glow" :class="getFieldGlowClass(field.type)"></div>
                    <div class="field-index-badge">{{ String(index + 1) }}</div>
                    <div class="field-card-content">
                      <div class="field-header">
                        <div class="field-icon-wrapper" :class="getFieldIconClass(field.type)">
                          <span class="field-type-icon">{{ getFieldTypeIcon(field.type) }}</span>
                        </div>
                        <div class="field-badges">
                          <n-tag v-if="field.required" type="error" size="tiny" class="required-badge">
                            <template #icon>
                              <span>*</span>
                            </template>
                            必填
                          </n-tag>
                          <n-tag
                            v-if="field.unique"
                            type="warning"
                            size="tiny"
                            class="unique-badge"
                          >
                            <template #icon>
                              <span>🔐</span>
                            </template>
                            唯一
                          </n-tag>
                        </div>
                      </div>

                      <div class="field-body">
                        <h4 class="field-title">{{ field.label || field.name }}</h4>
                        <p v-if="field.description" class="field-description">
                          <Icon icon="carbon:information" class="desc-icon" />
                          {{ field.description }}
                        </p>
                        <p v-else-if="field.placeholder" class="field-placeholder">
                          <Icon icon="carbon:help" class="placeholder-icon" />
                          {{ field.placeholder }}
                        </p>
                      </div>

                      <div class="field-footer">
                        <span class="field-type-label" :class="getFieldTypeClass(field.type)">
                          {{ getFieldTypeLabel(field.type) }}
                        </span>
                        <div v-if="field.validation" class="field-validation">
                          <Icon icon="carbon:checkmark-outline" class="validation-icon" />
                          已配置验证
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </n-tab-pane>

            <!-- 审批流程 -->
            <n-tab-pane name="flow" tab="审批流程">
              <div class="flow-container">
                <n-empty v-if="!flowNodes.length" description="暂未配置审批流程" />
                <div v-else class="flow-diagram-wrapper">
                  <div class="flow-diagram">
                    <FlowDiagram :nodes="flowNodes" :routes="flowRoutes" :fieldLabels="fieldLabels" />
                  </div>
                </div>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-spin>
      </n-modal>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, onMounted, h, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import { useMessage, useDialog } from 'naive-ui'
  import type { DataTableColumns } from 'naive-ui'
  import { NSpace, NButton, NTag, NInput } from 'naive-ui'
  import { Icon } from '@iconify/vue'
  import * as formApi from '@/api/form'
  import * as flowApi from '@/api/flow'
  import type {
    FormResponse,
    FormListQuery,
    FormTemplateSummary,
    FormListResponse
  } from '@/types/form'
  import { FormStatus } from '@/types/form'
  import CascadeDeleteConfirmDialog from '@/components/form/CascadeDeleteConfirmDialog.vue'
  import FlowDiagram from '@/components/form/FlowDiagram.vue'

  const router = useRouter()
  const message = useMessage()
  const dialog = useDialog()

  const loading = ref(false)
  const loadingTemplates = ref(false)
  const showTemplateModal = ref(false)
  const showCreateFromTemplate = ref(false)
  const showCascadeDialog = ref(false)
  const cascadeDialogData = ref<any>(null)
  const deleteLoading = ref(false)

  // 表单详情弹窗
  const showDetailModal = ref(false)
  const detailLoading = ref(false)
  const detailFormName = ref('')
  const detailFields = ref<any[]>([])
  const flowNodes = ref<any[]>([])
  const flowRoutes = ref<any[]>([])
  const fieldLabels = ref<Record<string, string>>({})

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
      width: 220,
      render: (row) => {
        const publishedVer = row.current_version || 0
        const hasUnpublished = row.has_unpublished_changes
        const flowVer = row.flow_version
        const hasFlowChanges = row.has_flow_changes
        const hasFlow = !!row.flow_definition_id

        return h(NSpace, { vertical: true, size: 4 }, {
          default: () => [
            h(NSpace, { align: 'center', size: 6 }, {
              default: () => [
                h('span', { style: { fontSize: '12px', color: '#64748b' } }, '表单'),
                h('span', { style: { fontSize: '13px', fontWeight: 500 } }, `v${publishedVer}`),
                hasUnpublished
                  ? h(NTag, { type: 'warning', size: 'tiny', bordered: false }, { default: () => '有未发布' })
                  : null,
              ],
            }),
            hasFlow
              ? h(NSpace, { align: 'center', size: 6 }, {
                  default: () => [
                    h('span', { style: { fontSize: '12px', color: '#64748b' } }, '流程'),
                    h('span', { style: { fontSize: '13px', fontWeight: 500 } }, `v${flowVer ?? '-'}`),
                    hasFlowChanges
                      ? h(NTag, { type: 'warning', size: 'tiny', bordered: false }, { default: () => '有未发布' })
                      : null,
                  ],
                })
              : null,
          ],
        })
      },
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
      width: 400,
      fixed: 'right',
      render: (row) => {
        const isDraft = row.status === FormStatus.DRAFT
        const isPublished = row.status === FormStatus.PUBLISHED
        const hasUnpublished = row.has_unpublished_changes

        return h(
          NSpace,
          {},
          {
            default: () => [
              h(
                NButton,
                {
                  size: 'small',
                  type: 'primary',
                  ghost: true,
                  onClick: () => handleShowDetail(row),
                },
                { default: () => '详情' }
              ),
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
                  type: 'info',
                  onClick: () => handleConfigureFlow(row),
                },
                { default: () => '配置流程' }
              ),
              isDraft && h(
                NButton,
                {
                  size: 'small',
                  type: 'success',
                  onClick: () => handlePublish(row),
                },
                { default: () => '发布' }
              ),
              isPublished && hasUnpublished && h(
                NButton,
                {
                  size: 'small',
                  type: 'warning',
                  onClick: () => handleRepublish(row),
                },
                { default: () => '重新发布' }
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
                  type: 'error',
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
      console.log('[DEBUG] res structure:', JSON.stringify(res, (k, v) => k === 'data' ? '{...}' : v, 2))
      
      // Handle both wrapped and unwrapped response
      let items: FormResponse[] = []
      let total = 0
      
      if (res.data && typeof res.data === 'object') {
        if ('items' in res.data) {
          // Direct: res.data = { items: [], total: N }
          items = res.data.items || []
          total = res.data.total || 0
        } else if ('data' in res.data && res.data.data) {
          // Wrapped: res.data = { data: { items: [], total: N } }
          items = res.data.data.items || []
          total = res.data.data.total || 0
        }
      }
      
      console.log('[DEBUG] items:', items[0])
      tableData.value = items
      pagination.itemCount = total
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

  // 显示表单详情
  const handleShowDetail = async (row: FormResponse) => {
    showDetailModal.value = true
    detailLoading.value = true
    detailFormName.value = row.name
    detailFields.value = []
    flowNodes.value = []
    flowRoutes.value = []
    fieldLabels.value = {}

    try {
      // 获取表单详情（包含字段信息）
      const formDetail = await formApi.getFormDetail(row.id)
      if (formDetail.data?.schema_json?.fields) {
        detailFields.value = formDetail.data.schema_json.fields
        // 构建字段标签映射
        const labels: Record<string, string> = {}
        for (const field of detailFields.value) {
          if (field.id && field.label) {
            labels[field.id] = field.label
          }
        }
        fieldLabels.value = labels
      }

      // 如果有流程定义，获取流程详情
      if (formDetail.data?.flow_definition_id) {
        const flowDetail = await flowApi.getFlowDefinitionDetail(formDetail.data.flow_definition_id)
        console.log('流程详情数据:', flowDetail.data)
        
        // 优先从草稿获取节点和路由
        if (flowDetail.data?.draft) {
          flowNodes.value = flowDetail.data.draft.nodes || []
          flowRoutes.value = flowDetail.data.draft.routes || []
          console.log('从草稿获取 - flowNodes:', flowNodes.value)
          console.log('从草稿获取 - flowRoutes:', flowRoutes.value)
        } else if (flowDetail.data?.active_snapshot?.rules_payload) {
          // 如果没有草稿，从已发布的快照获取
          const payload = flowDetail.data.active_snapshot.rules_payload
          flowNodes.value = payload.nodes || []
          flowRoutes.value = payload.routes || []
          console.log('从快照获取 - flowNodes:', flowNodes.value)
          console.log('从快照获取 - flowRoutes:', flowRoutes.value)
        }
        
        console.log('最终 flowNodes.length:', flowNodes.value.length)
        console.log('最终 flowRoutes.length:', flowRoutes.value.length)
      }
    } catch (error) {
      console.error('加载表单详情失败:', error)
      message.error('加载表单详情失败')
    } finally {
      detailLoading.value = false
    }
  }

  // 获取字段类型标签
  const getFieldTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      'text': '单行文本',
      'textarea': '多行文本',
      'number': '数字',
      'phone': '手机号',
      'email': '邮箱',
      'select': '下拉选择',
      'radio': '单选',
      'checkbox': '多选',
      'switch': '开关',
      'date': '日期',
      'date-range': '日期范围',
      'time': '时间',
      'datetime': '日期时间',
      'rate': '评分',
      'upload': '文件上传',
      'calculated': '计算字段',
      'divider': '分割线',
      'description': '说明文字'
    }
    return typeMap[type] || type
  }

  // 获取字段类型标签样式
  const getFieldTypeTag = (type: string): TagType => {
    const tagMap: Record<string, TagType> = {
      'text': 'default',
      'textarea': 'default',
      'number': 'info',
      'phone': 'info',
      'email': 'info',
      'select': 'success',
      'radio': 'success',
      'checkbox': 'success',
      'switch': 'warning',
      'date': 'warning',
      'date-range': 'warning',
      'time': 'warning',
      'datetime': 'warning',
      'rate': 'warning',
      'upload': 'error',
      'calculated': 'info',
      'divider': 'default',
      'description': 'default'
    }
    return tagMap[type] || 'default'
  }

  // 获取字段类型图标 - 使用 emoji 作为备选
  const getFieldTypeIcon = (type: string): string => {
    const iconMap: Record<string, string> = {
      'text': '📝',
      'textarea': '📄',
      'number': '🔢',
      'phone': '📞',
      'email': '📧',
      'select': '📋',
      'radio': '⭕',
      'checkbox': '☑️',
      'switch': '🔘',
      'date': '📅',
      'date-range': '📆',
      'time': '⏰',
      'datetime': '⏱️',
      'rate': '⭐',
      'upload': '📎',
      'calculated': '🧮',
      'divider': '➖',
      'description': 'ℹ️'
    }
    return iconMap[type] || '📋'
  }

  // 获取字段发光效果类名
  const getFieldGlowClass = (type: string): string => {
    const glowMap: Record<string, string> = {
      'text': 'glow-blue',
      'textarea': 'glow-blue',
      'number': 'glow-cyan',
      'phone': 'glow-cyan',
      'email': 'glow-cyan',
      'select': 'glow-green',
      'radio': 'glow-green',
      'checkbox': 'glow-green',
      'switch': 'glow-orange',
      'date': 'glow-orange',
      'date-range': 'glow-orange',
      'time': 'glow-orange',
      'datetime': 'glow-orange',
      'rate': 'glow-orange',
      'upload': 'glow-red',
      'calculated': 'glow-purple',
      'divider': 'glow-gray',
      'description': 'glow-gray'
    }
    return glowMap[type] || 'glow-gray'
  }

  // 获取字段图标包装类名
  const getFieldIconClass = (type: string): string => {
    const iconClassMap: Record<string, string> = {
      'text': 'icon-blue',
      'textarea': 'icon-blue',
      'number': 'icon-cyan',
      'phone': 'icon-cyan',
      'email': 'icon-cyan',
      'select': 'icon-green',
      'radio': 'icon-green',
      'checkbox': 'icon-green',
      'switch': 'icon-orange',
      'date': 'icon-orange',
      'date-range': 'icon-orange',
      'time': 'icon-orange',
      'datetime': 'icon-orange',
      'rate': 'icon-orange',
      'upload': 'icon-red',
      'calculated': 'icon-purple',
      'divider': 'icon-gray',
      'description': 'icon-gray'
    }
    return iconClassMap[type] || 'icon-gray'
  }

  // 获取字段类型标签类名
  const getFieldTypeClass = (type: string): string => {
    const typeClassMap: Record<string, string> = {
      'text': 'type-blue',
      'textarea': 'type-blue',
      'number': 'type-cyan',
      'phone': 'type-cyan',
      'email': 'type-cyan',
      'select': 'type-green',
      'radio': 'type-green',
      'checkbox': 'type-green',
      'switch': 'type-orange',
      'date': 'type-orange',
      'date-range': 'type-orange',
      'time': 'type-orange',
      'datetime': 'type-orange',
      'rate': 'type-orange',
      'upload': 'type-red',
      'calculated': 'type-purple',
      'divider': 'type-gray',
      'description': 'type-gray'
    }
    return typeClassMap[type] || 'type-gray'
  }

  // 配置流程
  const handleConfigureFlow = (row: FormResponse) => {
    if (!row.flow_definition_id) {
      message.error('该表单没有关联的流程定义')
      return
    }
    router.push({
      path: `/flow/configurator/${row.flow_definition_id}`,
    })
  }

  // 发布表单
  const handlePublish = async (row: FormResponse) => {
    dialog.warning({
      title: '确认发布',
      content: `确定要发布表单"${row.name}"吗？发布后表单将可以被用户填写。`,
      positiveText: '发布',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await formApi.publishForm(row.id)
          message.success('发布成功')
          loadList()
        } catch (error) {
          message.error(resolveErrorMessage(error, '发布失败'))
        }
      },
    })
  }

  // 重新发布表单（将草稿版本的更改发布为新版本）
  const handleRepublish = async (row: FormResponse) => {
    dialog.warning({
      title: '确认重新发布',
      content: `表单"${row.name}"存在未发布的更改。重新发布将创建新版本并立即生效，是否继续？`,
      positiveText: '重新发布',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await formApi.publishForm(row.id)
          message.success('重新发布成功')
          loadList()
        } catch (error) {
          message.error(resolveErrorMessage(error, '重新发布失败'))
        }
      },
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
          h(NInput, {
            value: cloneName.value,
            'onUpdate:value': (val: string) => {
              cloneName.value = val
            },
            placeholder: '请输入表单名称',
          })
        ])
      },
      onPositiveClick: async () => {
        if (!cloneName.value.trim()) {
          message.error('请输入表单名称')
          return false
        }
        try {
          await formApi.cloneForm(row.id, cloneName.value)
          message.success('克隆成功')
          loadList()
        } catch (error) {
          message.error(resolveErrorMessage(error, '克隆失败'))
          return false
        }
      },
    })
  }

  // 删除表单
  const handleDelete = async (row: FormResponse) => {
    try {
      deleteLoading.value = true
      await formApi.deleteForm(row.id)
      message.success('删除成功')
      loadList()
    } catch (error: any) {
      // 检查是否是409冲突（需要级联删除）
      if (error.response?.status === 409 && error.response?.data?.data) {
        cascadeDialogData.value = error.response.data.data
        showCascadeDialog.value = true
      } else {
        message.error(resolveErrorMessage(error, '删除失败'))
      }
    } finally {
      deleteLoading.value = false
    }
  }

  // 处理级联删除确认
  const handleCascadeConfirm = async () => {
    if (!cascadeDialogData.value) return
    
    try {
      deleteLoading.value = true
      await formApi.deleteForm(cascadeDialogData.value.form_id, { cascade: true })
      message.success('表单及关联的审批流程已成功删除')
      showCascadeDialog.value = false
      cascadeDialogData.value = null
      loadList()
    } catch (error) {
      message.error(resolveErrorMessage(error, '删除失败'))
    } finally {
      deleteLoading.value = false
    }
  }

  // 处理级联删除取消
  const handleCascadeCancel = () => {
    showCascadeDialog.value = false
    cascadeDialogData.value = null
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

  const goHome = () => {
    router.push('/')
  }

  onMounted(() => {
    loadList()
    loadTemplates()
  })
  </script>
  
  <style scoped lang="scss">
  .form-list-page {
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
  
  .action-btn {
    transition: all 0.2s ease;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    &.primary-action {
      background: linear-gradient(135deg, #18a058 0%, #0e8a4a 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #0e8a4a 0%, #0a7040 100%);
        box-shadow: 0 4px 16px rgba(24, 160, 88, 0.3);
      }
    }
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

  // 表单详情弹窗样式
  .form-detail-modal {
    :deep(.n-card-header) {
      padding: 20px 24px;
      border-bottom: 1px solid #f0f0f0;

      .n-card-header__main {
        font-size: 18px;
        font-weight: 600;
        color: #1f2937;
      }
    }

    :deep(.n-card__content) {
      padding: 0;
    }
  }

  .detail-tabs {
    :deep(.n-tabs-nav) {
      padding: 0 24px;
      border-bottom: 1px solid #f0f0f0;
    }

    :deep(.n-tabs-tab) {
      padding: 16px 20px;
      font-size: 15px;
    }

    :deep(.n-tab-pane) {
      padding: 20px 24px;
    }
  }

  .fields-container {
    max-height: 520px;
    overflow-y: auto;
    padding-right: 8px;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 3px;

      &:hover {
        background: #a8a8a8;
      }
    }
  }

  // 字段卡片网格布局
  .field-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    padding: 4px;
  }

  .field-card {
    position: relative;
    background: white;
    border-radius: 12px;
    border: 1px solid #e8e8e8;
    padding: 16px;
    transition: all 0.25s ease;
    overflow: hidden;
    animation: cardFadeIn 0.4s ease forwards;
    opacity: 0;
    transform: translateY(10px);

    &:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
      border-color: #d0d0d0;
    }

    &.is-required {
      border-color: #fecaca;

      &:hover {
        border-color: #f87171;
      }
    }

    @keyframes cardFadeIn {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    // 发光效果
    .field-card-glow {
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      opacity: 0;
      filter: blur(40px);
      border-radius: 50%;
      transition: opacity 0.3s ease;
      pointer-events: none;

      &.glow-blue {
        background: radial-gradient(circle, #3b82f6 0%, transparent 60%);
      }
      &.glow-cyan {
        background: radial-gradient(circle, #06b6d4 0%, transparent 60%);
      }
      &.glow-green {
        background: radial-gradient(circle, #10b981 0%, transparent 60%);
      }
      &.glow-orange {
        background: radial-gradient(circle, #f59e0b 0%, transparent 60%);
      }
      &.glow-red {
        background: radial-gradient(circle, #ef4444 0%, transparent 60%);
      }
      &.glow-purple {
        background: radial-gradient(circle, #8b5cf6 0%, transparent 60%);
      }
      &.glow-gray {
        background: radial-gradient(circle, #6b7280 0%, transparent 60%);
      }
    }

    &:hover .field-card-glow {
      opacity: 0.06;
    }

    .field-card-content {
      position: relative;
      z-index: 1;
    }

    .field-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
      padding-left: 32px;

      .field-icon-wrapper {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;

        &.icon-blue {
          background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
          .field-type-icon { color: #3b82f6; }
        }
        &.icon-cyan {
          background: linear-gradient(135deg, #ecfeff 0%, #cffafe 100%);
          box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
          .field-type-icon { color: #06b6d4; }
        }
        &.icon-green {
          background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
          box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2);
          .field-type-icon { color: #22c55e; }
        }
        &.icon-orange {
          background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
          box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
          .field-type-icon { color: #f59e0b; }
        }
        &.icon-red {
          background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
          box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
          .field-type-icon { color: #ef4444; }
        }
        &.icon-purple {
          background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
          box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
          .field-type-icon { color: #8b5cf6; }
        }
        &.icon-gray {
          background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
          box-shadow: 0 4px 12px rgba(107, 114, 128, 0.2);
          .field-type-icon { color: #6b7280; }
        }

        .field-type-icon {
          font-size: 28px;
          line-height: 1;
          transition: transform 0.3s ease;
          filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
        }
      }

      &:hover .field-icon-wrapper .field-type-icon {
        transform: scale(1.1);
      }

      .field-badges {
        display: flex;
        flex-direction: column;
        gap: 6px;

        .required-badge, .unique-badge {
          font-size: 10px;
          padding: 2px 8px;
          height: 20px;
          border-radius: 10px;
          font-weight: 500;

          .badge-icon {
            font-size: 10px;
          }
        }
      }
    }

    .field-body {
      margin-bottom: 16px;

      .field-title {
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 8px 0;
        line-height: 1.4;
      }

      .field-description, .field-placeholder {
        font-size: 13px;
        color: #64748b;
        margin: 0;
        line-height: 1.5;
        display: flex;
        align-items: flex-start;
        gap: 6px;

        .desc-icon, .placeholder-icon {
          font-size: 14px;
          margin-top: 2px;
          flex-shrink: 0;
        }
      }

      .field-placeholder {
        color: #94a3b8;
        font-style: italic;
      }
    }

    .field-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 12px;
      border-top: 1px solid #f1f5f9;

      .field-type-label {
        font-size: 12px;
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 6px;
        background: #f8fafc;

        &.type-blue { color: #3b82f6; background: #eff6ff; }
        &.type-cyan { color: #06b6d4; background: #ecfeff; }
        &.type-green { color: #22c55e; background: #f0fdf4; }
        &.type-orange { color: #f59e0b; background: #fffbeb; }
        &.type-red { color: #ef4444; background: #fef2f2; }
        &.type-purple { color: #8b5cf6; background: #f5f3ff; }
        &.type-gray { color: #6b7280; background: #f9fafb; }
      }

      .field-validation {
        font-size: 11px;
        color: #10b981;
        display: flex;
        align-items: center;
        gap: 4px;

        .validation-icon {
          font-size: 12px;
        }
      }
    }

    .field-index-badge {
      position: absolute;
      top: 12px;
      left: 12px;
      width: 24px;
      height: 24px;
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: white;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
      box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
      z-index: 2;
      transition: all 0.3s ease;
    }

    &:hover .field-index-badge {
      transform: scale(1.1) rotate(-5deg);
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.6);
    }
  }

  .flow-container {
    min-height: 500px;
    max-height: 600px;
    overflow: hidden;
    padding: 0;
    border-radius: 16px;
  }

  .flow-diagram-wrapper {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    padding: 0;
    min-height: 500px;
    height: 500px;
    overflow: hidden;
  }

  .flow-diagram {
    width: 100%;
    height: 100%;
  }
  </style>