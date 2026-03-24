<template>
  <n-image
    :src="imageUrl"
    :alt="alt"
    :width="width"
    :height="height"
    :object-fit="objectFit"
    :preview-src="previewSrc || imageUrl"
    :fallback-src="fallbackSrc"
  />
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { NImage } from 'naive-ui'
import { http } from '@/utils/request'

interface Props {
  src: string
  alt?: string
  width?: number | string
  height?: number | string
  objectFit?: 'fill' | 'contain' | 'cover' | 'none' | 'scale-down'
  previewSrc?: string
  fallbackSrc?: string
}

const props = defineProps<Props>()

const imageUrl = ref<string>(props.fallbackSrc || '')

const loadImage = async () => {
  if (!props.src) {
    imageUrl.value = props.fallbackSrc || ''
    return
  }

  try {
    const response = await http.get<Blob>(props.src, undefined, {
      responseType: 'blob',
      skipErrorHandler: true
    })
    // http.get 对于 blob 类型返回的是 AxiosResponse，其中 data 是 blob
    const blob = (response as unknown as { data: Blob }).data || response
    imageUrl.value = URL.createObjectURL(blob instanceof Blob ? blob : new Blob([blob]))
  } catch (error) {
    console.error('Failed to load image:', error)
    imageUrl.value = props.fallbackSrc || ''
  }
}

watch(() => props.src, loadImage)

onMounted(() => {
  loadImage()
})
</script>
