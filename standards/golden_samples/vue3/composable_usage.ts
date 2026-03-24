import { ref } from 'vue'

export function useLoading() {
  const loading = ref(false)

  const run = async <T>(fn: () => Promise<T>): Promise<T> => {
    loading.value = true
    try {
      return await fn()
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    run,
  }
}
