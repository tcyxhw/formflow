<template>
  <div class="flow-config-page">
    <div class="config-header">
      <div>
        <div class="title">{{ store.flowName || '流程配置' }}</div>
        <div class="meta">
          <span v-if="flowId">流程 ID：{{ flowId }}</span>
          <span class="version-info">
            <n-tag :type="store.dirty ? 'warning' : 'success'" size="small">
              草稿 v{{ store.version }}
            </n-tag>
            <n-tag v-if="latestSnapshotTag" type="info" size="small" style="margin-left: 8px;">
              已发布 {{ latestSnapshotTag }}
            </n-tag>
          </span>
          <span>上次保存：{{ formatTimestamp(store.lastSavedAt) }}</span>
          <span :class="{ dirty: store.dirty }">
            {{ store.dirty ? '未保存修改' : '已保存' }}
          </span>
          <span v-if="autoSaving" class="autosave">自动保存中…</span>
        </div>
      </div>
      <div class="header-actions">
        <n-space align="center" wrap>
          <n-popover trigger="click" placement="bottom-end">
            <template #trigger>
              <n-button quaternary size="small">
                版本信息
              </n-button>
            </template>
            <div class="version-popover">
              <n-descriptions :column="1" label-placement="left" size="small">
                <n-descriptions-item label="草稿版本">
                  v{{ store.version }}
                </n-descriptions-item>
                <n-descriptions-item label="已发布快照">
                  {{ store.snapshots.length }} 个
                </n-descriptions-item>
                <n-descriptions-item v-if="latestSnapshot" label="最新快照">
                  {{ latestSnapshot.version_tag }}
                </n-descriptions-item>
                <n-descriptions-item v-if="latestSnapshot" label="发布者">
                  {{ latestSnapshot.created_by || '-' }}
                </n-descriptions-item>
                <n-descriptions-item label="上次保存">
                  {{ formatTimestamp(store.lastSavedAt) }}
                </n-descriptions-item>
                <n-descriptions-item label="上次发布">
                  {{ formatTimestamp(store.lastPublishedAt) }}
                </n-descriptions-item>
              </n-descriptions>
              <n-divider v-if="store.snapshots.length > 0" style="margin: 12px 0;" />
              <div v-if="store.snapshots.length > 0" class="snapshot-list">
                <div class="snapshot-list-title">历史快照</div>
                <div v-for="snapshot in store.snapshots.slice(0, 5)" :key="snapshot.id" class="snapshot-item">
                  <span class="snapshot-tag">{{ snapshot.version_tag }}</span>
                  <span class="snapshot-time">{{ formatTimestamp(snapshot.created_at) }}</span>
                </div>
                <div v-if="store.snapshots.length > 5" class="snapshot-more">
                  还有 {{ store.snapshots.length - 5 }} 个历史快照...
                </div>
              </div>
            </div>
          </n-popover>
          <div class="autosave-control">
            <span>自动保存</span>
            <n-switch
              size="small"
              :value="autoSaveEnabled"
              @update:value="toggleAutoSave"
            />
          </div>
          <n-select
            v-if="autoSaveEnabled"
            class="autosave-delay"
            size="small"
            :value="autoSaveDelay"
            :options="autoSaveOptions"
            @update:value="handleAutoSaveDelayChange"
          />
          <n-button quaternary :loading="store.loading" @click="handleRefresh">
            刷新
          </n-button>
          <n-button :loading="store.saving" @click="handleSaveDraft" type="primary">
            保存草稿
          </n-button>
          <n-button :loading="store.publishing" type="success" @click="handlePublish">
            发布流程
          </n-button>
        </n-space>
      </div>
    </div>

    <div class="config-layout" v-if="flowId">
      <div class="sidebar-left">
        <FlowNodePalette :disabled="isDisabled" @add-node="handleAddNode" />
        <div class="divider"></div>
        <FlowRouteList
          :routes="store.routes"
          :nodes="store.nodes"
          :selected-index="store.selectedRouteIndex"
          :disabled="isDisabled"
          @select="handleSelectRoute"
          @add-route="handleAddRoute"
          @delete="handleDeleteRoute"
        />
      </div>
      <div class="canvas-area">
        <FlowDraftCanvas
          :nodes="store.nodes"
          :routes="store.routes"
          :nodes-graph="store.nodesGraph"
          :selected-key="store.selectedNodeKey"
          @select-node="store.selectNodeByKey"
          @update-position="handleUpdatePosition"
        />
      </div>
      <div class="sidebar-right">
        <div class="sidebar-right-scroll">
          <section class="panel">
            <FlowNodeInspector
              :node="store.currentNode"
              :all-nodes="store.nodes"
              :routes="store.routes"
              :selected-index="store.selectedRouteIndex"
              :form-schema="formSchema"
              :form-id="formId"
              :disabled="isDisabled"
              @update-node="handleUpdateNode"
              @select-route="handleSelectRoute"
            />
          </section>
          <section class="panel">
            <FlowRouteInspector
              :route="store.currentRoute"
              :node-options="routeNodeOptions"
              :selected-index="store.selectedRouteIndex"
              :disabled="isDisabled"
              :form-schema="formSchema"
              :form-id="formId"
              :nodes="store.nodes"
              :routes="store.routes"
              :current-node-key="store.selectedNodeKey"
              @update-route="handleUpdateRoute"
            />
          </section>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <n-empty description="缺少流程 ID，请从流程列表进入配置器">
        <n-button type="primary" @click="returnToHome">返回首页</n-button>
      </n-empty>
    </div>

    <n-modal
      v-model:show="publishModalVisible"
      preset="card"
      title="发布流程"
      class="publish-modal"
      :mask-closable="false"
      style="width: 500px; max-width: 90vw;"
    >
      <n-alert type="info" class="publish-tip" show-icon>
        发布会生成新的快照，建议填写版本标签与变更说明，便于团队追溯。
      </n-alert>
      <n-form
        ref="publishFormRef"
        :model="publishForm"
        :rules="publishFormRules"
        label-placement="top"
        require-mark-placement="left"
      >
        <n-form-item label="版本标签" path="versionTag">
          <n-input
            v-model:value="publishForm.versionTag"
            maxlength="32"
            placeholder="例如 v1.2.0 或 beta"
            clearable
          />
        </n-form-item>
        <n-form-item label="变更说明" path="changelog">
          <n-input
            v-model:value="publishForm.changelog"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            maxlength="500"
            placeholder="记录本次发布的主要修改点"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space justify="end">
          <n-button quaternary @click="closePublishModal">取消</n-button>
          <n-button type="primary" :loading="store.publishing" @click="handleSubmitPublish">
            确认发布
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { useDialog, useMessage, useNotification } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import dayjs from 'dayjs'
import FlowNodePalette from '@/components/flow-configurator/FlowNodePalette.vue'
import FlowDraftCanvas from '@/components/flow-configurator/FlowDraftCanvas.vue'
import FlowNodeInspector from '@/components/flow-configurator/FlowNodeInspector.vue'
import FlowRouteList from '@/components/flow-configurator/FlowRouteList.vue'
import FlowRouteInspector from '@/components/flow-configurator/FlowRouteInspector.vue'
import { useFlowDraftStore } from '@/stores/flowDraft'
import { getFormDetail } from '@/api/form'
import type { FlowNodeConfig, FlowNodePosition, FlowRouteConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const notification = useNotification()
const store = useFlowDraftStore()

// 最新快照信息
const latestSnapshot = computed(() => {
  if (!store.snapshots || store.snapshots.length === 0) return null
  return store.snapshots[0]
})

const latestSnapshotTag = computed(() => {
  if (!latestSnapshot.value) return null
  return latestSnapshot.value.version_tag
})

const flowId = computed(() => {
  const paramId = route.params.id as string | undefined
  const queryId = route.query.id as string | undefined
  const raw = paramId ?? queryId
  if (!raw) {
    return undefined
  }
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : undefined
})

const formSchema = ref<FormSchema>()
const formId = ref<number>()
const isDisabled = computed(() => store.loading || store.saving || !flowId.value)

const routeNodeOptions = computed(() =>
  store.nodes.map(node => ({
    label: node.name,
    value: node.id?.toString() ?? node.temp_id ?? ''
  }))
)

const autoSaving = ref(false)
const autoSaveEnabled = ref(true)
const autoSaveDelay = ref(8000)
const autoSaveOptions = [
  { label: '5 秒', value: 5000 },
  { label: '8 秒', value: 8000 },
  { label: '15 秒', value: 15000 }
]
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null

const publishModalVisible = ref(false)
const publishFormRef = ref<FormInst | null>(null)
const publishForm = ref({
  versionTag: '',
  changelog: ''
})
const publishFormRules: FormRules = {
  versionTag: [
    {
      validator: (_, value: string) => {
        if (!value) return true
        return /^[A-Za-z0-9._-]{1,32}$/.test(value)
      },
      message: '仅支持字母、数字、./_/- 且不超过 32 字符',
      trigger: ['input', 'blur']
    }
  ],
  changelog: [
    { required: true, message: '请填写本次发布的变更说明', trigger: ['input', 'blur'] },
    { min: 5, message: '至少 5 个字符', trigger: 'blur' }
  ]
}

const formatTimestamp = (value: string | null) =>
  value ? dayjs(value).format('YYYY-MM-DD HH:mm:ss') : '—'

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback

const clearAutoSaveTimer = () => {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
    autoSaveTimer = null
  }
}

