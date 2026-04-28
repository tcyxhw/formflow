<template>
  <div class="form-fill-page">
    <n-card class="fill-card">
      <div class="page-header">
        <n-button @click="goHome" class="home-btn">
          <template #icon>
            <n-icon><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></n-icon>
          </template>
          返回主页
        </n-button>
        <n-button v-if="isEditMode" @click="exitEdit" type="warning" class="exit-btn">
          <template #icon>
            <n-icon><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></n-icon>
          </template>
          退出编辑
        </n-button>
      </div>
      <div class="form-header">
        <h1 class="form-title">{{ formConfig?.name }}</h1>
        <div v-if="formConfig?.category" class="form-category">
          {{ formConfig.category }}
        </div>
        <div class="autosave-status">
          <span v-if="autoSaving" class="autosave-indicator saving">保存中...</span>
          <span v-else-if="lastSavedTime" class="autosave-indicator saved">已自动保存 {{ lastSavedTime }}</span>
        </div>
      </div>

      <!-- 权限/表单内容 -->
      <n-spin :show="loading || permissionChecking">
        <n-result
          v-if="permissionError"
          status="error"
          title="权限校验失败"
          :description="permissionError"
        >
          <template #footer>
            <n-button type="primary" size="small" @click="retryPermissionCheck">重新检测</n-button>
          </template>
        </n-result>

        <n-result
          v-else-if="!permissionChecking && !canFill"
          status="warning"
          title="暂无填写权限"
          description="如需填写该表单，请联系管理员授予 fill 权限。"
        />

        <FormRenderer
          v-else-if="formConfig && canFill"
          :config="formConfig"
          :edit-mode="isEditMode"
          @submit="handleSubmit"
          @save-as-draft="handleSaveAsDraft"
        />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import FormRenderer from '@/components/FormRenderer/index.vue'
import * as formApi from '@/api/form'
import * as submissionApi from '@/api/submission'
import { getMyFormPermissions } from '@/api/formPermission'
import type { AccessMode, FormConfig, FormSubmissionPayload } from '@/types/form'
import type { FormPermissionOverview } from '@/types/formPermission'
import type { SubmissionData } from '@/types/submission'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const loading = ref(false)
const formConfig = ref<FormConfig | null>(null)
const currentFormId = ref<number | null>(null)
const permissionChecking = ref(false)
const permissionError = ref<string | null>(null)
const permissionOverview = ref<FormPermissionOverview | null>(null)
const canFill = computed(() => Boolean(permissionOverview.value?.can_fill))
const editingSubmissionId = ref<number | null>(null)
const previousSubmissionStatus = ref<string | null>(null)
const explicitEditSubmissionId = ref<number | null>(null)
const formData = ref<Record<string, any>>({})
const autoSaveTimer = ref<ReturnType<typeof setInterval> | null>(null)
const autoSaving = ref(false)
const lastSavedTime = ref<string | null>(null)

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback

const isEditMode = computed(() => {
  // 只有通过URL参数明确指定编辑某个提交时，才进入编辑模式
  // 如果是通过"再次填写"进入（即使editingSubmissionId被赋值），也视为新建模式
  if (explicitEditSubmissionId.value !== null) {
    return true
  }
  return false
})

const loadFormData = async () => {
  try {
    loading.value = true
    const formId = Number(route.params.id)
    if (Number.isNaN(formId)) {
      message.error('无效的表单 ID')
      router.back()
      return
    }

    currentFormId.value = formId

    // 检查是否是编辑模式（通过URL参数明确指定编辑某个提交）
    const editSubmissionId = route.query.edit_submission_id
    if (editSubmissionId) {
      explicitEditSubmissionId.value = Number(editSubmissionId)
      editingSubmissionId.value = Number(editSubmissionId)
    }

    const { data } = await formApi.getFormDetail(formId)

    formConfig.value = {
      id: data.id,
      name: data.name,
      category: data.category,
      accessMode: data.access_mode as AccessMode,
      allowEdit: data.allow_edit,
      maxEditCount: data.max_edit_count,
      submitDeadline: data.submit_deadline,
      allowRepeatSubmit: data.allow_repeat_submit,
      maxSubmitCount: data.max_submit_count,
      formSchema: data.schema_json,
      uiSchema: data.ui_schema_json,
      logicSchema: data.logic_json,
    }

    await checkFillPermission(formId)

    // 如果是编辑模式，加载指定的提交数据；否则检查是否可以创建新提交
    if (editingSubmissionId.value) {
      await loadSubmissionForEdit(editingSubmissionId.value)
    } else {
      await checkAndLoadPreviousSubmission(formId)
    }

    // 加载草稿数据并启动自动保存
    await initAutoSave(formId)
  } catch (error) {
    message.error(resolveErrorMessage(error, '加载失败'))
  } finally {
    loading.value = false
  }
}

