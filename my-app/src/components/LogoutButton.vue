<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { NButton, useMessage } from 'naive-ui'

interface Props {
  size?: 'small' | 'medium' | 'large'
  type?: 'primary' | 'default' | 'text' | 'error'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  type: 'default'
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const authStore = useAuthStore()
const message = useMessage()
const isLoading = ref(false)

const handleLogout = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    await authStore.logout()
    message.success('退出登录成功')
  } catch (error) {
    console.error('Logout failed:', error)
    message.error('退出登录失败')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <NButton
    :size="size"
    :type="type"
    :loading="isLoading"
    :disabled="isLoading"
    @click="handleLogout"
  >
    退出登录
  </NButton>
</template>

<style scoped>
.logout-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>