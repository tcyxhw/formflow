<template>
  <n-tag size="small" :bordered="false" :type="tagType" class="sla-badge">
    {{ labelText }}
    <template v-if="showRemaining">
      · {{ remainingText }}
    </template>
  </n-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'
import { formatRemainingMinutes, slaLevelLabel, slaTagByLevel } from '@/utils/sla'

interface Props {
  level?: string | null
  minutes?: number | null
  showRemaining?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  level: null,
  minutes: null,
  showRemaining: false
})

const labelText = computed(() => slaLevelLabel(props.level))
const remainingText = computed(() => formatRemainingMinutes(props.minutes))
const tagType = computed(() => slaTagByLevel(props.level, props.minutes))
</script>

<style scoped>
.sla-badge {
  text-transform: none;
}
</style>