const loadSubmissionForEdit = async (submissionId: number) => {
  try {
    const { data } = await submissionApi.getSubmissionDetail(submissionId)
    console.log('[loadSubmissionForEdit] API data:', {
      submissionId,
      attachments: data.attachments,
      data_jsonb: data.data_jsonb,
      snapshot_json: data.snapshot_json
    })

    if (data && formConfig.value && data.data_jsonb) {
      // 将提交数据预填充到表单中
      const fields = formConfig.value.formSchema?.fields || []
      fields.forEach((field: any) => {
        if (data.data_jsonb && field.id in data.data_jsonb) {
          field.defaultValue = data.data_jsonb[field.id]
        }
      })

      // 传递附件信息
      if (data.attachments && data.attachments.length > 0) {
        console.log('[loadSubmissionForEdit] 加载附件:', data.attachments)
        formConfig.value = {
          ...formConfig.value!,
          attachments: data.attachments,
          formSchema: {
            ...formConfig.value!.formSchema!,
            fields: [...fields]
          }
        }
      } else {
        console.log('[loadSubmissionForEdit] 无附件数据')
        // 强制触发响应式更新
        formConfig.value = {
          ...formConfig.value!,
          formSchema: {
            ...formConfig.value!.formSchema!,
            fields: [...fields]
          }
        }
      }

      console.log('[loadSubmissionForEdit] 更新后的 formConfig:', {
        attachments: formConfig.value?.attachments?.length,
        fields: formConfig.value?.formSchema?.fields?.length
      })
    }
  } catch (error) {
    console.error('加载编辑数据失败:', error)
    message.error('加载历史数据失败')
  }
}

const checkAndLoadPreviousSubmission = async (formId: number) => {
  try {
    const { data } = await submissionApi.getLatestSubmission(formId)

    if (!data) {
      return
    }

    previousSubmissionStatus.value = data.status

    const allowRepeat = formConfig.value?.allowRepeatSubmit ?? true
    const maxCount = formConfig.value?.maxSubmitCount ?? 0
    const isApprovedOrRejected = data.status === 'approved' || data.status === 'rejected'

    if (allowRepeat && isApprovedOrRejected) {
      console.log(`[checkAndLoadPreviousSubmission] 表单允许重复提交，上次提交状态为 ${data.status}，不加载历史数据，允许创建新提交`)
      return
    }

    if (maxCount > 0) {
      const userSubmissionCount = await getUserSubmissionCount(formId)
      if (userSubmissionCount >= maxCount) {
        console.log(`[checkAndLoadPreviousSubmission] 已达到最大提交次数 ${maxCount}，不允许创建新提交`)
        return
      }
    }

    console.log(`[checkAndLoadPreviousSubmission] 加载历史提交数据: submission_id=${data.id}, status=${data.status}`)
    await populateFormWithSubmissionData(data)
  } catch (error) {
    console.log('未找到历史提交或加载失败:', error)
  }
}

const getUserSubmissionCount = async (formId: number): Promise<number> => {
  try {
    const { data } = await submissionApi.getSubmissionList({ form_id: formId, page: 1, page_size: 100 })
    return data.items.length
  } catch {
    return 0
  }
}

const populateFormWithSubmissionData = async (submission: any) => {
  if (!formConfig.value || !submission.data_jsonb) {
    return
  }

  const fields = formConfig.value.formSchema?.fields || []
  fields.forEach((field: any) => {
    if (submission.data_jsonb && field.id in submission.data_jsonb) {
      field.defaultValue = submission.data_jsonb[field.id]
    }
  })

  if (submission.attachments && submission.attachments.length > 0) {
    formConfig.value = {
      ...formConfig.value,
      attachments: submission.attachments,
      formSchema: {
        ...formConfig.value.formSchema!,
        fields: [...fields]
      }
    }
  } else {
    formConfig.value = {
      ...formConfig.value,
      formSchema: {
        ...formConfig.value.formSchema!,
        fields: [...fields]
      }
    }
  }

  editingSubmissionId.value = submission.id
  console.log(`已加载历史提交数据: submission_id=${submission.id}, status=${submission.status}`)
}

const checkFillPermission = async (formId: number) => {
  try {
    permissionChecking.value = true
    permissionError.value = null
    const { data } = await getMyFormPermissions(formId)
    permissionOverview.value = data ?? null
  } catch (error) {
    permissionError.value = resolveErrorMessage(error, '权限校验失败')
    permissionOverview.value = null
  } finally {
    permissionChecking.value = false
  }
}

const retryPermissionCheck = () => {
  if (currentFormId.value) {
    checkFillPermission(currentFormId.value)
  }
}

