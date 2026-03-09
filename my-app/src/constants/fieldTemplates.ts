// src\constants\fieldTemplates.ts
/**
 * 字段默认模板
 */
import { FieldType } from '@/types/field'
import type { FormField } from '@/types/field'

export const FIELD_TEMPLATES: Record<FieldType, Partial<FormField>> = {
  [FieldType.TEXT]: {
    type: FieldType.TEXT,
    label: '单行文本',
    required: false,
    props: {
      placeholder: '请输入',
      maxLength: 200,
      clearable: true,
    },
  },
  
  [FieldType.TEXTAREA]: {
    type: FieldType.TEXTAREA,
    label: '多行文本',
    required: false,
    props: {
      placeholder: '请输入',
      rows: 4,
      maxLength: 1000,
      showWordLimit: true,
    },
  },
  
  [FieldType.NUMBER]: {
    type: FieldType.NUMBER,
    label: '数字',
    required: false,
    props: {
      placeholder: '请输入',
      step: 1,
    },
  },
  
  [FieldType.PHONE]: {
    type: FieldType.PHONE,
    label: '手机号',
    required: false,
    props: {
      placeholder: '请输入手机号',
      maxLength: 11,
    },
    validation: {
      pattern: '^1[3-9]\\d{9}$',
      message: '请输入正确的手机号',
    },
  },
  
  [FieldType.EMAIL]: {
    type: FieldType.EMAIL,
    label: '邮箱',
    required: false,
    props: {
      placeholder: '请输入邮箱',
    },
    validation: {
      pattern: '^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
      message: '请输入正确的邮箱',
    },
  },
  
  [FieldType.SELECT]: {
    type: FieldType.SELECT,
    label: '下拉选择',
    required: false,
    props: {
      placeholder: '请选择',
      options: [
        { label: '选项1', value: '1' },
        { label: '选项2', value: '2' },
      ],
      clearable: true,
    },
  },
  
  [FieldType.RADIO]: {
    type: FieldType.RADIO,
    label: '单选框',
    required: false,
    props: {
      options: [
        { label: '选项1', value: '1' },
        { label: '选项2', value: '2' },
      ],
    },
  },
  
  [FieldType.CHECKBOX]: {
    type: FieldType.CHECKBOX,
    label: '复选框',
    required: false,
    props: {
      options: [
        { label: '选项1', value: '1' },
        { label: '选项2', value: '2' },
      ],
    },
  },
  
  [FieldType.SWITCH]: {
    type: FieldType.SWITCH,
    label: '开关',
    required: false,
    props: {
      checkedValue: true,
      uncheckedValue: false,
    },
  },
  
  [FieldType.DATE]: {
    type: FieldType.DATE,
    label: '日期',
    required: false,
    props: {
      placeholder: '请选择日期',
      format: 'yyyy-MM-dd',
      valueFormat: 'yyyy-MM-dd',
      type: 'date',
      clearable: true,
    },
  },
  
  [FieldType.DATE_RANGE]: {
    type: FieldType.DATE_RANGE,
    label: '日期范围',
    required: false,
    props: {
      placeholder: ['开始日期', '结束日期'],
      format: 'yyyy-MM-dd',
      valueFormat: 'yyyy-MM-dd',
      clearable: true,
    },
  },
  
  [FieldType.TIME]: {
    type: FieldType.TIME,
    label: '时间',
    required: false,
    props: {
      placeholder: '请选择时间',
      format: 'HH:mm:ss',
      valueFormat: 'HH:mm:ss',
    },
  },
  
  [FieldType.DATETIME]: {
    type: FieldType.DATETIME,
    label: '日期时间',
    required: false,
    props: {
      placeholder: '请选择日期时间',
      format: 'yyyy-MM-dd HH:mm:ss',
      valueFormat: 'yyyy-MM-dd HH:mm:ss',
      type: 'datetime',
    },
  },
  
  [FieldType.UPLOAD]: {
    type: FieldType.UPLOAD,
    label: '文件上传',
    required: false,
    props: {
      action: '/api/v1/upload',
      accept: '*',
      maxSize: 10 * 1024 * 1024,
      maxCount: 5,
    },
  },
  
  [FieldType.RATE]: {
    type: FieldType.RATE,
    label: '评分',
    required: false,
    props: {
      count: 5,
      allowHalf: false,
    },
  },
  
  [FieldType.CALCULATED]: {
    type: FieldType.CALCULATED,
    label: '计算字段',
    required: false,
    props: {
      formula: '',
      dependencies: [],
      precision: 2,
      readonly: true,
    },
  },
  
  [FieldType.DIVIDER]: {
    type: FieldType.DIVIDER,
    label: '分割线',
    required: false,
    props: {},
  },
  
  [FieldType.DESCRIPTION]: {
    type: FieldType.DESCRIPTION,
    label: '描述文本',
    required: false,
    props: {
      content: '这是一段描述文本',
    },
  },
}