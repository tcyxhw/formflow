<template>
  <div class="my-approvals-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>我的审批</h1>
          <p class="subtitle">查看我发起的审批进度与详情</p>
        </div>
        <div class="header-actions">
          <n-button @click="showImportModal = true" type="primary" ghost>
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </template>
            导入数据
          </n-button>
          <n-button v-if="selectedDraftIds.length > 0" @click="handleBatchApprove" type="primary" :loading="batchApproveLoading">
            批量通过 ({{ selectedDraftIds.length }})
          </n-button>
          <n-button v-if="selectedPendingIds.length > 0" @click="handleBatchSubmit" type="primary" ghost :loading="batchSubmitLoading">
            批量提交 ({{ selectedPendingIds.length }})
          </n-button>
          <n-button @click="goHome" quaternary>
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            </template>
            返回主页
          </n-button>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="main-layout">
      <!-- 左侧：表单分组 -->
      <aside class="sidebar">
        <div class="sidebar-search">
          <n-input v-model:value="searchKeyword" placeholder="搜索表单..." clearable size="small">
            <template #prefix>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            </template>
          </n-input>
        </div>
        <div class="status-tabs">
          <n-button
            v-for="tab in statusTabs"
            :key="tab.value"
            :type="statusFilter === tab.value ? 'primary' : 'default'"
            size="tiny"
            quaternary
            @click="statusFilter = tab.value"
          >{{ tab.label }}</n-button>
        </div>
        <div class="sidebar-list" v-loading="loading">
          <div
            v-for="group in groupedForms"
            :key="group.form_id"
            class="form-group-card"
            :class="{ active: selectedFormId === group.form_id }"
            @click="selectForm(group.form_id)"
          >
            <div class="form-group-name">{{ group.form_name }}</div>
            <div class="form-group-stats">
              <span class="stat-item" v-if="countByState(group.items, 'draft')">
                <span class="stat-dot draft"></span>{{ countByState(group.items, 'draft') }} 待通过
              </span>
              <span class="stat-item" v-if="countByState(group.items, 'pending_approval')">
                <span class="stat-dot pending"></span>{{ countByState(group.items, 'pending_approval') }} 待提交
              </span>
              <span class="stat-item" v-if="countByState(group.items, 'running')">
                <span class="stat-dot running"></span>{{ countByState(group.items, 'running') }} 进行中
              </span>
              <span class="stat-item" v-if="countByState(group.items, 'finished')">
                <span class="stat-dot finished"></span>{{ countByState(group.items, 'finished') }} 已完成
              </span>
              <span class="stat-item" v-if="countByState(group.items, 'canceled')">
                <span class="stat-dot canceled"></span>{{ countByState(group.items, 'canceled') }} 已撤回
              </span>
            </div>
          </div>
          <n-empty v-if="groupedForms.length === 0 && !loading" description="暂无审批记录" />
        </div>
      </aside>

      <!-- 右侧：提交列表 -->
      <main class="content-area" v-if="selectedFormGroup">
        <!-- 统计栏 -->
        <div class="stats-bar">
          <div class="stats-title">{{ selectedFormGroup.form_name }}</div>
          <div class="stats-pills">
            <span class="pill">总计 {{ selectedFormGroup.items.length }}</span>
            <span class="pill draft" v-if="draftCount">待通过 {{ draftCount }}</span>
            <span class="pill running" v-if="runningCount">运行中 {{ runningCount }}</span>
            <span class="pill finished" v-if="finishedCount">已完成 {{ finishedCount }}</span>
          </div>
        </div>

        <!-- 提交卡片列表 -->
        <div class="submission-list">
          <div
            v-for="item in selectedFormGroup.items"
            :key="item.id"
            class="submission-card"
            :class="[`status-${item.status === 'draft' ? 'draft' : item.process_state || 'pending_approval'}`]"
          >
            <!-- 左侧 checkbox（仅草稿和待提交） -->
            <n-checkbox
              v-if="item.status === 'draft' || item.status === 'pending_approval' || item.process_state === 'pending_approval' || item.process_state === 'canceled'"
              :checked="selectedDraftIds.includes(item.id) || selectedPendingIds.includes(item.id)"
              @click.stop="toggleSelect(item)"
              class="draft-checkbox"
            />

            <!-- 中间信息 -->
            <div class="submission-info">
              <div class="submission-meta">
                <span class="submission-time">{{ formatDateTime(item.created_at) }}</span>
                <n-tag :type="getStateType(item.process_state, item.is_overdue)" size="small" :bordered="false">
                  {{ getStateLabel(item.process_state, item.is_overdue, item.status) }}
                </n-tag>
              </div>
              <div class="submission-due" v-if="item.due_at">
                截止: <span :class="{ overdue: item.is_overdue }">{{ formatDateTime(item.due_at) }}</span>
              </div>
            </div>

              <!-- 右侧操作 -->
            <div class="submission-actions">
              <!-- 草稿：编辑 / 删除 / 通过 -->
              <template v-if="item.status === 'draft'">
                <n-button size="tiny" @click.stop="editSubmission(item)">编辑</n-button>
                <n-button size="tiny" type="error" ghost @click.stop="deleteDraft(item)">删除</n-button>
                <n-button size="tiny" type="primary" @click.stop="handleApprove(item)">通过</n-button>
              </template>
              <!-- 待提交：编辑 / 提交 -->
              <template v-else-if="item.status === 'pending_approval' || item.process_state === 'pending_approval'">
                <n-button size="tiny" @click.stop="editSubmission(item)">编辑</n-button>
                <n-button size="tiny" type="primary" @click.stop="handleSubmit(item)">提交</n-button>
                <n-button size="tiny" @click.stop="toggleDetail(item)">
                  {{ expandedSubmissionId === item.id ? '收起' : '详情' }}
                </n-button>
              </template>
              <!-- 其他状态 -->
              <template v-else>
                <n-button v-if="item.process_state === 'running'" size="tiny" type="warning" ghost @click.stop="handleWithdraw(item)">撤回</n-button>
                <n-button v-if="item.process_state === 'canceled'" size="tiny" @click.stop="editSubmission(item)">编辑</n-button>
                <n-button v-if="item.process_state === 'canceled'" size="tiny" type="primary" @click.stop="handleSubmit(item)">提交</n-button>
                <n-button size="tiny" @click.stop="toggleDetail(item)">
                  {{ expandedSubmissionId === item.id ? '收起' : '详情' }}
                </n-button>
              </template>
            </div>

            <!-- 展开的详情区域 -->
            <div class="detail-panel" :class="{ expanded: expandedSubmissionId === item.id }">
              <div v-if="expandedSubmissionId === item.id">
                <div v-if="flowLoading" class="detail-loading">
                  <n-spin size="small" /> 加载中...
                </div>
                <div v-else-if="flowNodes.length > 0">
                  <div class="detail-section-title">审批流程</div>
                  <FlowDiagram :nodes="flowNodes" :routes="flowRoutes" :timeline="processTimeline" />
                </div>
                <div v-else class="detail-empty">暂无流程数据</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- 未选择时占位 -->
      <main class="content-area empty" v-else>
        <n-empty description="从左侧选择一个表单查看审批记录" />
      </main>
    </div>

    <!-- 导入弹窗 -->
    <n-modal v-model:show="showImportModal" preset="dialog" title="导入数据" style="width: 500px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="选择表单">
          <n-select v-model:value="importFormId" :options="formOptions" placeholder="请选择要导入的表单" filterable />
        </n-form-item>
        <n-form-item label="操作">
          <n-space>
            <n-button size="small" @click="handleDownloadTemplate" :disabled="!importFormId">下载模板</n-button>
            <n-upload :show-file-list="false" accept=".xlsx,.xls" :custom-request="handleImportUpload">
              <n-button size="small" type="primary" :disabled="!importFormId" :loading="importLoading">选择文件并导入</n-button>
            </n-upload>
          </n-space>
        </n-form-item>
      </n-form>
      <n-alert v-if="importResult" :type="importResult.success ? 'success' : 'warning'" :title="importResult.message" style="margin-top: 12px" />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMySubmittedApprovals } from '@/stores/mySubmittedApprovals'