const initAutoSave = async (formId: number) => {
  const hasDraft = await loadDraft(formId)
  if (!hasDraft && formConfig.value?.formSchema?.fields) {
    const fields = formConfig.value.formSchema.fields
    const initialData: Record<string, unknown> = {}
    fields.forEach((field: any) => {
      if (field.defaultValue !== undefined) {
        initialData[field.id] = field.defaultValue
      }
    })
    if (Object.keys(initialData).length > 0) {
      formData.value = initialData
    }
  }
  if (!isEditMode.value) {
    startAutoSave()
  }
}

const handleSubmit = async (payload: FormSubmissionPayload) => {
  if (!currentFormId.value) {
    message.error('表单尚未准备完成')
    return
  }

  if (!canFill.value) {
    message.warning('当前账号暂无填写权限')
    return
  }

  try {
    // 编辑模式：保存编辑，不触发审批流程
    if (isEditMode.value) {
      await submissionApi.updateSubmission(
        editingSubmissionId.value!,
        payload as SubmissionData
      )
      message.success('保存成功')
      router.push('/form/fill-center')
      return
    }

    // 新建模式：创建提交并发起审批
    await submissionApi.createSubmission({
      form_id: currentFormId.value,
      data: payload as SubmissionData,
      auto_trigger_workflow: true
    })
    message.success('提交成功，审批流程已发起')
    router.push('/form/fill-center')
  } catch (error) {
    message.error(resolveErrorMessage(error, isEditMode.value ? '保存失败' : '提交失败'))
  }
}

const handleSaveAsDraft = async (payload: FormSubmissionPayload) => {
  if (!currentFormId.value) {
    message.error('表单尚未准备完成')
    return
  }

  if (!canFill.value) {
    message.warning('当前账号暂无填写权限')
    return
  }

  // 停止自动保存，避免冲突
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value)
    autoSaveTimer.value = null
  }

  try {
    await submissionApi.createSubmission({
      form_id: currentFormId.value,
      data: payload as SubmissionData,
      auto_trigger_workflow: false
    })
    message.success('暂存成功，可在"我的审批"中发起审批')
    
    router.push('/form/fill-center')
  } catch (error) {
    message.error(resolveErrorMessage(error, '暂存失败'))
  }
}

const loadDraft = async (formId: number, initialData?: Record<string, any>) => {
  try {
    const { data } = await submissionApi.getDraft(formId)
    if (data?.draft_data) {
      formData.value = data.draft_data
      if (data.auto_saved_at) {
        const time = new Date(data.auto_saved_at)
        lastSavedTime.value = time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      return true
    }
  } catch (error) {
    console.warn('加载草稿失败:', error)
  }
  if (initialData) {
    formData.value = initialData
  }
  return false
}

const saveDraft = async () => {
  if (!currentFormId.value || autoSaving.value || isEditMode.value) {
    return
  }
  if (Object.keys(formData.value).length === 0) {
    return
  }

  autoSaving.value = true
  try {
    await submissionApi.saveDraft({
      form_id: currentFormId.value,
      data: formData.value
    })
    const now = new Date()
    lastSavedTime.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    console.warn('自动保存失败:', error)
  } finally {
    autoSaving.value = false
  }
}

const startAutoSave = () => {
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value)
  }
  autoSaveTimer.value = setInterval(saveDraft, 30000)
}

onMounted(() => {
  loadFormData()
})

onUnmounted(() => {
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value)
    autoSaveTimer.value = null
  }
})

const goHome = () => {
  router.push('/')
}

const exitEdit = () => {
  router.push('/form/fill-center')
}
</script>

<style scoped lang="scss">
.form-fill-page {
  min-height: 100vh;
  padding: 40px 24px;
  background: #f5f7fa;
}

.fill-card {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.home-btn {
  color: #374151;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.2s ease;

  &:hover {
    color: #18a058;
    background: #f0fdf4;
    border-color: #86efac;
    transform: translateX(-2px);
  }

  &:active {
    transform: translateX(0);
  }
}

.exit-btn {
  margin-left: auto;
}

.form-header {
  text-align: center;
  padding-bottom: 32px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 32px;

  .form-title {
    margin: 0 0 12px;
    font-size: 28px;
    font-weight: 600;
    color: #1f2937;
  }

  .form-category {
    display: inline-block;
    padding: 4px 12px;
    background: #f0fdf4;
    border-radius: 4px;
    font-size: 14px;
    color: #18a058;
  }

  .autosave-status {
    margin-top: 8px;
    font-size: 12px;
    color: #9ca3af;
  }

  .autosave-indicator {
    &.saving {
      color: #f59e0b;
    }
    &.saved {
      color: #10b981;
    }
  }
}
</style>