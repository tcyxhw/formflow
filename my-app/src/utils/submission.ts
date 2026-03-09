// src/utils/submission.ts
/**
 * 提交数据转换工具
 */
import type { AttachmentInfo } from '@/types/attachment'
import type { SubmissionData } from '@/types/submission'

type RangeTuple = [unknown, unknown]
type RangeObject = NonNullable<SubmissionData['date_range']>

const toStringValue = (value: unknown): string => (value ?? '') as string

const isRangeTuple = (value: unknown): value is RangeTuple => Array.isArray(value) && value.length === 2

const isRangeObject = (value: unknown): value is RangeObject =>
  typeof value === 'object' && value !== null && 'start' in value && 'end' in value

const isNumberArray = (value: unknown[]): value is number[] =>
  value.every((item) => typeof item === 'number')

const isAttachmentInfo = (value: unknown): value is AttachmentInfo =>
  typeof value === 'object' && value !== null && 'id' in value && typeof (value as AttachmentInfo).id === 'number'

const isAttachmentInfoArray = (value: unknown[]): value is AttachmentInfo[] =>
  value.every((item) => isAttachmentInfo(item))

/**
 * 前端（Naive/Element 表单）数据 → 后端存储格式
 */
export const transformToBackend = (data: SubmissionData): SubmissionData => {
  const result: SubmissionData = JSON.parse(JSON.stringify(data || {}))

  const dateRangeValue = data?.date_range as unknown
  if (isRangeTuple(dateRangeValue)) {
    const [start, end] = dateRangeValue
    result.date_range = {
      start: toStringValue(start),
      end: toStringValue(end),
    }
  }

  const timeRangeValue = data?.time_range as unknown
  if (isRangeTuple(timeRangeValue)) {
    const [start, end] = timeRangeValue
    result.time_range = {
      start: toStringValue(start),
      end: toStringValue(end),
    }
  }

  const attachmentsValue = data?.attachments as unknown
  if (Array.isArray(attachmentsValue)) {
    if (isNumberArray(attachmentsValue)) {
      result.attachments = attachmentsValue
    } else if (isAttachmentInfoArray(attachmentsValue)) {
      result.attachments = attachmentsValue.map((item) => item.id)
    }
  }

  return result
}

/**
 * 后端存储格式 → 前端展示格式
 */
export const transformToFrontend = (data: SubmissionData): SubmissionData => {
  const result: SubmissionData = JSON.parse(JSON.stringify(data || {}))

  const dateRangeValue = data?.date_range as unknown
  if (isRangeObject(dateRangeValue)) {
    const { start, end } = dateRangeValue
    result.date_range = [start, end] as unknown as SubmissionData['date_range']
  }

  const timeRangeValue = data?.time_range as unknown
  if (isRangeObject(timeRangeValue)) {
    const { start, end } = timeRangeValue
    result.time_range = [start, end] as unknown as SubmissionData['time_range']
  }

  return result
}