import type { MyApprovalItem } from '@/stores/mySubmittedApprovals'
import { startApproval, batchImport, batchSubmit, batchApprove, downloadImportTemplate, deleteSubmission } from '@/api/submission'
import { cancelTaskBySubmission } from '@/api/approvals'
import { getFillableForms } from '@/api/workspace'
import FlowDiagram from '@/components/form/FlowDiagram.vue'
import { useMessage } from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()
const approvalStore = useMySubmittedApprovals()
const message = useMessage()

// 响应式数据
const searchKeyword = ref('')
const statusFilter = ref('all')
const selectedFormId = ref<number | null>(null)

const statusTabs = [
  { label: '全部', value: 'all' },
  { label: '待通过', value: 'draft' },
  { label: '待提交', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '已完成', value: 'finished' },
  { label: '已撤回', value: 'canceled' },
]

// 导入
const showImportModal = ref(false)
const importFormId = ref<number | null>(null)
const importLoading = ref(false)
const importResult = ref<{ success: boolean; message: string } | null>(null)
const formOptions = ref<Array<{ label: string; value: number }>>([])

// 批量操作
const selectedDraftIds = ref<number[]>([])
const selectedPendingIds = ref<number[]>([])
const batchApproveLoading = ref(false)
const batchSubmitLoading = ref(false)

