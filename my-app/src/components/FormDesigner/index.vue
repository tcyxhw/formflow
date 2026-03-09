<!-- src/components/FormDesigner/index.vue -->
<template>
  <div class="form-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left">
        <n-button text @click="$router.back()">
          <template #icon>
            <n-icon><Icon icon="carbon:arrow-left" /></n-icon>
          </template>
          返回
        </n-button>
        
        <n-divider vertical />
        
        <n-input
          v-model:value="designerStore.formName"
          placeholder="请输入表单名称"
          style="width: 300px"
        />
        
        <n-tag :type="statusTagType" size="small" style="margin-left: 12px">
          {{ statusText }}
        </n-tag>

        <!-- AI 生成标识 -->
        <n-tag v-if="isAIGenerated" type="success" size="small" style="margin-left: 8px">
          <template #icon>
            <n-icon><Icon icon="carbon:watson-health-ai-results" /></n-icon>
          </template>
          AI 生成
        </n-tag>
      </div>
      
      <div class="header-right">
        <n-space>
          <n-button @click="handlePreview">
            <template #icon>
              <n-icon><Icon icon="carbon:view" /></n-icon>
            </template>
            预览
          </n-button>

          <n-button tertiary @click="openPermissionDrawer">
            <template #icon>
              <n-icon><Icon icon="carbon:locked" /></n-icon>
            </template>
            权限
          </n-button>

          <n-button @click="handleSave" :loading="saving">
            <template #icon>
              <n-icon><Icon icon="carbon:save" /></n-icon>
            </template>
            保存
          </n-button>
          
          <n-button
            v-if="canPublish"
            type="primary"
            @click="handlePublish"
            :loading="publishing"
          >
            <template #icon>
              <n-icon><Icon icon="carbon:rocket" /></n-icon>
            </template>
            发布
          </n-button>
        </n-space>
      </div>
    </div>
    
    <!-- 主体区域 -->
    <div class="designer-body">
      <!-- 左侧：组件库 -->
      <div class="designer-sidebar left">
        <ComponentLibrary @add-field="handleAddField" />
      </div>
      
      <!-- 中间：设计画布 -->
      <div class="designer-canvas">
        <DesignCanvas
          :fields="designerStore.fields"
          :selected-field-id="designerStore.selectedFieldId"
          @select-field="handleSelectField"
          @delete-field="handleDeleteField"
          @move-field="handleMoveField"
          @add-field="handleAddFieldDirect"
        />
      </div>
      
      <!-- 右侧：属性面板 -->
      <div class="designer-sidebar right">
        <PropertyPanel
          v-if="designerStore.selectedField"
          :field="designerStore.selectedField"
          :all-fields="designerStore.fields"
          @update="handleUpdateField"
        />
        <FormSettings
          v-else
          :config="formSettings"
          @update="handleUpdateSettings"
        />
      </div>
    </div>
    
    <!-- AI 助手 -->
    <AIAssistant @apply-config="handleApplyAIConfig" />

    <FormPermissionDrawer
      v-model:show="showPermissionDrawer"
      :form-id="designerStore.formId"
      :form-name="designerStore.formName"
    />

    <!-- 预览抽屉 -->
    <n-drawer v-model:show="showPreview" :width="800" placement="right">
      <n-drawer-content title="表单预览" closable>
        <FormPreview :config="designerStore.getFormConfig()" />
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { useFormDesignerStore } from '@/stores/formDesigner'
import { FormValidation } from '@/utils/formValidation'
import { FormStatus, AccessMode } from '@/types/form'
import type { FormField } from '@/types/field'
import type { FormConfig } from '@/types/form'
import type { AIFormGenerateResponse } from '@/types/ai'
import type { LogicSchema } from '@/types/logic'
import * as formApi from '@/api/form'
import ComponentLibrary from './ComponentLibrary.vue'
import DesignCanvas from './DesignCanvas.vue'
import PropertyPanel from './PropertyPanel/index.vue'
import FormSettings from './FormSettings.vue'
import FormPreview from './FormPreview.vue'
import AIAssistant from '@/components/FormDesigner/AIAssistant.vue'
import FormPermissionDrawer from '@/components/form/FormPermissionDrawer.vue'
import { ConfigTransfer } from '@/utils/configTransfer' 
import type { FormCreateRequest } from '@/types/form'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const designerStore = useFormDesignerStore()

const saving = ref(false)
const publishing = ref(false)
const showPreview = ref(false)
const showPermissionDrawer = ref(false)
const formStatus = ref<FormStatus>(FormStatus.DRAFT)
const isAIGenerated = ref(false)

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback

const formSettings = computed(() => ({
  name: designerStore.formName,
  category: designerStore.formCategory,
  accessMode: designerStore.accessMode,
  allowEdit: designerStore.allowEdit,
  maxEditCount: designerStore.maxEditCount,
  submitDeadline: designerStore.submitDeadline,
  uiSchema: designerStore.uiSchema,
}))

