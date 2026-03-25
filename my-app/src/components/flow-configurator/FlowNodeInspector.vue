<template>
  <div class="inspector">
    <div class="inspector-header">
      <div class="title">节点属性</div>
      <div class="subtitle">配置审批策略与自动化参数</div>
    </div>

    <div v-if="node" class="inspector-body">
      <n-form label-placement="left" label-width="88" size="small">
        <n-form-item label="节点名称">
          <n-input
            :value="node.name"
            placeholder="请输入节点名称"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ name: val })"
          />
        </n-form-item>

        <n-form-item label="节点类型">
          <n-select
            :value="node.type"
            :options="nodeTypeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ type: val as FlowNodeType })"
          />
        </n-form-item>

        <!-- 开始/结束节点提示 -->
        <n-alert v-if="shouldShowBasicInfoHint(node.type)" type="info" :bordered="false">
          {{ node.type === 'start' ? '开始节点是流程的入口点，无需配置审批相关参数。' : '结束节点是流程的终点，无需配置审批相关参数。' }}
        </n-alert>

        <!-- 审批相关配置 -->
        <template v-if="shouldShowApprovalConfig(node.type)">
          <!-- 岗位选择（必选） -->
          <n-form-item label="审批岗位" required>
            <n-select
              :value="getPostId()"
              :options="positionOptions"
              :loading="loadingPositions"
              :disabled="disabled"
              filterable
              clearable
              placeholder="请选择岗位（必选）"
              @update:value="(val) => handlePostChange(val)"
            />
          </n-form-item>

          <!-- 部门选择（可选） -->
          <n-form-item label="指定部门">
            <n-select
              :value="getDepartmentId()"
              :options="departmentOptions"
              :loading="loadingDepartments"
              :disabled="disabled"
              filterable
              clearable
              placeholder="不指定则自动匹配"
              @update:value="(val) => handleDepartmentChange(val)"
            />
          </n-form-item>

          <!-- 匹配模式说明 -->
          <n-alert type="info" :bordered="false" style="margin-bottom: 12px;">
            <template #header>
              <span style="font-size: 12px;">匹配模式说明</span>
            </template>
            <div style="font-size: 12px; line-height: 1.6;">
              <p><strong>指定部门 + 岗位：</strong>在指定部门内查找该岗位的人（FIXED模式）</p>
              <p><strong>只选岗位：</strong>沿发起人部门链向上查找该岗位的人（ORG_CHAIN_UP模式）</p>
            </div>
          </n-alert>

          <n-form-item label="审批策略">
            <n-select
              :value="node.approve_policy"
              :options="approvePolicyOptions"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ approve_policy: val as FlowApprovePolicy })"
            />
          </n-form-item>

          <n-form-item v-if="node.approve_policy === 'percent'" label="通过阈值">
            <n-input-number
              :value="node.approve_threshold ?? 50"
              :min="1"
              :max="100"
              :disabled="disabled"
              suffix="%"
              @update:value="(val) => emitPatch({ approve_threshold: val ?? undefined })"
            />
          </n-form-item>

          <n-form-item label="SLA(小时)">
            <n-input-number
              :value="node.sla_hours ?? undefined"
              :min="1"
              :max="720"
              placeholder="可选"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ sla_hours: val ?? undefined })"
            />
          </n-form-item>

          <n-form-item label="允许代理">
            <n-switch
              :value="node.allow_delegate"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ allow_delegate: val })"
            />
          </n-form-item>

          <n-divider>驳回策略</n-divider>

          <n-form-item label="驳回策略">
            <n-select
              :value="node.reject_strategy"
              :options="rejectStrategyOptions"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ reject_strategy: val as RejectStrategy })"
            />
          </n-form-item>

          <n-divider>自动审批</n-divider>

          <n-form-item label="启用自动">
            <n-switch
              :value="node.auto_approve_enabled"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ auto_approve_enabled: val })"
            />
          </n-form-item>

          <!-- 自动通过条件配置 -->
          <div v-if="node.auto_approve_enabled" class="condition-config auto-approve">
            <div class="config-header">
              <span class="config-title">自动通过条件</span>
              <span class="condition-status" :class="{ 'is-configured': node.auto_approve_cond }">
                {{ node.auto_approve_cond ? '已配置条件' : '未配置' }}
              </span>
            </div>
            <div class="config-preview">
              <span v-if="node.auto_approve_cond" class="preview-text">
                {{ formatConditionPreview(node.auto_approve_cond) }}
              </span>
              <span v-else class="preview-empty">满足条件时自动通过审批</span>
            </div>
            <div class="config-actions">
              <n-button type="primary" size="small" :disabled="disabled" @click="openAutoApproveModal">
                {{ node.auto_approve_cond ? '编辑条件' : '添加条件' }}
              </n-button>
              <n-button
                v-if="node.auto_approve_cond"
                quaternary
                size="small"
                type="error"
                :disabled="disabled"
                @click="clearAutoApproveCondition"
              >
                清除
              </n-button>
            </div>
          </div>

          <!-- 自动驳回条件配置 -->
          <div v-if="node.auto_approve_enabled" class="condition-config auto-reject">
            <div class="config-header">
              <span class="config-title">自动驳回条件</span>
              <span class="condition-status" :class="{ 'is-configured': node.auto_reject_cond }">
                {{ node.auto_reject_cond ? '已配置条件' : '未配置' }}
              </span>
            </div>
            <div class="config-preview">
              <span v-if="node.auto_reject_cond" class="preview-text">
                {{ formatConditionPreview(node.auto_reject_cond) }}
              </span>
              <span v-else class="preview-empty">满足条件时自动驳回审批</span>
            </div>
            <div class="config-actions">
              <n-button type="error" size="small" :disabled="disabled" @click="openAutoRejectModal">
                {{ node.auto_reject_cond ? '编辑条件' : '添加条件' }}
              </n-button>
              <n-button
                v-if="node.auto_reject_cond"
                quaternary
                size="small"
                type="error"
                :disabled="disabled"
                @click="clearAutoRejectCondition"
              >
                清除
              </n-button>
            </div>
          </div>

          <!-- 提示信息 -->
          <n-alert v-if="node.auto_approve_enabled" type="info" :bordered="false" style="margin-top: 12px;">
            自动驳回条件优先于自动通过条件判断
          </n-alert>
        </template>

        <!-- 条件节点配置 -->
        <template v-if="shouldShowConditionConfig(node.type)">
          <n-divider>条件分支配置</n-divider>

          <div class="condition-config">
            <div class="config-header">
              <span class="config-title">条件分支配置</span>
              <span class="branch-count">当前有 {{ node.condition_branches?.branches.length ?? 0 }} 个分支</span>
            </div>
            <div class="config-actions">
              <n-button type="primary" size="small" :disabled="disabled" @click="openConditionModal">
                编辑条件
              </n-button>
            </div>
          </div>
        </template>
      </n-form>

      <!-- 归属路由区域 -->
      <div class="owned-routes-section">
        <div class="section-header">
          <span class="section-title">归属路由</span>
          <span class="section-count">{{ ownedRoutes.length }} 条</span>
        </div>
        <n-scrollbar v-if="ownedRoutes.length > 0" class="routes-scroll">
          <div class="routes-list">
            <div
              v-for="{ route, index } in ownedRoutes"
              :key="index"
              class="route-card"
              :class="{ active: index === selectedIndex }"
              @click="handleSelectRoute(index)"
            >
              <div class="route-header">
                <span class="route-number">{{ index + 1 }}</span>
                <span class="route-arrow">→</span>
                <span class="route-target">{{ getNodeName(route.to_node_key) }}</span>
              </div>
              <div class="route-meta">
                <span>优先级: {{ route.priority }}</span>
                <span v-if="route.condition">已配置条件</span>
                <span v-else>无条件</span>
              </div>
            </div>
          </div>
        </n-scrollbar>
        <n-empty v-else description="暂无归属路由" size="small" />
      </div>
    </div>

    <div v-else class="inspector-empty">
      <n-empty description="请选择画布中的节点" />
    </div>

    <!-- 条件分支编辑模态框 -->
    <n-modal
      v-model:show="showConditionModal"
      title="编辑条件表达式"
      preset="dialog"
      size="large"
      :mask-closable="false"
      @positive-click="saveCondition"
      @negative-click="cancelCondition"
    >
      <ConditionNodeEditor
        :model-value="editingConditionBranches"
        :all-nodes="allNodes"
        :form-schema="formSchema"
        :form-id="formId"
        :disabled="disabled"
        @update:model-value="(val) => (editingConditionBranches = val)"
      />
    </n-modal>

    <!-- 自动通过条件编辑模态框 -->
    <n-modal
      v-model:show="showAutoApproveModal"
      preset="card"
      :style="{ width: '80vw', maxWidth: '1200px' }"
      :mask-closable="false"
      :closable="false"
      :show-icon="false"
    >
      <template #header>
        <span>编辑自动通过条件</span>
      </template>
      <div class="modal-body-wrapper">
        <AutoConditionEditor
          v-model="editingAutoApproveCond"
          title="编辑自动通过条件"
          subtitle="配置表单字段的条件规则，满足条件时自动通过审批"
          :form-schema="formSchema"
          :form-id="formId"
          :disabled="disabled"
          @save="saveAutoApproveCondition"
          @cancel="cancelAutoApproveCondition"
        />
      </div>
    </n-modal>

    <!-- 自动驳回条件编辑模态框 -->
    <n-modal
      v-model:show="showAutoRejectModal"
      preset="card"
      :style="{ width: '80vw', maxWidth: '1200px' }"
      :mask-closable="false"
      :closable="false"
      :show-icon="false"
    >
      <template #header>
        <span>编辑自动驳回条件</span>
      </template>
      <div class="modal-body-wrapper">
        <AutoConditionEditor
          v-model="editingAutoRejectCond"
          title="编辑自动驳回条件"
          subtitle="配置表单字段的条件规则，满足条件时自动驳回审批"
          :form-schema="formSchema"
          :form-id="formId"
          :disabled="disabled"
          @save="saveAutoRejectCondition"
          @cancel="cancelAutoRejectCondition"
        />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ConditionNodeEditor from './ConditionNodeEditor.vue'
