// src/stores/tenant.ts
/**
 * 租户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as tenantAPI from '@/api/tenant'
import type { Tenant } from '@/types/tenant'


export const useTenantStore = defineStore('tenant', () => {
  // 状态
  const currentTenant = ref<Tenant | null>(null)
  const tenantList = ref<Tenant[]>([])
  const loading = ref(false)
  
  // 计算属性
  const tenantId = computed(() => currentTenant.value?.id)
  const tenantName = computed(() => currentTenant.value?.name)
  const hasTenant = computed(() => !!currentTenant.value)
  
  /**
   * 从localStorage恢复租户信息
   */
  const initTenant = (): boolean => {
    const storedTenantId = localStorage.getItem('tenant_id')
    const storedTenantName = localStorage.getItem('tenant_name')
    
    if (storedTenantId && storedTenantName) {
      currentTenant.value = {
        id: parseInt(storedTenantId),
        name: storedTenantName
      }
      return true
    }
    return false
  }
  
  /**
   * 获取租户列表
   */
  const fetchTenantList = async (): Promise<boolean> => {
    loading.value = true
    try {
      const response = await tenantAPI.getTenantList()
      console.log("store中的请求的返回值：",response);
      
      if (response.code === 200 && response.data) {
        tenantList.value = response.data
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to fetch tenant list:', error)
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 选择租户
   */
  const selectTenant = (tenant: Tenant): void => {
    currentTenant.value = tenant
    localStorage.setItem('tenant_id', tenant.id.toString())
    localStorage.setItem('tenant_name', tenant.name)
  }
  
  /**
   * 验证当前租户
   */
  const validateCurrentTenant = async (): Promise<boolean> => {
    if (!currentTenant.value) return false
    
    try {
      const response = await tenantAPI.validateTenant(currentTenant.value.id)
      
      if (response.code === 200 && response.data?.valid) {
        return true
      }
      
      // 租户无效，清除
      clearTenant()
      return false
    } catch (error) {
      console.error('Failed to validate tenant:', error)
      return false
    }
  }
  
  /**
   * 清除租户信息
   */
  const clearTenant = (): void => {
    currentTenant.value = null
    localStorage.removeItem('tenant_id')
    localStorage.removeItem('tenant_name')
  }
  
  // 初始化
  initTenant()
  
  return {
    // 状态
    currentTenant: computed(() => currentTenant.value),
    tenantList: computed(() => tenantList.value),
    loading: computed(() => loading.value),
    tenantId,
    tenantName,
    hasTenant,
    
    // 方法
    fetchTenantList,
    selectTenant,
    validateCurrentTenant,
    clearTenant,
    initTenant
  }
})