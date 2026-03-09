<template>
    <div class="formula-editor">
      <!-- 公式输入 -->
      <div class="formula-input-wrapper">
        <n-input
          v-model:value="localFormula"
          type="textarea"
          placeholder="请输入计算公式，如: ${price} * ${quantity}"
          :rows="5"
          @blur="handleUpdate"
        >
          <template #prefix>
            <Icon icon="carbon:formula" />
          </template>
        </n-input>
        
        <!-- 验证结果 -->
        <div v-if="validationError" class="validation-error">
          <Icon icon="carbon:warning-alt" />
          <span>{{ validationError }}</span>
        </div>
        
        <div v-else-if="localFormula" class="validation-success">
          <Icon icon="carbon:checkmark-outline" />
          <span>公式格式正确</span>
        </div>
      </div>
      
      <!-- 依赖字段选择 -->
      <div class="dependency-section">
        <div class="section-label">
          <Icon icon="carbon:link" />
          <span>依赖字段</span>
        </div>
        <n-select
          v-model:value="localDependencies"
          multiple
          placeholder="选择公式中使用的字段"
          :options="availableFieldOptions"
          :max-tag-count="3"
          @update:value="handleUpdate"
        />
        <div class="field-hint">
          选择公式中引用的字段，确保在这些字段有值时才计算
        </div>
      </div>
      
      <!-- 函数帮助 -->
      <n-collapse arrow-placement="right" class="help-collapse">
        <n-collapse-item title="可用函数" name="functions">
          <template #header>
            <div class="collapse-header">
              <Icon icon="carbon:catalog" />
              <span>可用函数</span>
            </div>
          </template>
          
          <div class="function-grid">
            <div
              v-for="func in FORMULA_FUNCTIONS"
              :key="func.name"
              class="function-card"
              @click="insertFunction(func.name)"
            >
              <div class="function-name">{{ func.name }}()</div>
              <div class="function-label">{{ func.label }}</div>
              <div class="function-example">{{ func.example }}</div>
            </div>
          </div>
        </n-collapse-item>
        
        <n-collapse-item title="可用字段" name="fields">
          <template #header>
            <div class="collapse-header">
              <Icon icon="carbon:data-1" />
              <span>可用字段</span>
            </div>
          </template>
          
          <div class="field-tags">
            <n-tag
              v-for="field in availableFields"
              :key="field.id"
              size="small"
              class="field-tag"
              @click="insertField(field.id)"
            >
              <template #icon>
                <Icon :icon="FIELD_TYPE_ICONS[field.type]" />
              </template>
              {{ field.label }}
            </n-tag>
          </div>
        </n-collapse-item>
        
        <n-collapse-item title="语法说明" name="syntax">
          <template #header>
            <div class="collapse-header">
              <Icon icon="carbon:document" />
              <span>语法说明</span>
            </div>
          </template>
          
          <div class="syntax-help">
            <div class="help-item">
              <div class="help-title">引用字段</div>
              <div class="help-code">${'{'}fieldId{'}'}</div>
              <div class="help-desc">使用 ${'{'}字段ID{'}'} 引用其他字段的值</div>
            </div>
            
            <div class="help-item">
              <div class="help-title">运算符</div>
              <div class="help-code">+ - * / %</div>
              <div class="help-desc">支持基本算术运算</div>
            </div>
            
            <div class="help-item">
              <div class="help-title">函数调用</div>
              <div class="help-code">functionName(arg1, arg2)</div>
              <div class="help-desc">调用内置函数进行计算</div>
            </div>
            
            <div class="help-item">
              <div class="help-title">示例</div>
              <div class="help-code">
                ${'{'}price{'}'} * ${'{'}quantity{'}'}<br>
                diffDays(${'{'}end_date{'}'}, ${'{'}start_date{'}'})<br>
                round(${'{'}score{'}'} * 0.8, 2)
              </div>
            </div>
          </div>
        </n-collapse-item>
      </n-collapse>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  import { Icon } from '@iconify/vue'
  import type { FormField } from '@/types/field'
  import { FIELD_TYPE_ICONS } from '@/constants/fieldTypes'
  import { FORMULA_FUNCTIONS } from '@/constants/formulaFunctions'
  
  interface Props {
    formula: string
    dependencies: string[]
    allFields: FormField[]
  }
  
  const props = defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update:formula', formula: string): void
    (e: 'update:dependencies', dependencies: string[]): void
    (e: 'update'): void
  }>()
  
  const localFormula = ref(props.formula)
  const localDependencies = ref([...props.dependencies])
  const validationError = ref('')
  
  watch(
    () => props.formula,
    (newFormula) => {
      localFormula.value = newFormula
      validateFormula()
    }
  )
  
  watch(
    () => props.dependencies,
    (newDeps) => {
      localDependencies.value = [...newDeps]
    }
  )
  
  // 可用字段（排除当前字段和计算字段）
  const availableFields = computed(() => {
    return props.allFields.filter(f => f.type !== 'calculated')
  })
  
  const availableFieldOptions = computed(() => {
    return availableFields.value.map(f => ({
      label: f.label,
      value: f.id,
    }))
  })
  
  const insertFunction = (funcName: string) => {
    localFormula.value += `${funcName}()`
    handleUpdate()
  }
  
  const insertField = (fieldId: string) => {
    localFormula.value += `\${${fieldId}}`
    
    // 自动添加到依赖
    if (!localDependencies.value.includes(fieldId)) {
      localDependencies.value.push(fieldId)
    }
    
    handleUpdate()
  }
  
  const handleUpdate = () => {
    validateFormula()
    
    emit('update:formula', localFormula.value)
    emit('update:dependencies', localDependencies.value)
    emit('update')
  }
  
  const validateFormula = () => {
    validationError.value = ''
    
    if (!localFormula.value) {
      validationError.value = '公式不能为空'
      return
    }
    
    // 提取公式中引用的字段
    const pattern = /\$\{(\w+)\}/g
    const matches = localFormula.value.matchAll(pattern)
    const referencedFields = Array.from(matches, m => m[1])
    
    // 检查引用的字段是否都在依赖列表中
    for (const fieldId of referencedFields) {
      if (!localDependencies.value.includes(fieldId)) {
        validationError.value = `字段 ${fieldId} 未在依赖列表中`
        return
      }
      
      if (!availableFields.value.find(f => f.id === fieldId)) {
        validationError.value = `字段 ${fieldId} 不存在`
        return
      }
    }
  }
  </script>
  
  <style scoped lang="scss">
  .formula-editor {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .formula-input-wrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .validation-error {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: var(--n-error-color-suppl);
    border-radius: 6px;
    font-size: 13px;
    color: var(--n-error-color);
    
    svg {
      flex-shrink: 0;
      font-size: 16px;
    }
  }
  
  .validation-success {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: var(--n-success-color-suppl);
    border-radius: 6px;
    font-size: 13px;
    color: var(--n-success-color);
    
    svg {
      flex-shrink: 0;
      font-size: 16px;
    }
  }
  
  .dependency-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    .section-label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      font-weight: 500;
      color: var(--n-text-color-1);
      
      svg {
        font-size: 16px;
        color: var(--n-color-target);
      }
    }
    
    .field-hint {
      font-size: 12px;
      color: var(--n-text-color-3);
      line-height: 1.5;
    }
  }
  
  .help-collapse {
    margin-top: 8px;
  }
  
  .collapse-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    
    svg {
      font-size: 16px;
    }
  }
  
  .function-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 8px;
  }
  
  .function-card {
    padding: 12px;
    background: var(--n-color-target);
    border: 1px solid var(--n-border-color);
    border-radius: 6px;
    cursor: pointer;
    transition: all 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
    
    &:hover {
      border-color: var(--n-color-target);
      background: var(--n-color-target);
      box-shadow: 0 2px 8px rgba(24, 160, 88, 0.1);
    }
    
    &:active {
      transform: scale(0.98);
    }
    
    .function-name {
      font-size: 13px;
      font-weight: 500;
      color: var(--n-color-target);
      font-family: monospace;
      margin-bottom: 4px;
    }
    
    .function-label {
      font-size: 12px;
      color: var(--n-text-color-2);
      margin-bottom: 4px;
    }
    
    .function-example {
      font-size: 11px;
      color: var(--n-text-color-3);
      font-family: monospace;
      line-height: 1.4;
    }
  }
  
  .field-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .field-tag {
    cursor: pointer;
    transition: all 180ms ease-out;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    &:active {
      transform: translateY(0);
    }
  }
  
  .syntax-help {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .help-item {
    .help-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--n-text-color-1);
      margin-bottom: 6px;
    }
    
    .help-code {
      padding: 8px 12px;
      background: var(--n-color-target);
      border: 1px solid var(--n-border-color);
      border-radius: 4px;
      font-family: monospace;
      font-size: 12px;
      color: var(--n-color-target);
      margin-bottom: 6px;
      line-height: 1.6;
    }
    
    .help-desc {
      font-size: 12px;
      color: var(--n-text-color-3);
      line-height: 1.5;
    }
  }
  
  /* 响应式 */
  @media (max-width: 768px) {
    .function-grid {
      grid-template-columns: 1fr;
    }
  }
  
  /* 运动减弱支持 */
  @media (prefers-reduced-motion: reduce) {
    .function-card,
    .field-tag {
      transition: none;
    }
  }
  </style>