const statusTagType = computed(() => {
  switch (formStatus.value) {
    case FormStatus.PUBLISHED: return 'success'
    case FormStatus.ARCHIVED: return 'warning'
    default: return 'default'
  }
})

const statusText = computed(() => {
  switch (formStatus.value) {
    case FormStatus.PUBLISHED: return '已发布'
    case FormStatus.ARCHIVED: return '已归档'
    default: return '草稿'
  }
})

const canPublish = computed(() => {
  return formStatus.value === FormStatus.DRAFT || formStatus.value === FormStatus.PUBLISHED
})

const handleAddField = (fieldType: string) => {
  designerStore.addField(fieldType)
}

const handleAddFieldDirect = (field: FormField) => {
  designerStore.fields.push(field)
  designerStore.selectField(field.id)
}

const handleSelectField = (fieldId: string) => {
  designerStore.selectField(fieldId)
}

const handleDeleteField = (fieldId: string) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个字段吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => {
      designerStore.deleteField(fieldId)
      message.success('删除成功')
    },
  })
}

const handleMoveField = (fromIndex: number, toIndex: number) => {
  designerStore.moveField(fromIndex, toIndex)
}

const handleUpdateField = (updates: Partial<FormField>) => {
  if (designerStore.selectedFieldId) {
    designerStore.updateField(designerStore.selectedFieldId, updates)
  }
}

const handleUpdateSettings = (updates: Partial<FormConfig>) => {
  if (updates.category !== undefined) {
    designerStore.formCategory = updates.category
  }
  if (updates.accessMode !== undefined) {
    designerStore.accessMode = updates.accessMode
  }
  if (updates.allowEdit !== undefined) {
    designerStore.allowEdit = updates.allowEdit
  }
  if (updates.maxEditCount !== undefined) {
    designerStore.maxEditCount = updates.maxEditCount
  }
  if (updates.submitDeadline !== undefined) {
    designerStore.submitDeadline = updates.submitDeadline
  }
  if (updates.uiSchema !== undefined) {
    designerStore.uiSchema = updates.uiSchema
  }
}

const handlePreview = () => {
  if (designerStore.fields.length === 0) {
    message.warning('请先添加字段')
    return
  }
  showPreview.value = true
}

const openPermissionDrawer = () => {
  showPermissionDrawer.value = true
}

