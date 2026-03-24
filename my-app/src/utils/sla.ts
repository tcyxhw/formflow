export type TagType = 'default' | 'success' | 'error' | 'info' | 'warning'
export type SlaLevel = 'unknown' | 'normal' | 'warning' | 'critical' | 'expired'

const MINUTE = 60

export const formatRemainingMinutes = (minutes?: number | null): string => {
  if (minutes === null || minutes === undefined) return '—'
  if (minutes <= 0) return '已超时'
  if (minutes < MINUTE) return `${minutes} 分钟`
  const hours = Math.floor(minutes / MINUTE)
  const rest = minutes % MINUTE
  if (rest === 0) return `${hours} 小时`
  return `${hours} 小时 ${rest} 分钟`
}

export const slaTagByMinutes = (minutes?: number | null): TagType => {
  if (minutes === null || minutes === undefined) return 'default'
  if (minutes <= 0) return 'error'
  if (minutes <= 60) return 'warning'
  return 'success'
}

export const normalizeSlaLevel = (level?: string | null): SlaLevel => {
  if (!level) return 'unknown'
  const lowered = level.toLowerCase()
  if (lowered === 'normal' || lowered === 'warning' || lowered === 'critical' || lowered === 'expired') {
    return lowered as SlaLevel
  }
  return 'unknown'
}

const SLA_LEVEL_LABELS: Record<SlaLevel, string> = {
  unknown: '状态未知',
  normal: '正常',
  warning: '预警',
  critical: '紧急',
  expired: '已超时'
}

export const slaLevelLabel = (level?: string | null): string => SLA_LEVEL_LABELS[normalizeSlaLevel(level)]

export const slaTagByLevel = (level?: string | null, minutes?: number | null): TagType => {
  const normalized = normalizeSlaLevel(level)
  switch (normalized) {
    case 'normal':
      return 'success'
    case 'warning':
      return 'warning'
    case 'critical':
      return 'error'
    case 'expired':
      return 'error'
    case 'unknown':
    default:
      return slaTagByMinutes(minutes)
  }
}

/**
 * 流程状态说明：
 * - running: 进行中 - 审批未到达结束节点且未超时
 * - finished: 已完成 - 到达结束节点
 * - stopped: 已停止 - 未完成并超时
 */
export const formatProcessState = (state?: string | null, isOverdue?: boolean): string => {
  if (!state) {
    // 没有状态时，根据是否超时判断
    return isOverdue ? '已停止' : '进行中'
  }
  switch (state) {
    case 'finished':
      return '已完成'
    case 'stopped':
    case 'canceled':
      return '已停止'
    case 'running':
    default:
      // running 状态下，如果超时了也显示已停止
      return isOverdue ? '已停止' : '进行中'
  }
}

export const processStateTag = (state?: string | null, isOverdue?: boolean): TagType => {
  if (!state || state === 'running') {
    return isOverdue ? 'error' : 'info'
  }
  if (state === 'finished') return 'success'
  if (state === 'stopped' || state === 'canceled') return 'error'
  return 'default'
}