// 详情展开
const expandedSubmissionId = ref<number | null>(null)

// 计算属性
const loading = computed(() => approvalStore.loading)
const flowLoading = computed(() => approvalStore.flowLoading)
const flowNodes = computed(() => approvalStore.flowNodes)
const flowRoutes = computed(() => approvalStore.flowRoutes)
const processTimeline = computed(() => approvalStore.processTimeline)

const filteredApprovals = computed(() => {
  let list = approvalStore.approvalList
  // 表单名称搜索
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(item => item.form_name.toLowerCase().includes(kw))
  }
  // 状态筛选
  if (statusFilter.value !== 'all') {
    list = list.filter(item => {
      switch (statusFilter.value) {
        case 'draft': return item.status === 'draft'
        case 'pending': return item.process_state === 'pending_approval'
        case 'running': return item.process_state === 'running'
        case 'finished': return item.process_state === 'finished'
        case 'canceled': return item.process_state === 'canceled' || item.process_state === 'pending_approval'
        default: return true
      }
    })
  }
  return list
})

const groupedForms = computed(() => {
  const map = new Map<number, { form_id: number; form_name: string; items: MyApprovalItem[] }>()
  for (const item of filteredApprovals.value) {
    if (!map.has(item.form_id)) {
      map.set(item.form_id, { form_id: item.form_id, form_name: item.form_name, items: [] })
    }
    map.get(item.form_id)!.items.push(item)
  }
  return Array.from(map.values())
})

const selectedFormGroup = computed(() => {
  if (!selectedFormId.value) return null
  return groupedForms.value.find(g => g.form_id === selectedFormId.value) || null
})

const draftCount = computed(() => selectedFormGroup.value ? countByState(selectedFormGroup.value.items, 'draft') : 0)
const runningCount = computed(() => selectedFormGroup.value ? countByState(selectedFormGroup.value.items, 'running') : 0)
const finishedCount = computed(() => selectedFormGroup.value ? countByState(selectedFormGroup.value.items, 'finished') : 0)

// 方法
const countByState = (items: MyApprovalItem[], state: string): number => {
  if (state === 'draft') return items.filter(i => i.status === 'draft').length
  if (state === 'pending_approval') return items.filter(i => i.process_state === 'pending_approval').length
  if (state === 'running') return items.filter(i => i.process_state === 'running').length
  if (state === 'finished') return items.filter(i => i.process_state === 'finished').length
  if (state === 'canceled') return items.filter(i => i.process_state === 'canceled' || i.process_state === 'pending_approval').length
  return 0
}

const goHome = () => router.push('/')
const refreshApprovals = async () => { await approvalStore.loadMyApprovals() }

const selectForm = (formId: number) => {
  selectedFormId.value = formId
  selectedDraftIds.value = []
  selectedPendingIds.value = []
  expandedSubmissionId.value = null
}

const editSubmission = (item: MyApprovalItem) => {
  router.push(`/form/${item.form_id}/fill?edit_submission_id=${item.id}`)
}

const viewSubmissionDetail = (item: MyApprovalItem) => {
  router.push(`/submissions/${item.id}`)
}

