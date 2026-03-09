<template>
    <div class="default-value-input">
      <!-- 文本输入 -->
      <n-input
        v-if="isTextField"
        :value="textValue ?? ''"
        :placeholder="getStringProp('placeholder') ?? '请输入默认值'"
        clearable
        @update:value="handleUpdate"
      />
      
      <!-- 多行文本 -->
      <n-input
        v-else-if="field.type === FieldType.TEXTAREA"
        :value="textValue ?? ''"
        type="textarea"
        :rows="3"
        :placeholder="getStringProp('placeholder') ?? '请输入默认值'"
        @update:value="handleUpdate"
      />
      
      <!-- 数字输入 -->
      <n-input-number
        v-else-if="field.type === FieldType.NUMBER"
        :value="numberValue ?? undefined"
        :min="getNumberProp('min')"
        :max="getNumberProp('max')"
        :step="getNumberProp('step')"
        placeholder="请输入默认值"
        style="width: 100%"
        @update:value="handleUpdate"
      />
      
      <!-- 选择 -->
      <n-select
        v-else-if="field.type === FieldType.SELECT"
        :value="selectValue"
        :options="selectOptionsForUi"
        :multiple="getBooleanProp('multiple')"
        :placeholder="getStringProp('placeholder') ?? '请选择默认值'"
        clearable
        @update:value="handleUpdate"
      />
      
      <!-- 单选 -->
      <n-radio-group
        v-else-if="field.type === FieldType.RADIO"
        :value="radioValue"
        @update:value="handleUpdate"
      >
        <n-space vertical :size="8">
          <n-radio
            v-for="option in selectOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </n-radio>
        </n-space>
      </n-radio-group>
      
      <!-- 复选 -->
      <n-checkbox-group
        v-else-if="field.type === FieldType.CHECKBOX"
        :value="checkboxValue"
        @update:value="handleUpdate"
      >
        <n-space vertical :size="8">
          <n-checkbox
            v-for="option in selectOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </n-checkbox>
        </n-space>
      </n-checkbox-group>
      
      <!-- 开关 -->
      <n-switch
        v-else-if="field.type === FieldType.SWITCH"
        :value="booleanValue ?? false"
        @update:value="handleUpdate"
      >
        <template #checked>开启</template>
        <template #unchecked>关闭</template>
      </n-switch>
      
      <!-- 时间选择器 -->
      <n-time-picker
        v-else-if="field.type === FieldType.TIME"
        :value="timeValue"
        placeholder="请选择默认时间"
        clearable
        style="width: 100%"
        @update:value="handleUpdate"
      />
      
      <!-- 日期选择器 -->
      <n-date-picker
        v-else-if="isDateField"
        :value="dateValue"
        :type="getDatePickerType()"
        placeholder="请选择默认日期"
        clearable
        style="width: 100%"
        @update:value="handleUpdate"
      />
      
      <!-- 评分 -->
      <n-rate
        v-else-if="field.type === FieldType.RATE"
        :value="numberValue ?? undefined"
        :count="getNumberProp('count') ?? 5"
        :allow-half="getBooleanProp('allowHalf')"
        @update:value="handleUpdate"
      />
      
      <!-- 其他 -->
      <n-input
        v-else
        :value="textValue ?? ''"
        placeholder="请输入默认值"
        @update:value="handleUpdate"
      />
    </div>
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue'
  import type { FormField, FieldPropValue, SelectOption } from '@/types/field'
  import { FieldType } from '@/types/field'
  
  interface Props {
    modelValue: FieldPropValue
    field: FormField
  }
  
  const props = defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update:value', value: FieldPropValue): void
  }>()
  
  const textValue = computed<string | null>(() => {
    const value = props.modelValue
    if (typeof value === 'string') return value
    if (value == null) return null
    return String(value)
  })

  const numberValue = computed<number | null>(() => {
    const value = props.modelValue
    if (typeof value === 'number') return value
    return null
  })

  const booleanValue = computed<boolean | undefined>(() => {
    const value = props.modelValue
    return typeof value === 'boolean' ? value : undefined
  })

  const toSelectableArray = (value: FieldPropValue): Array<string | number> => {
    if (Array.isArray(value)) {
      return value.filter((item): item is string | number => typeof item === 'string' || typeof item === 'number')
    }
    return []
  }

  const selectValue = computed<string | number | Array<string | number> | null>(() => {
    const value = props.modelValue
    if (Array.isArray(value)) {
      return toSelectableArray(value)
    }
    if (typeof value === 'string' || typeof value === 'number') {
      return value
    }
    return null
  })

  const checkboxValue = computed<(string | number)[]>(() => toSelectableArray(props.modelValue))

  const radioValue = computed<string | number | boolean | null>(() => {
    const value = props.modelValue
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return value
    }
    return null
  })

  const parseTimestamp = (value: FieldPropValue | null | undefined): number | null => {
    if (value instanceof Date) {
      return Number.isNaN(value.getTime()) ? null : value.getTime()
    }
    if (typeof value === 'number') {
      return value
    }
    if (typeof value === 'string') {
      const timestamp = Date.parse(value)
      return Number.isNaN(timestamp) ? null : timestamp
    }
    return null
  }

  const timeValue = computed<number | null>(() => parseTimestamp(props.modelValue))

  const dateValue = computed<number | [number, number] | null>(() => {
    const value = props.modelValue
    if (Array.isArray(value) && value.length === 2) {
      const start = parseTimestamp(value[0] as FieldPropValue)
      const end = parseTimestamp(value[1] as FieldPropValue)
      if (start != null && end != null) {
        return [start, end]
      }
      return null
    }
    return parseTimestamp(value)
  })

  const isSelectOptionArray = (options: unknown): options is SelectOption[] => {
    if (!Array.isArray(options)) {
      return false
    }
    return options.every((item) => typeof item === 'object' && item !== null && 'label' in item && 'value' in item)
  }

  type SimpleSelectOption = { label: string; value: string | number; disabled?: boolean }

  const selectOptions = computed<SimpleSelectOption[]>(() => {
    const options = props.field.props.options
    if (options && isSelectOptionArray(options)) {
      return options.map(option => ({
        label: option.label,
        value: option.value,
        disabled: 'disabled' in option ? (option as SelectOption).disabled : undefined
      }))
    }
    return []
  })

  const selectOptionsForUi = computed(() => selectOptions.value)

  const getNumberProp = (key: string): number | undefined => {
    const value = props.field.props[key]
    return typeof value === 'number' ? value : undefined
  }

  const getBooleanProp = (key: string): boolean | undefined => {
    const value = props.field.props[key]
    return typeof value === 'boolean' ? value : undefined
  }

  const getStringProp = (key: string): string | undefined => {
    const value = props.field.props[key]
    return typeof value === 'string' ? value : undefined
  }

  const isTextField = computed(() => {
    return [
      FieldType.TEXT,
      FieldType.PHONE,
      FieldType.EMAIL,
    ].includes(props.field.type as FieldType)
  })

  const isDateField = computed(() => {
    return [
      FieldType.DATE,
      FieldType.DATE_RANGE,
      FieldType.DATETIME,
    ].includes(props.field.type as FieldType)
  })

  const getDatePickerType = (): 'date' | 'datetime' | 'daterange' | 'datetimerange' => {
    switch (props.field.type) {
      case FieldType.DATE_RANGE:
        return 'daterange'
      case FieldType.DATETIME:
        return 'datetime'
      default:
        return 'date'
    }
  }

  const handleUpdate = (value: FieldPropValue) => {
    emit('update:value', value)
  }
  </script>
  
  <style scoped lang="scss">
  .default-value-input {
    width: 100%;
  }
  </style>