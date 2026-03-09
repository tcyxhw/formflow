<template>
  <div class="props-config">
    <n-scrollbar style="max-height: calc(100vh - 300px)">
      <div class="config-content">
        <n-form :model="localProps" label-placement="top" size="medium">
          <!-- ========== 文本类字段 ========== -->
          <template v-if="isTextField">
            <n-form-item label="占位符">
              <n-input
                :value="getStringProp('placeholder') ?? ''"
                placeholder="如：请输入姓名"
                clearable
                @update:value="value => setStringProp('placeholder', value)"
              />
            </n-form-item>

            <n-form-item label="最大长度">
              <n-input-number
                :value="getNumberProp('maxLength')"
                :min="1"
                :max="10000"
                placeholder="不限制"
                style="width: 100%"
                @update:value="value => setNumberProp('maxLength', value)"
              >
                <template #suffix>字符</template>
              </n-input-number>
            </n-form-item>

            <n-form-item v-if="field.type === FieldType.TEXTAREA" label="行数">
              <n-slider
                :value="getNumberProp('rows') ?? 4"
                :min="2"
                :max="10"
                :step="1"
                :marks="rowMarks"
                @update:value="value => setNumberProp('rows', Array.isArray(value) ? value[0] : value)"
              />
            </n-form-item>

            <n-form-item v-if="field.type === FieldType.TEXTAREA">
              <template #label>
                <div class="label-with-desc">
                  <span>显示字数统计</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('showWordLimit') ?? false"
                @update:value="value => setBooleanProp('showWordLimit', value)"
              />
            </n-form-item>

            <n-form-item>
              <template #label>
                <div class="label-with-desc">
                  <span>可清空</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('clearable') ?? false"
                @update:value="value => setBooleanProp('clearable', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 数字字段 ========== -->
          <template v-else-if="field.type === FieldType.NUMBER">
            <n-form-item label="最小值">
              <n-input-number
                :value="getNumberProp('min')"
                placeholder="不限制"
                style="width: 100%"
                @update:value="value => setNumberProp('min', value)"
              />
            </n-form-item>

            <n-form-item label="最大值">
              <n-input-number
                :value="getNumberProp('max')"
                placeholder="不限制"
                style="width: 100%"
                @update:value="value => setNumberProp('max', value)"
              />
            </n-form-item>

            <n-form-item label="步长">
              <n-input-number
                :value="getNumberProp('step')"
                :min="0"
                placeholder="默认 1"
                style="width: 100%"
                @update:value="value => setNumberProp('step', value)"
              />
            </n-form-item>

            <n-form-item label="小数位数">
              <n-input-number
                :value="getNumberProp('precision')"
                :min="0"
                :max="10"
                placeholder="不限制"
                style="width: 100%"
                @update:value="value => setNumberProp('precision', value)"
              >
                <template #suffix>位</template>
              </n-input-number>
            </n-form-item>
          </template>

          <!-- ========== 选择类字段 ========== -->
          <template v-else-if="isSelectField">
            <n-form-item label="选项配置" required>
              <OptionsEditor
                :options="selectOptions"
                @update:options="handleOptionsUpdate"
              />
            </n-form-item>

            <n-form-item v-if="field.type === FieldType.SELECT || field.type === FieldType.CHECKBOX">
              <template #label>
                <div class="label-with-desc">
                  <span>多选</span>
                  <span class="label-hint">允许选择多个选项</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('multiple') ?? field.type === FieldType.CHECKBOX"
                @update:value="value => setBooleanProp('multiple', value)"
              />
            </n-form-item>

            <n-form-item v-if="field.type === FieldType.SELECT">
              <template #label>
                <div class="label-with-desc">
                  <span>可清空</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('clearable') ?? true"
                @update:value="value => setBooleanProp('clearable', value)"
              />
            </n-form-item>

            <n-form-item v-if="field.type === FieldType.SELECT">
              <template #label>
                <div class="label-with-desc">
                  <span>可搜索</span>
                  <span class="label-hint">支持关键词过滤选项</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('filterable') ?? false"
                @update:value="value => setBooleanProp('filterable', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 日期字段 ========== -->
          <template v-else-if="isDateField">
            <n-form-item label="日期格式">
              <n-input
                :value="getStringProp('format') ?? ''"
                placeholder="如: yyyy-MM-dd"
                @update:value="value => setStringProp('format', value)"
              />
              <template #feedback>
                <span class="field-hint">显示给用户的格式</span>
              </template>
            </n-form-item>

            <n-form-item label="值格式">
              <n-input
                :value="getStringProp('valueFormat') ?? ''"
                placeholder="如: yyyy-MM-dd"
                @update:value="value => setStringProp('valueFormat', value)"
              />
              <template #feedback>
                <span class="field-hint">提交到后端的格式</span>
              </template>
            </n-form-item>

            <n-form-item>
              <template #label>
                <div class="label-with-desc">
                  <span>可清空</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('clearable') ?? true"
                @update:value="value => setBooleanProp('clearable', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 上传字段 ========== -->
          <template v-else-if="field.type === FieldType.UPLOAD">
            <n-form-item label="上传地址" required>
              <n-input
                :value="getStringProp('action') ?? ''"
                placeholder="/api/v1/upload"
                @update:value="value => setStringProp('action', value)"
              />
            </n-form-item>

            <n-form-item label="接受的文件类型">
              <n-input
                :value="getStringProp('accept') ?? ''"
                placeholder="如: .pdf,.jpg,.png 或 image/*"
                @update:value="value => setStringProp('accept', value)"
              />
            </n-form-item>

            <n-form-item label="最大文件大小">
              <n-input-number
                :value="maxSizeMB"
                :min="0"
                placeholder="不限制"
                style="width: 100%"
                @update:value="handleMaxSizeUpdate"
              >
                <template #suffix>MB</template>
              </n-input-number>
            </n-form-item>

            <n-form-item label="最大文件数量">
              <n-input-number
                :value="getNumberProp('maxCount')"
                :min="1"
                :max="20"
                placeholder="不限制"
                style="width: 100%"
                @update:value="value => setNumberProp('maxCount', value)"
              >
                <template #suffix>个</template>
              </n-input-number>
            </n-form-item>

            <n-form-item>
              <template #label>
                <div class="label-with-desc">
                  <span>多选</span>
                  <span class="label-hint">允许一次选择多个文件</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('multiple') ?? true"
                @update:value="value => setBooleanProp('multiple', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 计算字段 ========== -->
          <template v-else-if="field.type === FieldType.CALCULATED">
            <n-form-item label="计算公式" required>
              <FormulaEditor
                v-model:formula="formulaValue"
                v-model:dependencies="formulaDependencies"
                :all-fields="allFields"
                @update="handleUpdate"
              />
            </n-form-item>

            <n-form-item label="小数位数">
              <n-input-number
                :value="getNumberProp('precision') ?? 2"
                :min="0"
                :max="10"
                placeholder="默认 2"
                style="width: 100%"
                @update:value="value => setNumberProp('precision', value)"
              >
                <template #suffix>位</template>
              </n-input-number>
            </n-form-item>
          </template>

          <!-- ========== 评分字段 ========== -->
          <template v-else-if="field.type === FieldType.RATE">
            <n-form-item label="星星数量">
              <n-slider
                :value="getNumberProp('count') ?? 5"
                :min="1"
                :max="10"
                :step="1"
                :marks="rateMarks"
                @update:value="value => setNumberProp('count', Array.isArray(value) ? value[0] : value)"
              />
            </n-form-item>

            <n-form-item>
              <template #label>
                <div class="label-with-desc">
                  <span>允许半星</span>
                </div>
              </template>
              <n-switch
                :value="getBooleanProp('allowHalf') ?? false"
                @update:value="value => setBooleanProp('allowHalf', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 开关字段 ========== -->
          <template v-else-if="field.type === FieldType.SWITCH">
            <n-form-item label="开启时的值">
              <n-input
                :value="getStringProp('checkedValue') ?? ''"
                placeholder="true"
                @update:value="value => setStringProp('checkedValue', value)"
              />
            </n-form-item>

            <n-form-item label="关闭时的值">
              <n-input
                :value="getStringProp('uncheckedValue') ?? ''"
                placeholder="false"
                @update:value="value => setStringProp('uncheckedValue', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 描述文本 ========== -->
          <template v-else-if="field.type === FieldType.DESCRIPTION">
            <n-form-item label="描述内容" required>
              <n-input
                :value="getStringProp('content') ?? ''"
                type="textarea"
                :rows="6"
                placeholder="请输入描述内容"
                :maxlength="1000"
                show-count
                @update:value="value => setStringProp('content', value)"
              />
            </n-form-item>
          </template>

          <!-- ========== 通用属性 ========== -->
          <n-form-item v-if="!isLayoutField">
            <template #label>
              <div class="label-with-desc">
                <span>禁用</span>
                <span class="label-hint">禁止用户编辑此字段</span>
              </div>
            </template>
            <n-switch
              :value="getBooleanProp('disabled') ?? false"
              @update:value="value => setBooleanProp('disabled', value)"
            />
          </n-form-item>
        </n-form>
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormField, FieldProps, FieldPropValue, SelectOption } from '@/types/field'
import { FieldType } from '@/types/field'
import OptionsEditor from './OptionsEditor.vue'
import FormulaEditor from './FormulaEditor.vue'