const toggleDetail = async (item: MyApprovalItem) => {
  if (expandedSubmissionId.value === item.id) {
    expandedSubmissionId.value = null
    return
  }
  expandedSubmissionId.value = item.id
  // 设置选中项，computed refs 会自动返回该提交的流程数据
  approvalStore.selectedApproval = item
  // 按需加载流程数据（已有缓存则跳过）
  if (item.process_instance_id) {
    await approvalStore.loadFlowDiagram(item.form_id, item.process_instance_id, item.flow_definition_id)
  }
}

const handleStartApproval = async (item: MyApprovalItem) => {
  try {
    await startApproval(item.id)
    message.success('已通过，审批流程已发起')
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '通过失败')
  }
}

const handleWithdraw = async (item: MyApprovalItem) => {
  try {
    await cancelTaskBySubmission(item.id)
    message.success('已撤回')
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '撤回失败')
  }
}

// 通过（草稿 → 待提交）
const handleApprove = async (item: MyApprovalItem) => {
  try {
    await batchApprove([item.id])
    message.success('已通过')
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '通过失败')
  }
}

// 提交（待提交 → 审批流程）
const handleSubmit = async (item: MyApprovalItem) => {
  try {
    await startApproval(item.id)
    message.success('已提交，审批流程已发起')
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '提交失败')
  }
}

// 批量通过
const handleBatchApprove = async () => {
  if (!selectedDraftIds.value.length) return
  batchApproveLoading.value = true
  try {
    const res = await batchApprove(selectedDraftIds.value)
    message.success(res.message || '批量通过完成')
    selectedDraftIds.value = []
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '批量通过失败')
  } finally {
    batchApproveLoading.value = false
  }
}

// 多选切换
const toggleSelect = (item: MyApprovalItem) => {
  if (item.status === 'draft') {
    const idx = selectedDraftIds.value.indexOf(item.id)
    if (idx >= 0) selectedDraftIds.value.splice(idx, 1)
    else selectedDraftIds.value.push(item.id)
  } else if (item.status === 'pending_approval' || item.process_state === 'pending_approval' || item.process_state === 'canceled') {
    const idx = selectedPendingIds.value.indexOf(item.id)
    if (idx >= 0) selectedPendingIds.value.splice(idx, 1)
    else selectedPendingIds.value.push(item.id)
  }
}

const deleteDraft = async (item: MyApprovalItem) => {
  try {
    await deleteSubmission(item.id)
    message.success('草稿删除成功')
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '删除失败')
  }
}

// 导入
const handleDownloadTemplate = () => {
  if (!importFormId.value) return
  downloadImportTemplate(importFormId.value)
}

const handleImportUpload = async (options: any) => {
  if (!importFormId.value) return
  importLoading.value = true
  importResult.value = null
  try {
    const res = await batchImport(importFormId.value, options.file.file)
    importResult.value = { success: true, message: `成功导入 ${res.data.created} 条草稿` }
    await approvalStore.loadMyApprovals()
    selectedFormId.value = importFormId.value
  } catch (error: any) {
    importResult.value = { success: false, message: error?.message || '导入失败' }
  } finally {
    importLoading.value = false
  }
}

const loadFormOptions = async () => {
  try {
    const res = await getFillableForms({ page: 1, page_size: 100 })
    formOptions.value = (res.data?.items || []).map((f: any) => ({ label: f.name, value: f.id }))
  } catch { formOptions.value = [] }
}

// 批量提交（待提交 → 审批流程）
const handleBatchSubmit = async () => {
  if (!selectedPendingIds.value.length) return
  batchSubmitLoading.value = true
  try {
    const res = await batchSubmit(selectedPendingIds.value)
    message.success(res.message || '批量提交完成')
    selectedPendingIds.value = []
    await approvalStore.loadMyApprovals()
  } catch (error: any) {
    message.error(error?.message || '批量提交失败')
  } finally {
    batchSubmitLoading.value = false
  }
}

// 工具
const getStateType = (state: string | null, isOverdue?: boolean) => approvalStore.getStateType(state, isOverdue)
const getStateLabel = (state: string | null, isOverdue?: boolean, status?: string) => approvalStore.getStateLabel(state, isOverdue, status)

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// 导入弹窗打开时加载表单选项
watch(showImportModal, (val) => { if (val) loadFormOptions() })

