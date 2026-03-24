<!-- src\App.vue -->
<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <!-- ✅ 使用内部组件来初始化实例 -->
          <AppContent />
          <!-- ✅ 添加全局样式 -->
          <n-global-style />
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { defineComponent, h, onMounted } from 'vue'
import { 
  NConfigProvider, 
  NMessageProvider, 
  NDialogProvider,
  NNotificationProvider,
  NGlobalStyle,
  useMessage,
  useDialog,
  type GlobalThemeOverrides
} from 'naive-ui'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTenantStore } from '@/stores/tenant'
import { setNaiveUIInstances } from '@/utils/request'
import { setGuardMessageInstance } from '@/router/guards'

// ✅ 主题配置
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#18a058',
    primaryColorHover: '#36ad6a',
    primaryColorPressed: '#0c7a43',
    primaryColorSuppl: '#36ad6a',
    infoColor: '#2080f0',
    successColor: '#18a058',
    warningColor: '#f0a020',
    errorColor: '#d03050',
    textColorBase: '#000000',
    textColor1: 'rgb(31, 34, 37)',
    textColor2: 'rgb(51, 54, 57)',
    textColor3: 'rgb(118, 124, 130)',
    borderColor: '#e5e7eb',
    borderRadius: '8px',
    fontWeightStrong: '600',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusLarge: '8px',
    borderRadiusSmall: '6px',
    paddingMedium: '0 16px',
    heightMedium: '36px',
  },
  Input: {
    borderRadius: '8px',
    heightMedium: '36px',
  },
  Card: {
    borderRadius: '12px',
    paddingMedium: '20px',
  },
  Tag: {
    borderRadius: '6px',
  },
  Form: {
    labelFontSizeTopMedium: '14px',
    labelTextColor: 'rgb(51, 54, 57)',
    feedbackFontSizeMedium: '12px',
  },
}

// ✅ 定义内部组件，在 Provider 内部调用 useMessage/useDialog
const AppContent = defineComponent({
  name: 'AppContent',
  setup() {
    const authStore = useAuthStore()
    const tenantStore = useTenantStore()
    
    // ✅ 现在可以安全地调用了，因为已经在 Provider 内部
    const message = useMessage()
    const dialog = useDialog()

    onMounted(async () => {
      // 设置全局实例
      setNaiveUIInstances(message, dialog)
      setGuardMessageInstance(message)
      
      // 初始化时检查登录状态
      await authStore.checkAuth()
      
      // 如果需要初始化租户信息
      if (!tenantStore.hasTenant) {
        tenantStore.initTenant()
      }
    })

    // 渲染 RouterView
    return () => h(RouterView)
  }
})
</script>

<style>
/* ✅ 全局基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', 
    'Arial', 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
  font-size: 14px;
  line-height: 1.5;
  color: #1f2937;
  background: #f5f7fa;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
}

/* ✅ 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ✅ 禁用系统默认的焦点框 */
*:focus-visible {
  outline: 2px solid #18a058;
  outline-offset: 2px;
}

/* ✅ 选中文本样式 */
::selection {
  background-color: rgba(24, 160, 88, 0.2);
  color: inherit;
}

/* ✅ 运动减弱支持 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ✅ 打印样式 */
@media print {
  body {
    background: white;
  }
  
  /* 隐藏不需要打印的元素 */
  nav,
  .no-print {
    display: none !important;
  }
}
</style>