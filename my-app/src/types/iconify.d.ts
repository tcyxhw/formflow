/**
 * Iconify Vue 类型声明（如果还有类型问题）
 */
declare module '@iconify/vue' {
    import { DefineComponent } from 'vue'
    
    export const Icon: DefineComponent<{
      icon: string
      color?: string
      width?: string | number
      height?: string | number
      rotate?: number
      flip?: 'horizontal' | 'vertical' | 'horizontal,vertical'
      inline?: boolean
    }>
  }