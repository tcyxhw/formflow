<template>
    <div class="logic-rule-editor">
      <!-- 规则列表 -->
      <div class="rules-sidebar">
        <div class="sidebar-header">
          <h4 class="sidebar-title">规则列表</h4>
          <n-button
            size="small"
            type="primary"
            @click="addRule"
          >
            <template #icon>
              <Icon icon="carbon:add" />
            </template>
            新建规则
          </n-button>
        </div>
        
        <n-scrollbar class="rules-list">
          <div class="list-content">
            <div
              v-for="(rule, index) in localRules"
              :key="rule.id"
              class="rule-card"
              :class="{ 'is-active': selectedRuleIndex === index }"
              @click="selectRule(index)"
            >
              <div class="rule-header">
                <n-switch
                  v-model:value="rule.enabled"
                  size="small"
                  @click.stop
                  @update:value="handleUpdate"
                />
                <span class="rule-name">{{ rule.name || `规则 ${index + 1}` }}</span>
                <n-button
                  size="tiny"
                  quaternary
                  circle
                  @click.stop="removeRule(index)"
                >
                  <template #icon>
                    <Icon icon="carbon:trash-can" />
                  </template>
                </n-button>
              </div>
              
              <div class="rule-summary">
                <div class="summary-item">
                  <Icon icon="carbon:touch-1" />
                  <span>{{ rule.trigger.fields.length }} 个触发字段</span>
                </div>
                <div class="summary-item">
                  <Icon icon="carbon:condition-point" />
                  <span>{{ rule.conditions.length }} 个条件</span>
                </div>
                <div class="summary-item">
                  <Icon icon="carbon:flash" />
                  <span>{{ rule.actions.length }} 个动作</span>
                </div>
              </div>
            </div>
            
            <div v-if="localRules.length === 0" class="empty-rules">
              <Icon icon="carbon:rule" class="empty-icon" />
              <p class="empty-text">暂无规则</p>
              <p class="empty-hint">点击上方按钮创建规则</p>
            </div>
          </div>
        </n-scrollbar>
      </div>
      
      <!-- 规则编辑 -->
      <div v-if="selectedRule" class="rule-editor">
        <n-scrollbar style="height: 100%">
          <div class="editor-content">
            <n-form :model="selectedRule" label-placement="top" size="medium">
              
              <!-- 规则名称 -->
              <n-form-item label="规则名称">
                <n-input
                  v-model:value="selectedRule.name"
                  placeholder="为规则起一个易于理解的名称"
                  clearable
                  @blur="handleUpdate"
                >
                  <template #prefix>
                    <Icon icon="carbon:text-annotation-toggle" />
                  </template>
                </n-input>
              </n-form-item>
              
              <!-- 触发器 -->
              <n-divider title-placement="left">
                <div class="section-title">
                  <Icon icon="carbon:touch-1" />
                  <span>触发器</span>
                </div>
              </n-divider>
              
              <n-form-item label="触发时机">
                <n-select
                  v-model:value="selectedRule.trigger.type"
                  :options="triggerTypeOptions"
                  @update:value="handleUpdate"
                />
              </n-form-item>
              
              <n-form-item label="监听字段" required>
                <n-select
                  v-model:value="selectedRule.trigger.fields"
                  multiple
                  :options="fieldOptions"
                  placeholder="选择要监听的字段"
                  :max-tag-count="3"
                  @update:value="handleUpdate"
                />
                <template #feedback>
                  <span class="field-hint">当这些字段的值发生变化时触发规则</span>
                </template>
              </n-form-item>
              
              <!-- 条件 -->
              <n-divider title-placement="left">
                <div class="section-title">
                  <Icon icon="carbon:condition-point" />
                  <span>条件</span>
                </div>
              </n-divider>
              
              <n-form-item v-if="selectedRule.conditions.length > 1" label="条件组合">
                <n-radio-group
                  v-model:value="selectedRule.conditionLogic"
                  @update:value="handleUpdate"
                >
                  <n-space :size="12">
                    <n-radio value="AND">
                      <span class="radio-text">全部满足 (AND)</span>
                    </n-radio>
                    <n-radio value="OR">
                      <span class="radio-text">任一满足 (OR)</span>
                    </n-radio>
                  </n-space>
                </n-radio-group>
              </n-form-item>
              
              <div class="conditions-list">
                <div
                  v-for="(condition, index) in selectedRule.conditions"
                  :key="index"
                  class="condition-item"
                >
                  <div class="condition-header">
                    <span class="condition-label">条件 {{ index + 1 }}</span>
                    <n-button
                      size="tiny"
                      quaternary
                      circle
                      @click="removeCondition(index)"
                    >
                      <template #icon>
                        <Icon icon="carbon:close" />
                      </template>
                    </n-button>
                  </div>
                  
                  <n-space vertical :size="12">
                    <n-select
                      v-model:value="condition.field"
                      :options="fieldOptions"
                      placeholder="选择字段"
                      @update:value="handleUpdate"
                    />
                    
                    <n-select
                      v-model:value="condition.operator"
                      :options="operatorOptions"
                      placeholder="选择运算符"
                      @update:value="handleUpdate"
                    />
                    
                    <n-input
                      v-model:value="condition.value"
                      placeholder="输入比较值"
                      @blur="handleUpdate"
                    />
                  </n-space>
                </div>
                
                <n-button
                  size="small"
                  dashed
                  block
                  @click="addCondition"
                >
                  <template #icon>
                    <Icon icon="carbon:add" />
                  </template>
                  添加条件
                </n-button>
              </div>
              
              <!-- 动作 -->
              <n-divider title-placement="left">
                <div class="section-title">
                  <Icon icon="carbon:flash" />
                  <span>动作</span>
                </div>
              </n-divider>
              
              <div class="actions-list">
                <div
                  v-for="(action, index) in selectedRule.actions"
                  :key="index"
                  class="action-item"
                >
                  <div class="action-header">
                    <span class="action-label">动作 {{ index + 1 }}</span>
                    <n-button
                      size="tiny"
                      quaternary
                      circle
                      @click="removeAction(index)"
                    >
                      <template #icon>
                        <Icon icon="carbon:close" />
                      </template>
                    </n-button>
                  </div>
                  
                  <n-space vertical :size="12">
                    <n-select
                      v-model:value="action.type"
                      :options="actionTypeOptions"
                      placeholder="选择动作类型"
                      @update:value="handleUpdate"
                    />
                    
                    <n-select
                      v-model:value="action.target"
                      :options="fieldOptions"
                      placeholder="选择目标字段"
                      @update:value="handleUpdate"
                    />
                  </n-space>
                </div>
                
                <n-button
                  size="small"
                  dashed
                  block
                  @click="addAction"
                >
                  <template #icon>
                    <Icon icon="carbon:add" />
                  </template>
                  添加动作
                </n-button>
              </div>
              
            </n-form>
          </div>
        </n-scrollbar>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="editor-empty">
        <Icon icon="carbon:rule" class="empty-icon" />
        <p class="empty-text">请选择或创建一个规则</p>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  import { Icon } from '@iconify/vue'
  import type { LogicRule, LogicCondition, LogicAction } from '@/types/logic'
  import { ConditionOperator, ActionType } from '@/types/logic'
  import type { FormField } from '@/types/field'
  import { generateRuleId } from '@/utils/idGenerator'
  
  interface Props {
    rules: LogicRule[]
    fields: FormField[]
  }
  
  const props = defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update:rules', rules: LogicRule[]): void
  }>()
  
  const localRules = ref<LogicRule[]>([...props.rules])
  const selectedRuleIndex = ref<number>()
  
  watch(
    () => props.rules,
    (newRules) => {
      localRules.value = [...newRules]
    },
    { deep: true }
  )
  
  const selectedRule = computed(() => {
    return selectedRuleIndex.value !== undefined
      ? localRules.value[selectedRuleIndex.value]
      : undefined
  })
  
  // 字段选项
  const fieldOptions = computed(() => {
    return props.fields.map(f => ({
      label: f.label,
      value: f.id,
    }))
  })
  
  // 触发类型选项
  const triggerTypeOptions = [
    { label: '值改变时', value: 'change' },
    { label: '失去焦点时', value: 'blur' },
    { label: '获得焦点时', value: 'focus' },
    { label: '表单加载时', value: 'load' },
  ]
  
  // 运算符选项
  const operatorOptions = [
    { label: '等于', value: ConditionOperator.EQUALS },
    { label: '不等于', value: ConditionOperator.NOT_EQUALS },
    { label: '大于', value: ConditionOperator.GREATER_THAN },
    { label: '大于等于', value: ConditionOperator.GREATER_OR_EQUAL },
    { label: '小于', value: ConditionOperator.LESS_THAN },
    { label: '小于等于', value: ConditionOperator.LESS_OR_EQUAL },
    { label: '包含', value: ConditionOperator.CONTAINS },
    { label: '不包含', value: ConditionOperator.NOT_CONTAINS },
    { label: '为空', value: ConditionOperator.IS_EMPTY },
    { label: '非空', value: ConditionOperator.IS_NOT_EMPTY },
  ]
  
  // 动作类型选项
  const actionTypeOptions = [
    { label: '显示', value: ActionType.SHOW },
    { label: '隐藏', value: ActionType.HIDE },
    { label: '启用', value: ActionType.ENABLE },
    { label: '禁用', value: ActionType.DISABLE },
    { label: '设为必填', value: ActionType.SET_REQUIRED },
    { label: '设为非必填', value: ActionType.SET_OPTIONAL },
    { label: '设置值', value: ActionType.SET_VALUE },
    { label: '清空值', value: ActionType.CLEAR_VALUE },
  ]
  
  // 添加规则
  const addRule = () => {
    const newRule: LogicRule = {
      id: generateRuleId(),
      name: '',
      enabled: true,
      trigger: {
        type: 'change',
        fields: [],
      },
      conditions: [],
      conditionLogic: 'AND',
      actions: [],
    }
    
    localRules.value.push(newRule)
    selectedRuleIndex.value = localRules.value.length - 1
    handleUpdate()
  }
  
  // 移除规则
  const removeRule = (index: number) => {
    localRules.value.splice(index, 1)
    if (selectedRuleIndex.value === index) {
      selectedRuleIndex.value = undefined
    }
    handleUpdate()
  }
  
  // 选择规则
  const selectRule = (index: number) => {
    selectedRuleIndex.value = index
  }
  
  // 添加条件
  const addCondition = () => {
    if (selectedRule.value) {
      const newCondition: LogicCondition = {
        field: '',
        operator: ConditionOperator.EQUALS,
        value: '',
        valueType: 'fixed',
      }
      selectedRule.value.conditions.push(newCondition)
      handleUpdate()
    }
  }
  
  // 移除条件
  const removeCondition = (index: number) => {
    if (selectedRule.value) {
      selectedRule.value.conditions.splice(index, 1)
      handleUpdate()
    }
  }
  
  // 添加动作
  const addAction = () => {
    if (selectedRule.value) {
      const newAction: LogicAction = {
        type: ActionType.SHOW,
        target: '',
      }
      selectedRule.value.actions.push(newAction)
      handleUpdate()
    }
  }
  
  // 移除动作
  const removeAction = (index: number) => {
    if (selectedRule.value) {
      selectedRule.value.actions.splice(index, 1)
      handleUpdate()
    }
  }
  
  // 更新
  const handleUpdate = () => {
    emit('update:rules', [...localRules.value])
  }
  </script>
  
  <style scoped lang="scss">
  .logic-rule-editor {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 0;
    height: calc(100vh - 200px);
    background: var(--n-color);
  }
  
  .rules-sidebar {
    display: flex;
    flex-direction: column;
    background: var(--n-color-target);
    border-right: 1px solid var(--n-border-color);
  }
  
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--n-border-color);
    
    .sidebar-title {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--n-text-color-1);
    }
  }
  
  .rules-list {
    flex: 1;
  }
  
  .list-content {
    padding: 12px;
  }
  
  .rule-card {
    padding: 12px;
    margin-bottom: 8px;
    background: var(--n-color);
    border: 2px solid var(--n-border-color);
    border-radius: 8px;
    cursor: pointer;
    transition: all 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
    
    &:hover {
      border-color: var(--n-border-color-hover);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    &.is-active {
      border-color: var(--n-color-target);
      background: var(--n-color-target);
      box-shadow: 0 0 0 3px rgba(24, 160, 88, 0.1);
    }
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .rule-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    
    .rule-name {
      flex: 1;
      font-size: 14px;
      font-weight: 500;
      color: var(--n-text-color-1);
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  
  .rule-summary {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .summary-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--n-text-color-3);
    
    svg {
      font-size: 14px;
      flex-shrink: 0;
    }
  }
  
  .empty-rules {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
    text-align: center;
    
    .empty-icon {
      font-size: 48px;
      color: var(--n-text-color-disabled);
      margin-bottom: 16px;
    }
    
    .empty-text {
      margin: 0 0 4px;
      font-size: 14px;
      color: var(--n-text-color-2);
    }
    
    .empty-hint {
      margin: 0;
      font-size: 12px;
      color: var(--n-text-color-3);
    }
  }
  
  .rule-editor {
    height: 100%;
    background: var(--n-card-color);
  }
  
  .editor-content {
    padding: 24px;
    
    :deep(.n-form-item) {
      margin-bottom: 24px;
    }
  }
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--n-text-color-3);
    
    svg {
      font-size: 14px;
    }
  }
  
  .field-hint {
    font-size: 12px;
    color: var(--n-text-color-3);
    line-height: 1.5;
  }
  
  .radio-text {
    font-size: 14px;
  }
  
  .conditions-list,
  .actions-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .condition-item,
  .action-item {
    padding: 16px;
    background: var(--n-color-target);
    border: 1px solid var(--n-border-color);
    border-radius: 8px;
  }
  
  .condition-header,
  .action-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  
  .condition-label,
  .action-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--n-text-color-2);
  }
  
  .editor-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    background: var(--n-card-color);
    
    .empty-icon {
      font-size: 64px;
      color: var(--n-text-color-disabled);
      margin-bottom: 16px;
    }
    
    .empty-text {
      margin: 0;
      font-size: 14px;
      color: var(--n-text-color-3);
    }
  }
  
  /* 响应式 */
  @media (max-width: 1024px) {
    .logic-rule-editor {
      grid-template-columns: 280px 1fr;
    }
  }
  
  @media (max-width: 768px) {
    .logic-rule-editor {
      grid-template-columns: 1fr;
      
      .rules-sidebar {
        display: none;
      }
    }
  }
  
  /* 运动减弱支持 */
  @media (prefers-reduced-motion: reduce) {
    .rule-card {
      transition: none;
    }
  }
  </style>