const showVersionConflictDialog = () => {
  dialog.warning({
    title: '检测到新草稿版本',
    content: '后端草稿版本已更新，请刷新以同步最新修改。',
    positiveText: '刷新草稿',
    negativeText: '稍后',
    onPositiveClick: () => {
      if (flowId.value) {
        loadFlowDraft(flowId.value)
      }
    }
  })
}

const confirmDiscardLocalChanges = (messageText: string) => {
  if (!store.dirty) return Promise.resolve(true)
  return new Promise<boolean>((resolve) => {
    dialog.warning({
      title: '存在未保存的修改',
      content: messageText,
      positiveText: '仍然继续',
      negativeText: '取消',
      maskClosable: false,
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false),
      onClose: () => resolve(false)
    })
  })
}

const handleSaveError = (error: unknown, { silent = false } = {}) => {
  const messageText = resolveErrorMessage(error, '保存草稿失败')
  if (silent) {
    message.warning(messageText)
  } else {
    message.error(messageText)
  }
  if (messageText.includes('版本')) {
    showVersionConflictDialog()
  }
}

const performSave = async ({ silent = false, reason = 'manual' }: { silent?: boolean; reason?: 'manual' | 'auto' } = {}) => {
  try {
    await store.saveDraftRemote()
    const successText = reason === 'auto' ? '自动保存成功' : '草稿已保存'
    if (!silent) {
      message.success(successText)
    } else if (reason === 'auto') {
      message.success(successText)
    }
  } catch (error) {
    handleSaveError(error, { silent })
    throw error
  }
}