import AutoConditionEditor from './AutoConditionEditor.vue'
import { listUsers } from '@/api/user'
import { listRoles, listDepartments, listPositions, listGroups } from '@/api/admin'
import { conditionNodeToRouteRule, routeRuleToConditionNode } from '@/utils/conditionConverter'
import type {
  FlowApprovePolicy,
  FlowAssigneeType,
  FlowNodeConfig,
  FlowNodeType,
  FlowRouteConfig,
  RejectStrategy,
  ConditionBranchesConfig
} from '@/types/flow'
import type { FormSchema } from '@/types/schema'
import type { ConditionNode } from '@/types/condition'

interface Props {
  node?: FlowNodeConfig
  allNodes?: FlowNodeConfig[]
  routes?: FlowRouteConfig[]
  formSchema?: FormSchema
  formId?: number
  disabled?: boolean
  selectedIndex?: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update-node', payload: { key: string; patch: Partial<FlowNodeConfig> }): void
  (e: 'select-route', index: number): void
}>()

const showConditionModal = ref(false)
const editingConditionBranches = ref<ConditionBranchesConfig | null>(null)

const showAutoApproveModal = ref(false)
const showAutoRejectModal = ref(false)
const editingAutoApproveCond = ref<ConditionNode | null>(null)
const editingAutoRejectCond = ref<ConditionNode | null>(null)

