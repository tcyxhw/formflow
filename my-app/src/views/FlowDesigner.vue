<template>
  <div class="flow-designer-container">
    <!-- 头部工具栏 -->
    <div class="designer-header">
      <div class="header-left">
        <n-button text @click="goBack">
          <template #icon>
            <n-icon><ArrowLeft /></n-icon>
          </template>
          返回
        </n-button>
        <div class="flow-title">
          <h1>{{ store.flowName }}</h1>
          <span class="version-tag">v{{ store.version }}</span>
        </div>
      </div>

      <div class="header-right">
        <div class="status-indicator">
          <span v-if="store.dirty" class="status-unsaved">
            <n-icon size="16"><Circle /></n-icon>
            未保存
          </span>
          <span v-else class="status-saved">
            <n-icon size="16"><CheckCircle /></n-icon>
            已保存
          </span>
        </div>

        <n-button-group>
          <n-button
            type="primary"
            :loading="store.saving"
            @click="handleSaveDraft"
          >
            <template #icon>
              <n-icon><Save /></n-icon>
            </template>
            保存草稿
          </n-button>

          <n-button
            type="success"
            :loading="store.publishing"
            @click="showPublishDialog = true"
          >
            <template #icon>
              <n-icon><Upload /></n-icon>
            </template>
            发布流程
          </n-button>
        </n-button-group>
      </div>
    </div>

    <!-- 主体布局 -->
    <div class="designer-body">
      <!-- 左侧：节点调色板 -->
      <div class="designer-sidebar left-sidebar">
        <FlowNodePalette />
      </div>

      <!-- 中间：画布 -->
      <div class="designer-canvas-wrapper">
        <FlowCanvas
          :nodes="store.nodes"
          :routes="store.routes"
          :nodes-graph="store.nodesGraph"
          :selected-node-key="store.selectedNodeKey"
          :selected-node-keys="store.selectedNodeKeys"
          :selected-route-index="store.selectedRouteIndex"
          @select-node="handleSelectNode"
          @select-route="handleSelectRoute"
          @update-position="handleUpdatePosition"
          @add-route="handleAddRoute"
          @delete-node="handleDeleteNode"
          @delete-route="handleDeleteRoute"
          @undo="handleUndo"
          @redo="handleRedo"
        />
      </div>

      <!-- 右侧：编辑器面板 -->
      <div class="designer-sidebar right-sidebar">
        <div class="editor-tabs">
          <div
            class="tab-button"
            :class="{ active: activeTab === 'node' }"
            @click="activeTab = 'node'"
          >
            节点编辑
          </div>
          <div
            class="tab-button"
            :class="{ active: activeTab === 'route' }"
            @click="activeTab = 'route'"
          >
            路由编辑
          </div>
        </div>

        <div class="editor-content">
          <!-- 节点编辑器 -->
          <div v-show="activeTab === 'node'" class="editor-panel">
            <FlowNodeEditor
              :node="store.currentNode"
              :all-nodes="store.nodes"
              :form-schema="formSchema"
              :form-id="formId"
              @update-node="handleUpdateNode"
            />
          </div>

          <!-- 路由编辑器 -->
          <div v-show="activeTab === 'route'" class="editor-panel">
            <FlowRouteEditor
              :route="store.currentRoute"
              :all-nodes="store.nodes"
              :form-schema="formSchema"
              :form-id="formId"
              @update-route="handleUpdateRoute"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 发布对话框 -->
    <n-modal
      v-model:show="showPublishDialog"
      title="发布流程"
      preset="dialog"
      type="info"
      positive-text="发布"
      negative-text="取消"
      :loading="store.publishing"
      @positive="handlePublish"
      @negative="showPublishDialog = false"
    >
      <div class="publish-dialog-content">
        <n-form label-placement="left" label-width="80">
          <n-form-item label="版本标签">
            <n-input
              v-model:value="publishVersionTag"
              placeholder="例如：v1.0.0"
            />
          </n-form-item>

          <n-form-item label="变更说明">
            <n-input
              v-model:value="publishChangelog"
              type="textarea"
              placeholder="描述此版本的主要变更"
              :rows="4"
            />
          </n-form-item>
        </n-form>

        <n-alert type="warning" style="margin-top: 16px">
          发布后，此流程版本将被锁定，无法再进行编辑。请确保所有配置都已完成。
        </n-alert>
      </div>
    </n-modal>

    <!-- 保存成功提示 -->
    <n-message-provider>
      <!-- 消息容器 -->
    </n-message-provider>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  NButton,
  NButtonGroup,
  NIcon,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NAlert,
  NMessageProvider
} from 'naive-ui'
import {
  ArrowLeft,
  Save,
  Upload,
  Circle,
  CheckCircle
} from '@vicons/antd'
import FlowCanvas from '@/components/flow-designer/FlowCanvas.vue'
import FlowNodePalette from '@/components/flow-designer/FlowNodePalette.vue'
import FlowNodeEditor from '@/components/flow-designer/FlowNodeEditor.vue'
import FlowRouteEditor from '@/components/flow-designer/FlowRouteEditor.vue'
import { useFlowDraftStore } from '@/stores/flowDraft'
import type { FormSchema } from '@/types/schema'
import type { FlowNodeConfig, FlowRouteConfig, FlowNodePosition } from '@/types/flow'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const store = useFlowDraftStore()

// 状态
const activeTab = ref<'node' | 'route'>('node')
const showPublishDialog = ref(false)
const publishVersionTag = ref('')
const publishChangelog = ref('')
const formSchema = ref<FormSchema | undefined>()
const formId = ref<number | undefined>()

