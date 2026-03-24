<template>
  <n-modal
    v-model:show="isVisible"
    :title="t('form.cascadeDeleteTitle')"
    :positive-text="t('common.confirm')"
    :negative-text="t('common.cancel')"
    :on-positive-click="handleConfirm"
    :on-negative-click="handleCancel"
    :loading="loading"
    preset="dialog"
    :closable="!loading"
  >
    <div class="cascade-delete-dialog">
      <n-alert type="warning" :title="t('form.cascadeDeleteWarning')" closable>
        {{ t('form.cascadeDeleteDescription') }}
      </n-alert>

      <div class="form-info">
        <div class="info-item">
          <span class="label">{{ t('form.formName') }}:</span>
          <span class="value">{{ formName }}</span>
        </div>
      </div>

      <div class="flow-definitions">
        <h4>{{ t('form.associatedFlowDefinitions') }} ({{ flowDefinitionCount }})</h4>
        <n-list>
          <n-list-item v-for="flow in flowDefinitions" :key="flow.id">
            <template #prefix>
              <n-icon>
                <CheckCircleOutlined />
              </n-icon>
            </template>
            <div class="flow-item">
              <div class="flow-name">{{ flow.name }}</div>
              <div class="flow-version">v{{ flow.version }}</div>
            </div>
          </n-list-item>
        </n-list>
      </div>

      <n-alert type="error" :title="t('form.cascadeDeleteConfirm')" closable>
        {{ t('form.cascadeDeleteConfirmDescription') }}
      </n-alert>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NModal, NAlert, NList, NListItem, NIcon } from 'naive-ui'
import { CheckCircleOutlined } from '@vicons/antd'
import { useI18n } from 'vue-i18n'

interface FlowDefinition {
  id: number
  name: string
  version: number
}

interface Props {
  visible: boolean
  formId: number
  formName: string
  flowDefinitionCount: number
  flowDefinitions: FlowDefinition[]
  loading?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()
const { t } = useI18n()

const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  isVisible.value = false
}
</script>

<style scoped lang="scss">
.cascade-delete-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .form-info {
    padding: 12px;
    background-color: #f5f5f5;
    border-radius: 4px;

    .info-item {
      display: flex;
      gap: 8px;

      .label {
        font-weight: 500;
        min-width: 100px;
      }

      .value {
        flex: 1;
        word-break: break-all;
      }
    }
  }

  .flow-definitions {
    h4 {
      margin: 0 0 12px 0;
      font-size: 14px;
      font-weight: 500;
    }

    .flow-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;

      .flow-name {
        flex: 1;
        font-weight: 500;
      }

      .flow-version {
        color: #999;
        font-size: 12px;
      }
    }
  }
}
</style>