const userOptions = ref<Array<{ label: string; value: number }>>([])
const roleOptions = ref<Array<{ label: string; value: number }>>([])
const departmentOptions = ref<Array<{ label: string; value: number }>>([])
const positionOptions = ref<Array<{ label: string; value: number }>>([])
const groupOptions = ref<Array<{ label: string; value: number }>>([])

const loadingUsers = ref(false)
const loadingRoles = ref(false)
const loadingDepartments = ref(false)
const loadingPositions = ref(false)
const loadingGroups = ref(false)

const nodeTypeOptions = computed(() => [
  { label: '开始', value: 'start' },
  { label: '人工审批', value: 'user' },
  { label: '条件分支', value: 'condition' },
  { label: '自动节点', value: 'auto' },
  { label: '结束', value: 'end' }
])

const approvePolicyOptions = computed(() => [
  { label: '任意一人', value: 'any' },
  { label: '全部同意', value: 'all' },
  { label: '自定义比例', value: 'percent' }
])

const rejectStrategyOptions = computed(() => [
  { label: '驳回到发起人', value: 'TO_START' },
  { label: '驳回到上一个审批节点', value: 'TO_PREVIOUS' }
])

const getPostId = (): number | undefined => {
  if (props.node?.assignee_type === 'department_post') {
    return props.node.assignee_value?.post_id as number | undefined
  }
  return undefined
}

