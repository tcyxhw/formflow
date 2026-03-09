// src/types/global.d.ts
/**
 * 全局类型定义
 */

import type { ApiDialogBridge, ApiMessageBridge } from '@/types/api'

declare global {
  interface Window {
    $message: ApiMessageBridge
    $dialog: ApiDialogBridge
  }
}

export {}