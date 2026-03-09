<template>
  <div class="form-fill-page">
    <n-card class="fill-card">
      <!-- 表单头部 -->
      <div class="form-header">
        <h1 class="form-title">{{ formConfig?.name }}</h1>
        <div v-if="formConfig?.category" class="form-category">
          {{ formConfig.category }}
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
          @submit="handleSubmit"
        />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback

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
    const { data } = await formApi.getFormDetail(formId)

    formConfig.value = {
      id: data.id,
      name: data.name,
      category: data.category,
      accessMode: data.access_mode as AccessMode,
      allowEdit: data.allow_edit,
      maxEditCount: data.max_edit_count,
      submitDeadline: data.submit_deadline,
      formSchema: data.schema_json,
      uiSchema: data.ui_schema_json,
      logicSchema: data.logic_json,
    }

    await checkFillPermission(formId)
  } catch (error) {
    message.error(resolveErrorMessage(error, '加载失败'))
  } finally {
    loading.value = false
  }
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
    await submissionApi.createSubmission({
      form_id: currentFormId.value,
      data: payload as SubmissionData
    })
    message.success('提交成功')
    router.push('/submissions')
  } catch (error) {
    message.error(resolveErrorMessage(error, '提交失败'))
  }
}

onMounted(() => {
  loadFormData()
})
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
}
</style>