const scheduleAutoSave = () => {
  if (!autoSaveEnabled.value || !store.dirty || store.saving || store.loading || store.publishing) {
    return
  }
  clearAutoSaveTimer()
  autoSaveTimer = setTimeout(async () => {
    if (!store.dirty) return
    autoSaving.value = true
    try {
      await performSave({ silent: true, reason: 'auto' })
    } finally {
      autoSaving.value = false
    }
  }, autoSaveDelay.value)
}

const loadFlowDraft = async (id: number) => {
  try {
    const result = await store.loadDefinition(id)
    
    // 加载关联的表单schema
    try {
      const loadedFormId = result.detail?.definition?.form_id
      formId.value = loadedFormId
      console.log('Flow definition loaded:', {
        flowId: id,
        formId: loadedFormId,
        definition: result.detail?.definition
      })
      
      if (loadedFormId) {
        try {
          const formDetail = await getFormDetail(loadedFormId)
          formSchema.value = formDetail.schema_json
          console.log('Form schema loaded successfully:', {
            formId: loadedFormId,
            hasFields: !!formDetail.schema_json?.fields,
            fieldsCount: formDetail.schema_json?.fields?.length || 0,
            fieldsSample: formDetail.schema_json?.fields?.slice(0, 2).map((f: any) => ({ id: f.id, label: f.label })),
            fullSchema: formDetail.schema_json
          })
        } catch (formError) {
          console.warn(`Failed to load form schema for form ID ${loadedFormId}:`, formError)
          message.warning(`无法加载表单 ID ${loadedFormId} 的字段信息，条件构建器可能无法正常工作`)
          // 不影响流程配置的加载，但提示用户
        }
      } else {
        console.warn('No form_id found in flow definition')
      }
    } catch (error) {
      console.warn('Unexpected error loading form schema:', error)
      // 不影响流程配置的加载
    }
  } catch (error) {
    message.error(resolveErrorMessage(error, '加载流程失败'))
  }
}