const handleSave = async () => {
  try {
    console.log("点击了保存按钮");
    
    saving.value = true
    
    const errors = FormValidation.validateFormConfig(designerStore.getFormConfig())
    if (errors.length > 0) {
      console.log("错误errors:",errors);
      
      message.warning(errors[0])
      return
    }
    
    const config = designerStore.getFormConfig()
    const payload: FormCreateRequest = {
      name: config.name,
      category: config.category,
      access_mode: config.accessMode,
      allow_edit: config.allowEdit,
      max_edit_count: config.maxEditCount,
      submit_deadline: config.submitDeadline,
      form_schema: config.formSchema,
      ui_schema: config.uiSchema,
      logic_schema: config.logicSchema,
    }
    
    if (designerStore.formId) {
      await formApi.updateForm(designerStore.formId, payload)
      message.success('保存成功')
    } else {
      const res = await formApi.createForm(payload)
      designerStore.formId = res.data.id
      message.success('创建成功')
      router.replace({ query: { id: res.data.id } })
    }
  } catch (error) {
    message.error(resolveErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

const handlePublish = async () => {
  try {
    await handleSave()
    
    if (!designerStore.formId) {
      message.error('请先保存表单')
      return
    }
    
    const errors = FormValidation.validateFormConfig(designerStore.getFormConfig())
    if (errors.length > 0) {
      dialog.error({
        title: '无法发布',
        content: errors.join('\n'),
      })
      return
    }
    
    dialog.info({
      title: '确认发布',
      content: '发布后表单配置将无法修改，是否继续？',
      positiveText: '发布',
      negativeText: '取消',
      onPositiveClick: async () => {
        publishing.value = true
        try {
          await formApi.publishForm(designerStore.formId!)
          formStatus.value = FormStatus.PUBLISHED
          message.success('发布成功')
        } catch (error) {
          message.error(resolveErrorMessage(error, '发布失败'))
        } finally {
          publishing.value = false
        }
      },
    })
  } catch (error) {
    message.error(resolveErrorMessage(error, '发布表单失败，请稍后重试'))
  }
}

/**
 * 应用 AI 生成的配置
 */
const handleApplyAIConfig = (config: AIFormGenerateResponse['config']) => {
  try {
    console.log('[设计器] 应用 AI 配置:', config)

    // 设置基础信息
    if (config.name) designerStore.formName = config.name
    if (config.category) designerStore.formCategory = config.category
    if (config.accessMode) designerStore.accessMode = config.accessMode as AccessMode
    if (config.allowEdit !== undefined) designerStore.allowEdit = config.allowEdit
    if (config.maxEditCount !== undefined) designerStore.maxEditCount = config.maxEditCount
    if (config.submitDeadline) designerStore.submitDeadline = config.submitDeadline

    // ✅ 直接替换字段列表（深拷贝）
    if (config.formSchema?.fields) {
      designerStore.fields = JSON.parse(JSON.stringify(config.formSchema.fields)) as FormField[]
      console.log('[设计器] 已加载字段，数量:', designerStore.fields.length)
    } else {
      designerStore.fields = []  // ✅ 没有字段时，清空而不是保留
    }

    // ✅ 直接替换 UI 配置，但确保结构完整
    if (config.uiSchema) {
      designerStore.uiSchema = {
        layout: config.uiSchema.layout || {
          type: 'vertical',
          labelWidth: 120,
          labelPosition: 'right',
          size: 'medium',
        },
        rows: config.uiSchema.rows || [],      // ✅ 确保是数组，而不是 undefined
        groups: config.uiSchema.groups || []   // ✅ 确保是数组，而不是 undefined
      }
      console.log('[设计器] 已加载 UI 配置')
    } else {
      // ✅ 没有 UI 配置时，使用默认配置
      designerStore.uiSchema = {
        layout: {
          type: 'vertical',
          labelWidth: 120,
          labelPosition: 'right',
          size: 'medium',
        },
        rows: [],
        groups: []
      }
    }

    // ✅ 直接替换逻辑规则，但确保结构完整
    if (config.logicSchema) {
      const nextLogic: LogicSchema = {
        rules: config.logicSchema.rules || []  // ✅ 确保是数组，而不是 undefined
      }
      designerStore.logicSchema = nextLogic
      console.log('[设计器] 已加载逻辑规则，数量:', designerStore.logicSchema.rules.length)
    } else {
      // ✅ 没有逻辑规则时，使用空规则
      designerStore.logicSchema = {
        rules: []
      }
    }

    // 清除选中
    designerStore.clearSelection()

    // 标记为 AI 生成
    isAIGenerated.value = true

    message.success(`已加载 AI 生成的表单「${config.name}」`)
  } catch (error) {
    console.error('[设计器] 应用 AI 配置失败:', error)
    message.error(resolveErrorMessage(error, '应用配置失败'))
  }
}

/**
 * 加载表单数据
 */
const toFormStatus = (value: string | undefined): FormStatus => {
  if (value === FormStatus.PUBLISHED || value === FormStatus.ARCHIVED || value === FormStatus.DRAFT) {
    return value
  }
  return FormStatus.DRAFT
}

const loadFormData = async (formId: number) => {
  try {
    const res = await formApi.getFormDetail(formId)
    designerStore.loadFormConfig(res.data)
    formStatus.value = toFormStatus(res.data.status)
  } catch (error) {
    message.error(resolveErrorMessage(error, '加载失败'))
  }
}

/**
 * 从 sessionStorage 加载 AI 配置
 */
const loadAIConfigFromStorage = (): boolean => {
  console.log('[设计器] 检查 sessionStorage AI 配置')
  
  // ✅ 使用 ConfigTransfer 工具
  if (!ConfigTransfer.hasConfig()) {
    console.log('[设计器] sessionStorage 中没有 AI 配置')
    return false
  }

  const config = ConfigTransfer.getConfig()
  
  if (!config) {
    console.log('[设计器] AI 配置读取失败')
    return false
  }

  console.log('[设计器] 从 sessionStorage 读取到 AI 配置:', config)
  console.log('[设计器] 字段数量:', config.formSchema?.fields?.length)

  // 应用配置
  handleApplyAIConfig(config)

  // ✅ 清除 sessionStorage，避免刷新后重复加载
  ConfigTransfer.clearConfig()

  return true
}


onMounted(async () => {
  console.log('[设计器] onMounted 开始')
  console.log('[设计器] route.query:', route.query)
  
  const formId = route.query.id
  const fromAI = route.query.from === 'ai'
  
  if (formId) {
    // 加载已有表单
    console.log('[设计器] 加载已有表单:', formId)
    await loadFormData(Number(formId))
  } else {
    // 新建表单
    console.log('[设计器] 新建表单，重置 store')
    designerStore.reset()
    
    // ✅ 等待 DOM 更新
    await nextTick()
    
    // ✅ 检查是否来自 AI 生成
    if (fromAI) {
      console.log('[设计器] 检测到来自 AI 生成')
      const loaded = loadAIConfigFromStorage()
      
      if (!loaded) {
        console.warn('[设计器] AI 配置加载失败')
        message.warning('AI 配置加载失败，请重新生成')
      }
    } else {
      console.log('[设计器] 正常新建表单')
    }
  }
  
  console.log('[设计器] onMounted 完成')
  console.log('[设计器] 最终 fields 数量:', designerStore.fields.length)
  console.log('[设计器] 最终 fields 内容:', designerStore.fields)
})
</script>

<style scoped lang="scss">
.form-designer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.designer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  
  .header-left,
  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.designer-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.designer-sidebar {
  background: #ffffff;
  overflow-y: auto;
  
  &.left {
    width: 280px;
    border-right: 1px solid #e5e7eb;
  }
  
  &.right {
    width: 360px;
    border-left: 1px solid #e5e7eb;
  }
}

.designer-canvas {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>