// 初始化
onMounted(async () => {
  if (authStore.isLoggedIn) {
    await approvalStore.loadMyApprovals()
    if (groupedForms.value.length && !selectedFormId.value) {
      selectedFormId.value = groupedForms.value[0].form_id
    }
  }
})
</script>

<style scoped>
.my-approvals-page {
  min-height: 100vh;
  background: #f5f7fa;
}

/* 头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 28px 32px;
}
.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-text h1 { margin: 0; font-size: 24px; font-weight: 700; }
.header-text .subtitle { margin: 4px 0 0; font-size: 14px; opacity: 0.8; }
.header-actions { display: flex; gap: 12px; }
.header-actions .n-button { color: white; border-color: rgba(255,255,255,0.3); }
.header-actions .n-button:hover { background: rgba(255,255,255,0.15); }

/* 主布局 */
.my-approvals-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
}

.main-layout {
  flex: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 32px;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

/* 左侧边栏 */
.sidebar {
  background: white;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-search { padding: 16px; border-bottom: 1px solid #f0f0f0; }
.status-tabs { display: flex; gap: 4px; padding: 8px 12px 12px; border-bottom: 1px solid #f0f0f0; }
.sidebar-list { flex: 1; overflow-y: auto; padding: 8px; }

.form-group-card {
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  border: 1px solid transparent;
}
.form-group-card:hover { background: #f8fafc; }
.form-group-card.active {
  background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
  border-color: #667eea;
}
.form-group-name { font-weight: 600; color: #1a202c; font-size: 14px; margin-bottom: 8px; }
.form-group-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.stat-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #6b7280; }
.stat-dot { width: 6px; height: 6px; border-radius: 50%; }
.stat-dot.draft { background: #f59e0b; }
.stat-dot.pending { background: #8b5cf6; }
.stat-dot.running { background: #3b82f6; }
.stat-dot.finished { background: #10b981; }
.stat-dot.canceled { background: #9ca3af; }

/* 右侧内容 */
.content-area {
  background: white;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content-area.empty { display: flex; align-items: center; justify-content: center; min-height: 400px; }

/* 统计栏 */
.stats-bar {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stats-title { font-size: 16px; font-weight: 600; color: #1a202c; }
.stats-pills { display: flex; gap: 8px; }
.pill {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  background: #f3f4f6;
  color: #6b7280;
}
.pill.draft { background: #fef3c7; color: #92400e; }
.pill.running { background: #dbeafe; color: #1e40af; }
.pill.finished { background: #d1fae5; color: #065f46; }

/* 提交列表 */
.submission-list { flex: 1; overflow-y: auto; padding: 16px 24px; }

.submission-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  margin-bottom: 8px;
  transition: all 0.25s ease;
  flex-wrap: wrap;
}
.submission-card:hover {
  border-color: #e5e7eb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.submission-card.status-draft { border-left: 3px solid #f59e0b; }
.submission-card.status-running,
.submission-card.status-submitted { border-left: 3px solid #3b82f6; }
.submission-card.status-completed,
.submission-card.status-approved { border-left: 3px solid #10b981; }
.submission-card.status-canceled { border-left: 3px solid #9ca3af; }
.submission-card.status-pending_approval { border-left: 3px solid #8b5cf6; background: #f5f3ff; }

.submission-info { flex: 1; min-width: 0; }
.submission-meta { display: flex; align-items: center; gap: 10px; }
.submission-time { font-size: 13px; color: #374151; font-weight: 500; }
.submission-due { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.submission-due .overdue { color: #ef4444; font-weight: 500; }

.submission-actions { display: flex; gap: 6px; flex-shrink: 0; }

/* 展开详情面板 */
.detail-panel {
  flex-basis: 100%;
  height: 0;
  overflow: hidden;
  transform: translateY(-10px);
  opacity: 0;
  transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.3s ease,
              transform 0.4s cubic-bezier(0.4, 0, 0.2, 1),
              padding 0.3s ease,
              margin 0.3s ease;
}
.detail-panel.expanded {
  height: auto;
  transform: translateY(0);
  opacity: 1;
  margin-top: 8px;
  padding: 16px 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.detail-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}
.detail-loading { display: flex; align-items: center; gap: 8px; color: #9ca3af; font-size: 13px; }
.detail-empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 16px; }

/* 导入弹窗 */
</style>
