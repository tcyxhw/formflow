<template>
  <div class="form-renderer">
    <FormPreview :config="config" @submit="handleSubmit" />
  </div>
</template>

<script setup lang="ts">
import FormPreview from '@/components/FormDesigner/FormPreview.vue'
import type { FormConfig, FormSubmissionPayload } from '@/types/form'

interface Props {
  config: FormConfig
}

withDefaults(defineProps<Props>(), {})

const emit = defineEmits<{
  (e: 'submit', data: FormSubmissionPayload): void
}>()

const handleSubmit = (payload: FormSubmissionPayload) => {
  emit('submit', payload)
}
</script>