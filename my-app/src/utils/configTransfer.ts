// src/utils/configTransfer.ts
/**
 * AI 配置传递工具
 * 
 * 用于在页面间传递大型配置对象
 */

import type { AIFormGenerateResponse } from '@/types/ai'

const AI_CONFIG_KEY = 'TEMP_AI_CONFIG'

type StoredAIConfig = AIFormGenerateResponse['config']

export const ConfigTransfer = {
  /**
   * 保存配置到 sessionStorage
   */
  saveConfig(config: StoredAIConfig): void {
    try {
      const configJson = JSON.stringify(config)
      sessionStorage.setItem(AI_CONFIG_KEY, configJson)
      console.log('[ConfigTransfer] 配置已保存，大小:', configJson.length, '字符')
    } catch (error) {
      console.error('[ConfigTransfer] 保存配置失败:', error)
    }
  },

  /**
   * 从 sessionStorage 读取配置
   */
  getConfig(): StoredAIConfig | null {
    try {
      const configJson = sessionStorage.getItem(AI_CONFIG_KEY)
      if (!configJson) {
        console.log('[ConfigTransfer] 未找到配置')
        return null
      }

      const config = JSON.parse(configJson)
      console.log('[ConfigTransfer] 配置已读取')
      return config
    } catch (error) {
      console.error('[ConfigTransfer] 读取配置失败:', error)
      return null
    }
  },

  /**
   * 清除配置
   */
  clearConfig(): void {
    sessionStorage.removeItem(AI_CONFIG_KEY)
    console.log('[ConfigTransfer] 配置已清除')
  },

  /**
   * 检查是否有配置
   */
  hasConfig(): boolean {
    return sessionStorage.getItem(AI_CONFIG_KEY) !== null
  }
}