const getDepartmentId = (): number | undefined => {
  if (props.node?.assignee_type === 'department_post') {
    return props.node.assignee_value?.department_id as number | undefined
  }
  return undefined
}

const handlePostChange = (postId: number | null) => {
  if (!postId) {
    emitPatch({ assignee_type: undefined, assignee_value: undefined })
    return
  }
  
  const currentDeptId = getDepartmentId()
  const assigneeValue: Record<string, unknown> = { post_id: postId }
  
  if (currentDeptId) {
    assigneeValue.department_id = currentDeptId
    assigneeValue.match_mode = 'FIXED'
  } else {
    assigneeValue.match_mode = 'ORG_CHAIN_UP'
  }
  
  emitPatch({
    assignee_type: 'department_post',
    assignee_value: assigneeValue
  })
}

const handleDepartmentChange = (deptId: number | null) => {
  const currentPostId = getPostId()
  if (!currentPostId) {
    return
  }
  
  const assigneeValue: Record<string, unknown> = { post_id: currentPostId }
  
  if (deptId) {
    assigneeValue.department_id = deptId
    assigneeValue.match_mode = 'FIXED'
  } else {
    assigneeValue.match_mode = 'ORG_CHAIN_UP'
  }
  
  emitPatch({
    assignee_type: 'department_post',
    assignee_value: assigneeValue
  })
}

const resolveNodeKey = (node: FlowNodeConfig): string | undefined => {
  return node.id?.toString() ?? node.temp_id ?? undefined
}

const emitPatch = (patch: Partial<FlowNodeConfig>) => {
  if (!props.node) return
  const key = resolveNodeKey(props.node)
  if (!key) return
  emit('update-node', { key, patch })
}

const shouldShowApprovalConfig = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'user' || nodeType === 'auto'
}

const shouldShowConditionConfig = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'condition'
}

const shouldShowBasicInfoHint = (nodeType: FlowNodeType): boolean => {
  return nodeType === 'start' || nodeType === 'end'
}

const ownedRoutes = computed(() => {
  if (!props.node || !props.routes) return []
  const nodeKey = resolveNodeKey(props.node)
  if (!nodeKey) return []
  return props.routes
    .map((route, index) => ({ route, index }))
    .filter(({ route }) => route.from_node_key === nodeKey)
})

const getNodeName = (key: string) => {
  if (!props.allNodes) return key
  const found = props.allNodes.find(node => node.id?.toString() === key || node.temp_id === key)
  return found?.name ?? key
}

const handleSelectRoute = (index: number) => {
  emit('select-route', index)
}

const openConditionModal = () => {
  if (!props.node) return
  editingConditionBranches.value = props.node.condition_branches ?? null
  showConditionModal.value = true
}

const saveCondition = () => {
  if (editingConditionBranches.value) {
    emitPatch({ condition_branches: editingConditionBranches.value })
  }
  showConditionModal.value = false
  editingConditionBranches.value = null
}

const cancelCondition = () => {
  editingConditionBranches.value = null
  showConditionModal.value = false
}

const openAutoApproveModal = () => {
  const routeRule = props.node?.auto_approve_cond ?? null
  editingAutoApproveCond.value = routeRuleToConditionNode(routeRule as any)
  showAutoApproveModal.value = true
}

const saveAutoApproveCondition = () => {
  const routeRule = conditionNodeToRouteRule(editingAutoApproveCond.value)
  emitPatch({ auto_approve_cond: routeRule as any })
  showAutoApproveModal.value = false
  editingAutoApproveCond.value = null
}

const cancelAutoApproveCondition = () => {
  showAutoApproveModal.value = false
  editingAutoApproveCond.value = null
}

const clearAutoApproveCondition = () => {
  emitPatch({ auto_approve_cond: null })
}

const openAutoRejectModal = () => {
  const routeRule = props.node?.auto_reject_cond ?? null
  editingAutoRejectCond.value = routeRuleToConditionNode(routeRule as any)
  showAutoRejectModal.value = true
}

