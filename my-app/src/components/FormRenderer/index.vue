<template>
  <div class="form-renderer">
    <FormPreview :config="config" @submit="handleSubmit" />
  </div>
</template>

<script setup lang="ts">
import { defineEmits } from 'vue'
import FormPreview from '@/components/FormDesigner/FormPreview.vue'
import type { FormConfig, FormSubmissionPayload } from '@/types/form'

interface Props {
  config: FormConfig
}

defineProps<Props>()
const emit = defineEmits<{ (e: 'submit', payload: FormSubmissionPayload): void }>()

const handleSubmit = (payload: FormSubmissionPayload) => {
  emit('submit', payload)
}
</script>

<style scoped>
.form-renderer {
  width: 100%;
}
</style>