const handleRefresh = async () => {
  if (!flowId.value) {
    message.warning('请先选择流程')
    return
  }
  const confirmed = await confirmDiscardLocalChanges('刷新将覆盖当前未保存的修改，是否继续？')
  if (!confirmed) return
  await loadFlowDraft(flowId.value)
  message.success('草稿已刷新')
}

const handleSaveDraft = async () => {
  clearAutoSaveTimer()
  await performSave()
}

const handlePublish = () => {
  if (!flowId.value) {
    message.warning('请先选择流程')
    return
  }
  publishModalVisible.value = true
  publishFormRef.value?.restoreValidation()
}

const handleAddNode = (type: FlowNodeConfig['type']) => {
  store.addNode(type)
}

const handleUpdateNode = (payload: { key: string; patch: Partial<FlowNodeConfig> }) => {
  store.updateNode(payload.key, payload.patch)
}

const handleUpdatePosition = (payload: { key: string; position: FlowNodePosition }) => {
  store.updateNodePosition(payload.key, payload.position)
}

const handleSelectRoute = (index: number) => {
  store.selectRouteByIndex(index)
}

const handleAddRoute = () => {
  // 默认从当前选中的节点出发，目标节点也是当前节点
  const fromKey = store.selectedNodeKey
  if (!fromKey) {
    message.warning('请先选择一个节点作为路由起点')
    return
  }

  // 计算优先级（取最大优先级+1）
  const maxPriority = store.routes.reduce((max, r) => Math.max(max, r.priority), 0)

  // 默认来源和目标都是当前节点，用户可以在路由属性中修改
  store.addRoute({
    from_node_key: fromKey,
    to_node_key: fromKey,
    is_default: false,
    priority: maxPriority + 1,
    condition: null,
  })

  message.success('已创建新路由，请在右侧属性面板修改目标节点')
}

const handleDeleteRoute = (index: number) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这条路由吗？此操作无法撤销。',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => {
      store.removeRoute(index)
      message.success('路由已删除')
    }
  })
}

const handleUpdateRoute = (payload: { index: number; patch: Partial<FlowRouteConfig> }) => {
  store.updateRoute(payload.index, payload.patch)
}

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  if (store.dirty) {
    event.preventDefault()
    event.returnValue = ''
  }
}

const returnToHome = async () => {
  const confirmed = await confirmDiscardLocalChanges('返回首页将丢失未保存的修改，是否继续？')
  if (!confirmed) return
  router.push('/')
}

const toggleAutoSave = (value: boolean) => {
  autoSaveEnabled.value = value
  if (!value) {
    clearAutoSaveTimer()
  } else if (store.dirty) {
    scheduleAutoSave()
  }
}

const handleAutoSaveDelayChange = (value: number) => {
  autoSaveDelay.value = value
  if (store.dirty && autoSaveEnabled.value) {
    scheduleAutoSave()
  }
}

const closePublishModal = () => {
  publishModalVisible.value = false
}

const resetPublishForm = () => {
  publishForm.value = {
    versionTag: '',
    changelog: ''
  }
}

