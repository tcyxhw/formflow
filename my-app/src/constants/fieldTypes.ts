// src\constants\fieldTypes.ts
/**
 * 字段类型配置
 */
import { FieldType } from '@/types/field'

export { FieldType } // ✅ 确保导出 FieldType 枚举

export const FIELD_GROUPS = [
  {
    name: '基础字段',
    icon: 'carbon:text-creation',
    types: [
      FieldType.TEXT,
      FieldType.TEXTAREA,
      FieldType.NUMBER,
    ]
  },
  {
    name: '选择字段',
    icon: 'carbon:list-dropdown',
    types: [
      FieldType.SELECT,
      FieldType.RADIO,
      FieldType.CHECKBOX,
      FieldType.SWITCH,
    ]
  },
  {
    name: '日期时间',
    icon: 'carbon:calendar',
    types: [
      FieldType.DATE,
      FieldType.DATE_RANGE,
      FieldType.TIME,
      FieldType.DATETIME,
    ]
  },
  {
    name: '高级字段',
    icon: 'carbon:application',
    types: [
      FieldType.RATE,
      FieldType.UPLOAD,
      FieldType.CALCULATED,
    ]
  },
  {
    name: '布局组件',
    icon: 'carbon:layout',
    types: [
      FieldType.DIVIDER,
      FieldType.DESCRIPTION,
    ]
  }
] as const

export const FIELD_TYPE_LABELS: Record<FieldType, string> = {
  [FieldType.TEXT]: '单行文本',
  [FieldType.TEXTAREA]: '多行文本',
  [FieldType.NUMBER]: '数字',
  [FieldType.PHONE]: '手机号',
  [FieldType.EMAIL]: '邮箱',
  [FieldType.DATE]: '日期',
  [FieldType.DATE_RANGE]: '日期范围',
  [FieldType.TIME]: '时间',
  [FieldType.DATETIME]: '日期时间',
  [FieldType.SELECT]: '下拉选择',
  [FieldType.RADIO]: '单选框',
  [FieldType.CHECKBOX]: '复选框',
  [FieldType.SWITCH]: '开关',
  [FieldType.RATE]: '评分',
  [FieldType.UPLOAD]: '文件上传',
  [FieldType.CALCULATED]: '计算字段',
  [FieldType.DIVIDER]: '分割线',
  [FieldType.DESCRIPTION]: '描述文本',
}

export const FIELD_TYPE_ICONS: Record<FieldType, string> = {
  [FieldType.TEXT]: 'carbon:text-short-paragraph',
  [FieldType.TEXTAREA]: 'carbon:text-long-paragraph',
  [FieldType.NUMBER]: 'carbon:hashtag',
  [FieldType.PHONE]: 'carbon:phone',
  [FieldType.EMAIL]: 'carbon:email',
  [FieldType.DATE]: 'carbon:calendar',
  [FieldType.DATE_RANGE]: 'carbon:calendar-heat-map',
  [FieldType.TIME]: 'carbon:time',
  [FieldType.DATETIME]: 'carbon:events',
  [FieldType.SELECT]: 'carbon:list-dropdown',
  [FieldType.RADIO]: 'carbon:radio-button',
  [FieldType.CHECKBOX]: 'carbon:checkbox',
  [FieldType.SWITCH]: 'carbon:toggle',
  [FieldType.RATE]: 'carbon:star',
  [FieldType.UPLOAD]: 'carbon:upload',
  [FieldType.CALCULATED]: 'carbon:calculator',
  [FieldType.DIVIDER]: 'carbon:horizontal-rule',
  [FieldType.DESCRIPTION]: 'carbon:document',
}