interface Props {
  field: FormField
  allFields: FormField[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update', updates: Partial<FormField>): void
}>()

const localProps = ref<FieldProps>({ ...props.field.props })

const BYTES_IN_MB = 1024 * 1024
const DEFAULT_MAX_SIZE_MB = 10
const rowMarks = { 2: '2', 4: '4', 6: '6', 8: '8', 10: '10' }
const rateMarks = { 1: '1', 5: '5', 10: '10' }

const toNumber = (value: FieldPropValue | undefined): number | undefined =>
  typeof value === 'number' ? value : undefined

const getMaxSizeMB = (value: FieldPropValue | undefined) => {
  const size = toNumber(value)
  return size !== undefined ? size / BYTES_IN_MB : DEFAULT_MAX_SIZE_MB
}

const maxSizeMB = ref<number>(getMaxSizeMB(props.field.props.maxSize))

watch(
  () => props.field.props,
  (newProps: FieldProps) => {
    localProps.value = { ...newProps }
    maxSizeMB.value = getMaxSizeMB(newProps.maxSize)
  },
  { deep: true }
)

const isTextField = computed(() => (
  [FieldType.TEXT, FieldType.TEXTAREA, FieldType.PHONE, FieldType.EMAIL] as FieldType[]
).includes(props.field.type))

const isSelectField = computed(() => (
  [FieldType.SELECT, FieldType.RADIO, FieldType.CHECKBOX] as FieldType[]
).includes(props.field.type))

const isDateField = computed(() => (
  [FieldType.DATE, FieldType.DATE_RANGE, FieldType.TIME, FieldType.DATETIME] as FieldType[]
).includes(props.field.type))

const isLayoutField = computed(() => (
  [FieldType.DIVIDER, FieldType.DESCRIPTION] as FieldType[]
).includes(props.field.type))

const handleUpdate = () => {
  emit('update', { props: { ...localProps.value } })
}

const assignProp = (key: string, value: FieldPropValue | undefined) => {
  if (value === undefined) {
    delete localProps.value[key]
  } else {
    localProps.value[key] = value
  }
  handleUpdate()
}

const getStringProp = (key: string): string | undefined => {
  const value = localProps.value[key]
  return typeof value === 'string' ? value : undefined
}

const setStringProp = (key: string, value: string | null | undefined) => {
  assignProp(key, value ?? undefined)
}

const getNumberProp = (key: string): number | undefined => {
  const value = localProps.value[key]
  return typeof value === 'number' ? value : undefined
}

const setNumberProp = (key: string, value: number | null | undefined) => {
  assignProp(key, typeof value === 'number' && !Number.isNaN(value) ? value : undefined)
}

const getBooleanProp = (key: string): boolean | undefined => {
  const value = localProps.value[key]
  return typeof value === 'boolean' ? value : undefined
}

const setBooleanProp = (key: string, value: boolean) => {
  assignProp(key, value)
}

const handleMaxSizeUpdate = (value: number | null) => {
  maxSizeMB.value = value ?? DEFAULT_MAX_SIZE_MB
  assignProp('maxSize', typeof value === 'number' ? value * BYTES_IN_MB : undefined)
}

const isSelectOptionArray = (options: unknown): options is SelectOption[] => {
  if (!Array.isArray(options)) {
    return false
  }
  return options.every(option =>
    typeof option === 'object' && option !== null && 'label' in option && 'value' in option
  )
}

const selectOptions = computed<SelectOption[]>(() => {
  const options = localProps.value.options
  return isSelectOptionArray(options) ? options : []
})

const handleOptionsUpdate = (options: SelectOption[]) => {
  assignProp('options', options)
}

const formulaValue = computed<string>({
  get: () => getStringProp('formula') ?? '',
  set: value => setStringProp('formula', value)
})

const formulaDependencies = computed<string[]>({
  get: () => {
    const value = localProps.value.dependencies
    if (Array.isArray(value)) {
      return value.filter((item): item is string => typeof item === 'string')
    }
    return []
  },
  set: value => assignProp('dependencies', value)
})
</script>

<style scoped lang="scss">
.props-config {
  height: 100%;
}

.config-content {
  padding: 0 4px;

  :deep(.n-form-item) {
    margin-bottom: 24px;

    &:last-child {
      margin-bottom: 0;
    }
  }
}

.label-with-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .label-hint {
    font-size: 12px;
    font-weight: 400;
    color: var(--n-text-color-3);
    line-height: 1.5;
  }
}

.field-hint {
  font-size: 12px;
  color: var(--n-text-color-3);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .config-content {
    padding: 0;
  }
}
</style>