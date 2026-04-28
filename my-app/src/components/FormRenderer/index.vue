<template>
  <div class="form-renderer">
    <FormPreview
      :config="config"
      :edit-mode="editMode"
      :model-value="modelValue"
      @update:model-value="handleUpdate"
      @submit="handleSubmit"
      @save-as-draft="handleSaveAsDraft"
    />
  </div>
</template>

<script setup lang="ts">
import FormPreview from '@/components/FormDesigner/FormPreview.vue'
import type { FormConfig, FormSubmissionPayload } from '@/types/form'

interface Props {
  config: FormConfig
  editMode?: boolean
  modelValue?: Record<string, unknown>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({})
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, unknown>): void
  (e: 'submit', payload: FormSubmissionPayload): void
  (e: 'saveAsDraft', payload: FormSubmissionPayload): void
}>()

const handleUpdate = (value: Record<string, unknown>) => {
  emit('update:modelValue', value)
}

const handleSubmit = (payload: FormSubmissionPayload) => {
  emit('submit', payload)
}

const handleSaveAsDraft = (payload: FormSubmissionPayload) => {
  emit('saveAsDraft', payload)
}
</script>

<style scoped>
.form-renderer {
  width: 100%;
}
</style>