// 计算属性
const isLoading = computed(() => store.loading)

// 生命周期
onMounted(async () => {
  const flowDefinitionId = route.params.flowDefinitionId as string
  if (!flowDefinitionId) {
    message.error('缺少流程定义 ID')
    goBack()
    return
  }

  try {
    const result = await store.loadDefinition(parseInt(flowDefinitionId))
    // 从流程定义中获取表单信息
    if (result.detail.definition.form_id) {
      formId.value = result.detail.definition.form_id
      // 这里可以加载表单 schema，如果需要的话
    }
  } catch (error) {
    message.error('加载流程定义失败')
    console.error(error)
    goBack()
  }
})

// 事件处理
const handleSelectNode = (nodeKey: string, multiSelect?: boolean) => {
  if (multiSelect) {
    store.toggleNodeSelection(nodeKey, true)
  } else {
    store.toggleNodeSelection(nodeKey, false)
  }
  activeTab.value = 'node'
}

const handleSelectRoute = (index: number) => {
  store.selectRouteByIndex(index)
  activeTab.value = 'route'
}

const handleUpdatePosition = (payload: { key: string; position: FlowNodePosition }) => {
  store.updateNodePosition(payload.key, payload.position)
}

const handleAddRoute = (payload: { from_node_key: string; to_node_key: string }) => {
  try {
    store.addRoute({
      from_node_key: payload.from_node_key,
      to_node_key: payload.to_node_key,
      priority: 1,
      is_default: false
    })
    message.success('路由已添加')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '添加路由失败')
  }
}

const handleDeleteNode = (nodeKey: string) => {
  const node = store.nodes.find(n => (n.id?.toString() ?? n.temp_id) === nodeKey)
  if (!node) return

  // 检查是否为开始或结束节点
  if (node.type === 'start' || node.type === 'end') {
    message.warning('不能删除开始或结束节点')
    return
  }

  store.removeNode(nodeKey)
  message.success('节点已删除')
}

const handleDeleteRoute = (index: number) => {
  store.removeRoute(index)
  message.success('路由已删除')
}

const handleUpdateNode = (payload: { key: string; patch: Partial<FlowNodeConfig> }) => {
  try {
    store.updateNode(payload.key, payload.patch)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '更新节点失败')
  }
}

const handleUpdateRoute = (payload: { key: string; patch: Partial<FlowRouteConfig> }) => {
  const index = store.routes.findIndex(
    r => (r.id?.toString() ?? r.temp_id) === payload.key
  )
  if (index !== -1) {
    store.updateRoute(index, payload.patch)
  }
}

const handleUndo = () => {
  if (store.canUndo) {
    store.undo()
    message.info('已撤销')
  }
}

const handleRedo = () => {
  if (store.canRedo) {
    store.redo()
    message.info('已重做')
  }
}

const handleSaveDraft = async () => {
  try {
    await store.saveDraftRemote()
    message.success('草稿已保存')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '保存失败')
    console.error(error)
  }
}

const handlePublish = async () => {
  try {
    await store.publishCurrentDraft({
      versionTag: publishVersionTag.value || undefined,
      changelog: publishChangelog.value || undefined
    })
    message.success('流程已发布')
    showPublishDialog.value = false
    publishVersionTag.value = ''
    publishChangelog.value = ''
  } catch (error) {
    message.error(error instanceof Error ? error.message : '发布失败')
    console.error(error)
  }
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.flow-designer-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.designer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: white;
  border-bottom: 1px solid #e0e5ec;
  box-shadow: 0 2px 8px rgba(15, 22, 36, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.flow-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.flow-title h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.version-tag {
  font-size: 12px;
  color: #6b7385;
  background-color: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-unsaved {
  color: #f59e0b;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-saved {
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 4px;
}

.designer-body {
  display: flex;
  flex: 1;
  gap: 0;
  overflow: hidden;
}

.designer-sidebar {
  background-color: white;
  border: 1px solid #e0e5ec;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.left-sidebar {
  width: 240px;
  border-right: 1px solid #e0e5ec;
}

.right-sidebar {
  width: 320px;
  border-left: 1px solid #e0e5ec;
}

.designer-canvas-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #fafbfc;
}

.editor-tabs {
  display: flex;
  border-bottom: 1px solid #e0e5ec;
  background-color: #f9fbfc;
}

.tab-button {
  flex: 1;
  padding: 12px 16px;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: #6b7385;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.tab-button:hover {
  color: #1f2937;
  background-color: #f3f4f6;
}

.tab-button.active {
  color: #18a058;
  border-bottom-color: #18a058;
  background-color: white;
}

.editor-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.editor-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.publish-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .left-sidebar {
    width: 200px;
  }

  .right-sidebar {
    width: 280px;
  }
}

@media (max-width: 1200px) {
  .designer-header {
    padding: 12px 16px;
  }

  .flow-title h1 {
    font-size: 16px;
  }

  .left-sidebar {
    width: 180px;
  }

  .right-sidebar {
    width: 260px;
  }
}

@media (max-width: 768px) {
  .designer-body {
    flex-direction: column;
  }

  .left-sidebar,
  .right-sidebar {
    width: 100%;
    height: 200px;
    border: none;
    border-top: 1px solid #e0e5ec;
  }

  .designer-canvas-wrapper {
    order: 2;
  }

  .left-sidebar {
    order: 1;
  }

  .right-sidebar {
    order: 3;
  }
}
</style>