const saveAutoRejectCondition = () => {
  const routeRule = conditionNodeToRouteRule(editingAutoRejectCond.value)
  emitPatch({ auto_reject_cond: routeRule as any })
  showAutoRejectModal.value = false
  editingAutoRejectCond.value = null
}

const cancelAutoRejectCondition = () => {
  showAutoRejectModal.value = false
  editingAutoRejectCond.value = null
}

const clearAutoRejectCondition = () => {
  emitPatch({ auto_reject_cond: null })
}

const formatConditionPreview = (condition: any): string => {
  if (!condition) return '未设置'
  
  if (condition.type === 'GROUP') {
    if (!condition.children || condition.children.length === 0) {
      return '未设置'
    }
    return `${condition.logic === 'AND' ? '全部满足' : '任意满足'} (${condition.children.length} 个条件)`
  }
  
  if (condition.type === 'RULE') {
    return `单条件: ${condition.fieldKey}`
  }
  
  if (condition.and || condition.or) {
    const logic = condition.and ? 'and' : 'or'
    const conditions = condition[logic]
    if (Array.isArray(conditions) && conditions.length > 0) {
      return `${logic === 'and' ? '全部满足' : '任意满足'} (${conditions.length} 个条件)`
    }
  }
  
  return '已设置条件'
}

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

const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await listGroups({ page: 1, size: 100 })
    groupOptions.value = res.data.items.map((group) => ({
      label: group.name,
      value: group.id
    }))
  } catch (error) {
    console.error('加载群组列表失败', error)
  } finally {
    loadingGroups.value = false
  }
}

const handleSearchUsers = (query: string) => {
  if (query) {
    loadUsers(query)
  }
}

watch(
  () => props.node?.type,
  (newType) => {
    if (newType === 'user' || newType === 'auto') {
      if (positionOptions.value.length === 0) {
        loadPositions()
      }
      if (departmentOptions.value.length === 0) {
        loadDepartments()
      }
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.inspector {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.inspector-header {
  margin-bottom: 12px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.subtitle {
  font-size: 12px;
  color: #6b7385;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.inspector-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.condition-config {
  padding: 16px;
  background: #f9fbfc;
  border-radius: 8px;
  border: 1px solid #e0e5ec;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.condition-config.auto-approve {
  background: #f0faf4;
  border-color: #d3e8e0;
}

.condition-config.auto-reject {
  background: #fff5f5;
  border-color: #f0d0d0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.branch-count {
  font-size: 13px;
  color: #6b7385;
}

.condition-status {
  font-size: 13px;
  color: #999;
  background: #f0f0f0;
  padding: 4px 12px;
  border-radius: 12px;
}

.condition-status.is-configured {
  color: #18a058;
  background: #e8f5e9;
}

.auto-reject .condition-status.is-configured {
  color: #d03050;
  background: #ffeaea;
}

.config-preview {
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e0e5ec;
  font-size: 14px;
  min-height: 44px;
  display: flex;
  align-items: center;
}

.preview-text {
  color: #1f2937;
  font-weight: 500;
}

.auto-approve .preview-text {
  color: #18a058;
}

.auto-reject .preview-text {
  color: #d03050;
}

.preview-empty {
  color: #999;
  font-style: italic;
}

.config-actions {
  display: flex;
  gap: 12px;
}

.owned-routes-section {
  margin-top: 16px;
  border-top: 1px solid #e0e5ec;
  padding-top: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.section-count {
  font-size: 12px;
  color: #6b7385;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 10px;
}

.routes-scroll {
  max-height: 200px;
}

.routes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-card {
  padding: 10px 12px;
  background: #f7f9fb;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.route-card:hover {
  background: #f0faf4;
}

.route-card.active {
  border-color: #18a058;
  background: #f0faf4;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.route-number {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #18a058;
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.route-arrow {
  color: #18a058;
  font-weight: 600;
}

.route-target {
  font-weight: 600;
  color: #1f2937;
}

.route-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7385;
  display: flex;
  gap: 12px;
}

/* 弹窗内容容器 */
.modal-body-wrapper {
  height: 65vh;
  overflow: hidden;
}
</style>
