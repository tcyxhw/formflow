<script setup lang="ts">
import { reactive, ref } from 'vue'

interface LoginForm {
  username: string
  password: string
}

const form = reactive<LoginForm>({
  username: '',
  password: '',
})

const loading = ref(false)

const submit = async () => {
  if (!form.username || !form.password) return
  loading.value = true
  try {
    // 调用现有 API 封装
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form @submit.prevent="submit">
    <input v-model="form.username" />
    <input v-model="form.password" type="password" />
    <button :disabled="loading">提交</button>
  </form>
</template>
