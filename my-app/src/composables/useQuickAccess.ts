// src/composables/useQuickAccess.ts
/**
 * 快捷入口组合函数
 * 
 * 功能:
 * - 管理快捷入口表单列表状态
 * - 提供添加、移除、查询快捷入口的方法
 * - 实现本地状态管理和持久化
 * 
 * 依赖: workspace API, localStorage
 */

import { ref, computed } from 'vue'
import {
  getQuickAccessForms,
  addQuickAccess,
  removeQuickAccess
} from '@/api/workspace'
import type { FillableFormItem } from '@/types/workspace'

const STORAGE_KEY = 'formflow_quick_access_cache'

/**
 * 快捷入口组合函数
 * 
 * @returns 快捷入口状态和方法
 */
export function useQuickAccess() {
  // 快捷入口表单列表
  const quickAccessForms = ref<FillableFormItem[]>([])
  
  // 加载状态
  const loading = ref(false)
  
  // 错误信息
  const error = ref<string | null>(null)
  
  // 计算属性：快捷入口表单ID集合（用于快速判断某表单是否在快捷入口中）
  const quickAccessFormIds = computed(() => {
    return new Set(quickAccessForms.value.map(form => form.id))
  })
  
  /**
   * 从localStorage加载缓存的快捷入口数据
   */
  const loadFromCache = () => {
    try {
      const cached = localStorage.getItem(STORAGE_KEY)
      if (cached) {
        const data = JSON.parse(cached)
        // 验证缓存数据的有效性（不超过1小时）
        if (data.timestamp && Date.now() - data.timestamp < 3600000) {
          quickAccessForms.value = data.forms || []
          return true
        }
      }
    } catch (e) {
      console.warn('Failed to load quick access cache:', e)
    }
    return false
  }
  
  /**
   * 保存快捷入口数据到localStorage
   */
  const saveToCache = () => {
    try {
      const data = {
        forms: quickAccessForms.value,
        timestamp: Date.now()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (e) {
      console.warn('Failed to save quick access cache:', e)
    }
  }
  
  /**
   * 加载快捷入口表单列表
   * 优先从缓存加载，然后从API获取最新数据
   */
  const loadQuickAccess = async (useCache = true) => {
    // 如果允许使用缓存且缓存加载成功，则先显示缓存数据
    if (useCache && loadFromCache()) {
      // 缓存加载成功，但仍在后台刷新数据
      fetchQuickAccess(false)
      return
    }
    
    // 缓存不可用或不使用缓存，直接从API加载
    await fetchQuickAccess(true)
  }
  
  /**
   * 从API获取快捷入口表单列表
   * 
   * @param showLoading 是否显示加载状态
   */
  const fetchQuickAccess = async (showLoading = true) => {
    if (showLoading) {
      loading.value = true
    }
    error.value = null
    
    try {
      const { data } = await getQuickAccessForms()
      quickAccessForms.value = data.items
      saveToCache()
    } catch (e: any) {
      error.value = e?.message || '加载快捷入口失败'
      quickAccessForms.value = []
    } finally {
      if (showLoading) {
        loading.value = false
      }
    }
  }
  
  /**
   * 添加表单到快捷入口（带乐观更新）
   * 
   * @param formId 表单ID
   * @param formData 表单数据（可选，用于乐观更新）
   * @returns 是否添加成功
   */
  const addToQuickAccess = async (formId: number, formData?: FillableFormItem): Promise<boolean> => {
    // 检查是否已存在
    if (quickAccessFormIds.value.has(formId)) {
      return true // 已存在，视为成功
    }
    
    // 乐观更新：如果提供了表单数据，立即添加到本地列表
    if (formData) {
      quickAccessForms.value.push(formData)
      saveToCache()
    }
    
    try {
      await addQuickAccess(formId)
      // 添加成功后重新加载列表（确保数据一致性）
      await fetchQuickAccess(false)
      return true
    } catch (e: any) {
      error.value = e?.message || '添加到快捷入口失败'
      // 添加失败，重新加载以恢复正确状态
      await fetchQuickAccess(false)
      return false
    }
  }
  
  /**
   * 从快捷入口移除表单
   * 
   * @param formId 表单ID
   * @returns 是否移除成功
   */
  const removeFromQuickAccess = async (formId: number): Promise<boolean> => {
    // 检查是否存在
    if (!quickAccessFormIds.value.has(formId)) {
      return true // 不存在，视为成功
    }
    
    try {
      await removeQuickAccess(formId)
      // 乐观更新：立即从本地列表中移除
      quickAccessForms.value = quickAccessForms.value.filter(
        form => form.id !== formId
      )
      saveToCache()
      return true
    } catch (e: any) {
      error.value = e?.message || '从快捷入口移除失败'
      // 移除失败，重新加载以恢复正确状态
      await fetchQuickAccess(false)
      return false
    }
  }
  
  /**
   * 检查表单是否在快捷入口中
   * 
   * @param formId 表单ID
   * @returns 是否在快捷入口中
   */
  const isInQuickAccess = (formId: number): boolean => {
    return quickAccessFormIds.value.has(formId)
  }
  
  /**
   * 切换表单的快捷入口状态（带乐观更新）
   * 
   * @param formId 表单ID
   * @param formData 表单数据（可选，用于乐观更新）
   * @returns 是否操作成功
   */
  const toggleQuickAccess = async (formId: number, formData?: FillableFormItem): Promise<boolean> => {
    if (isInQuickAccess(formId)) {
      return await removeFromQuickAccess(formId)
    } else {
      return await addToQuickAccess(formId, formData)
    }
  }
  
  /**
   * 清除缓存
   */
  const clearCache = () => {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch (e) {
      console.warn('Failed to clear quick access cache:', e)
    }
  }
  
  return {
    // 状态
    quickAccessForms,
    loading,
    error,
    quickAccessFormIds,
    
    // 方法
    loadQuickAccess,
    addToQuickAccess,
    removeFromQuickAccess,
    isInQuickAccess,
    toggleQuickAccess,
    clearCache
  }
}
