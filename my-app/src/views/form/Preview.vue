<template>
    <div class="form-preview-page">
      <n-page-header @back="handleBack">
        <template #title>表单预览</template>
        <template #extra>
          <n-space>
            <n-button @click="handleEdit">
              <template #icon>
                <Icon icon="carbon:edit" />
              </template>
              编辑
            </n-button>
          </n-space>
        </template>
      </n-page-header>
      
      <n-card class="preview-card">
        <n-spin :show="loading">
          <FormPreview v-if="formConfig" :config="formConfig" />
        </n-spin>
      </n-card>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useMessage } from 'naive-ui'
  import { Icon } from '@iconify/vue'
  import FormPreview from '@/components/FormDesigner/FormPreview.vue'
  import * as formApi from '@/api/form'
  import { AccessMode, type FormConfig } from '@/types/form'
  
  const route = useRoute()
  const router = useRouter()
  const message = useMessage()
  
  const loading = ref(false)
  const formConfig = ref<FormConfig | null>(null)

  const resolveErrorMessage = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback

  const toAccessMode = (value: string | undefined): AccessMode =>
    value === AccessMode.PUBLIC ? AccessMode.PUBLIC : AccessMode.AUTHENTICATED

  const loadFormData = async () => {
    try {
      loading.value = true
      const formId = Number(route.params.id)
      if (Number.isNaN(formId)) {
        message.error('无效的表单 ID')
        router.back()
        return
      }

      const { data } = await formApi.getFormDetail(formId)
      
      formConfig.value = {
        id: data.id,
        name: data.name,
        category: data.category,
        accessMode: toAccessMode(data.access_mode),
        allowEdit: data.allow_edit,
        maxEditCount: data.max_edit_count,
        submitDeadline: data.submit_deadline,
        formSchema: data.schema_json,
        uiSchema: data.ui_schema_json,
        logicSchema: data.logic_json,
      }
    } catch (error) {
      message.error(resolveErrorMessage(error, '加载失败'))
    } finally {
      loading.value = false
    }
  }
  
  const handleBack = () => {
    router.back()
  }
  
  const handleEdit = () => {
    router.push({
      path: '/form/designer',
      query: { id: route.params.id },
    })
  }
  
  onMounted(() => {
    loadFormData()
  })
  </script>
  
  <style scoped lang="scss">
  .form-preview-page {
    padding: 24px;
  }
  
  .preview-card {
    margin-top: 16px;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
  }
  </style>