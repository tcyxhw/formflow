export type TimelineTagType = 'default' | 'success' | 'error' | 'info' | 'warning'

const ACTION_LABEL_MAP: Record<string, string> = {
  approve: '已通过',
  reject: '已拒绝',
  transfer: '已转交',
  delegate: '已委托',
  add_sign: '已加签',
  claim: '已认领',
  release: '已释放',
  cancel: '已撤销',
  auto_pass: '系统通过'
}

export const formatActionLabel = (action?: string | null, fallback = '待处理'): string => {
  if (!action) return fallback
  const lower = action.toLowerCase()
  return ACTION_LABEL_MAP[lower] || action
}

export const formatActorLabel = (userId?: number | null, actorName?: string | null): string => {
  if (actorName) return actorName
  if (userId) return `用户 #${userId}`
  return '系统'
}

export const timelineActionTag = (action?: string | null): TimelineTagType => {
  const lower = (action || '').toLowerCase()
  if (lower === 'approve' || lower === 'auto_pass') return 'success'
  if (lower === 'reject' || lower === 'cancel') return 'error'
  if (lower === 'transfer' || lower === 'delegate' || lower === 'add_sign') return 'warning'
  if (lower === 'claim' || lower === 'release') return 'info'
  return 'default'
}
