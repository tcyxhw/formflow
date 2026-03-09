/**
 * vuedraggable 类型声明
 */
declare module 'vuedraggable' {
    import { DefineComponent } from 'vue'
    
    const draggable: DefineComponent<{
      list?: any[]
      modelValue?: any[]
      itemKey?: string | ((item: any) => any)
      tag?: string
      clone?: (item: any) => any
      move?: (evt: any, originalEvent: any) => boolean | void
      componentData?: Record<string, any>
      handle?: string
      filter?: string
      animation?: number
      group?: string | { name: string; pull?: boolean | string; put?: boolean | string }
      sort?: boolean
      disabled?: boolean
      ghostClass?: string
      chosenClass?: string
      dragClass?: string
      dataIdAttr?: string
      forceFallback?: boolean
      fallbackClass?: string
      fallbackOnBody?: boolean
      fallbackTolerance?: number
      scroll?: boolean | HTMLElement
      scrollSensitivity?: number
      scrollSpeed?: number
      bubbleScroll?: boolean
    }>
    
    export default draggable
  }