const handleSubmitPublish = async () => {
  if (!flowId.value) {
    message.warning('请先选择流程')
    return
  }
  try {
    await publishFormRef.value?.validate()
  } catch {
    return
  }
  try {
    await store.publishCurrentDraft({
      changelog: publishForm.value.changelog.trim(),
      versionTag: publishForm.value.versionTag.trim() || undefined
    })
    message.success('流程发布成功')
    notification.success({
      title: '流程发布成功',
      content: `最新快照 ID：${store.lastSnapshotId ?? '-'}，版本：v${store.version}`,
      duration: 4000
    })
    closePublishModal()
    resetPublishForm()
  } catch (error) {
    // 处理业务错误
    if (error instanceof Error) {
      const errorMsg = error.message
      
      // 检查是否为校验错误
      if (errorMsg.includes('流程') || errorMsg.includes('节点') || errorMsg.includes('边') || errorMsg.includes('分支') || errorMsg.includes('审批') || errorMsg.includes('可达') || errorMsg.includes('循环')) {
        dialog.error({
          title: '流程校验失败',
          content: errorMsg,
          positiveText: '确定',
          onPositiveClick: () => {
            // 尝试高亮失败的节点（如果错误信息中包含节点ID）
            const nodeIdMatch = errorMsg.match(/节点[：:]\s*(\w+)/)
            if (nodeIdMatch) {
              const nodeId = nodeIdMatch[1]
              store.selectNodeByKey(nodeId)
            }
          }
        })
      } 
      // 检查是否为权限错误
      else if (errorMsg.includes('权限') || errorMsg.includes('创建者')) {
        router.push('/403')
      } 
      // 其他错误
      else {
        message.error(errorMsg)
      }
    } else {
      message.error(resolveErrorMessage(error, '发布失败'))
    }
  }
}

watch(
  () => store.dirty,
  dirty => {
    if (dirty) {
      scheduleAutoSave()
    } else {
      clearAutoSaveTimer()
    }
  }
)

watch(
  () => [store.loading, store.saving, store.publishing],
  ([loading, saving, publishing]) => {
    if (loading || saving || publishing) {
      clearAutoSaveTimer()
    } else if (store.dirty) {
      scheduleAutoSave()
    }
  },
  { deep: true }
)

watch(
  () => flowId.value,
  (id) => {
    if (typeof id === 'number') {
      loadFlowDraft(id)
    } else {
      message.warning('未检测到流程 ID')
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  clearAutoSaveTimer()
})

onBeforeRouteLeave(async () => {
  const confirmed = await confirmDiscardLocalChanges('离开页面将失去未保存的修改，是否继续？')
  return confirmed
})
</script>

<style scoped>
.flow-config-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100vh;
  overflow: hidden;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title {
  font-size: 20px;
  font-weight: 600;
}

.meta {
  margin-top: 4px;
  color: #6b7385;
  display: flex;
  gap: 12px;
  font-size: 12px;
  flex-wrap: wrap;
}

.meta .dirty {
  color: #d03050;
}

.config-layout {
  display: grid;
  grid-template-columns: 240px 1fr 320px;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.sidebar-left {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(15, 22, 36, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.sidebar-left .divider {
  height: 1px;
  background: #e0e5ec;
  margin: 8px 0;
}

.sidebar-right {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(15, 22, 36, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-right-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  background: #f9fbfc;
  border-radius: 10px;
  padding: 12px;
  box-shadow: inset 0 0 0 1px rgba(24, 160, 88, 0.05);
  flex-shrink: 0;
}

.autosave-control {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7385;
}

.autosave-delay {
  min-width: 100px;
}

.autosave {
  color: #2080f0;
  font-weight: 600;
}

.publish-modal :deep(.n-card__content) {
  padding-top: 0;
}

.publish-tip {
  margin-bottom: 12px;
}

.canvas-area {
  background: #f6fbf8;
  border-radius: 12px;
  padding: 12px;
  box-shadow: inset 0 0 0 1px rgba(24, 160, 88, 0.08);
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.empty-state {
  padding: 48px 0;
}

.version-info {
  display: inline-flex;
  align-items: center;
}

.version-popover {
  min-width: 280px;
  max-width: 360px;
}

.snapshot-list {
  margin-top: 8px;
}

.snapshot-list-title {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 8px;
}

.snapshot-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.snapshot-item:last-child {
  border-bottom: none;
}

.snapshot-tag {
  font-size: 12px;
  font-weight: 500;
  color: #3b82f6;
}

.snapshot-time {
  font-size: 11px;
  color: #9ca3af;
}

.snapshot-more {
  font-size: 11px;
  color: #9ca3af;
  text-align: center;
  padding-top: 8px;
}
</style>
