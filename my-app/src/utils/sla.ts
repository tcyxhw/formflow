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

export const formatProcessState = (state?: string | null): string => {
  if (!state) return '进行中'
  switch (state) {
    case 'finished':
      return '已完成'
    case 'canceled':
      return '已终止'
    case 'running':
    default:
      return '进行中'
  }
}

export const processStateTag = (state?: string | null): TagType => {
  if (!state || state === 'running') return 'info'
  if (state === 'finished') return 'success'
  if (state === 'canceled') return 'warning'
  return 'default'
}
