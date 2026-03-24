// src/stores/homeInteractive.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type Scenario = 'leave' | 'reimburse' | 'room' | 'award' | 'certificate'

export interface FieldSchema {
  id: string
  label: string
  type: string
  required?: boolean
  placeholder?: string
  options?: Array<{ label: string; value: string }>
}

export interface FlowNode {
  id: string
  name: string
  type: 'start' | 'user' | 'auto' | 'end'
  position: { x: number; y: number }
}

export interface FlowEdge {
  from: string
  to: string
  condition?: string
  active?: boolean
}

type ApprovalStrategy = 'all' | 'any' | 'percent'

interface LeaveControls {
  days: number
  medicalProof: boolean
}

interface ReimburseControls {
  amount: number
  needInvoice: boolean
  docsComplete: boolean
}

interface RoomControls {
  resourceId: string
  range: [Date, Date]
  bufferMin: number
}

interface AwardControls {
  approvers: number
  strategy: ApprovalStrategy
  percent: number
}

interface CertificateControls {
  urgent: boolean
  eSeal: boolean
}

type ScenarioControlMap = {
  leave: LeaveControls
  reimburse: ReimburseControls
  room: RoomControls
  award: AwardControls
  certificate: CertificateControls
}

export const useHomeInteractive = defineStore('homeInteractive', () => {
  // 当前场景
  const scenario = ref<Scenario>('leave')

  // 生成的表单 Schema
  const formSchema = ref<FieldSchema[]>([])

  // 控制条件
  const controls = ref<ScenarioControlMap>({
    leave: { days: 2, medicalProof: false },
    reimburse: { amount: 3000, needInvoice: true, docsComplete: true },
    room: { resourceId: 'room-a', range: [new Date(), new Date()] as [Date, Date], bufferMin: 5 },
    award: { approvers: 3, strategy: 'all', percent: 60 },
    certificate: { urgent: false, eSeal: true }
  })

  // 流程图数据 - 默认展示请假审批流程
  const flowData = ref<{ nodes: FlowNode[]; edges: FlowEdge[] }>({
    nodes: [
      { id: 'start', name: '提交申请', type: 'start', position: { x: 100, y: 200 } },
      { id: 'counselor', name: '辅导员审批', type: 'user', position: { x: 300, y: 200 } },
      { id: 'college', name: '学院审批', type: 'user', position: { x: 500, y: 150 } },
      { id: 'school', name: '校级审批', type: 'user', position: { x: 700, y: 100 } },
      { id: 'auto', name: '自动归档', type: 'auto', position: { x: 500, y: 250 } },
      { id: 'end', name: '完成', type: 'end', position: { x: 500, y: 320 } }
    ],
    edges: [
      { from: 'start', to: 'counselor', active: true },
      { from: 'counselor', to: 'auto', condition: '≤3天', active: true },
      { from: 'counselor', to: 'college', condition: '>3天', active: false },
      { from: 'college', to: 'auto', condition: '≤7天', active: false },
      { from: 'college', to: 'school', condition: '>7天', active: false },
      { from: 'school', to: 'auto', active: false },
      { from: 'auto', to: 'end', active: true }
    ]
  })

  // 自动审批决策
  const autoDecision = ref({
    pass: 70,
    reject: 10,
    manual: 20
  })

  // 预计处理时长（分钟）
  const etaMinutes = ref(120)

  // 场景配置映射
  const scenarioConfig = computed(() => {
    const configs = {
      leave: {
        name: '请假审批',
        icon: '🏖️',
        color: '#18a058',
        description: '智能分级审批，3 天以内自动通过',
        fields: [
          { id: 'type', label: '请假类型', type: 'select' },
          { id: 'days', label: '请假天数', type: 'number' },
          { id: 'reason', label: '请假事由', type: 'textarea' },
          { id: 'dateRange', label: '起止日期', type: 'date-range' }
        ]
      },
      reimburse: {
        name: '经费报销',
        icon: '💰',
        color: '#f0a020',
        description: '按金额自动路由，材料完整自动通过',
        fields: [
          { id: 'amount', label: '报销金额', type: 'number' },
          { id: 'category', label: '报销类目', type: 'select' },
          { id: 'invoice', label: '发票附件', type: 'attachment' },
          { id: 'desc', label: '费用说明', type: 'textarea' }
        ]
      },
      room: {
        name: '教室预约',
        icon: '🏫',
        color: '#2080f0',
        description: '实时冲突检测，自动缓冲时间',
        fields: [
          { id: 'resource', label: '教室选择', type: 'select' },
          { id: 'timeRange', label: '使用时段', type: 'time-range' },
          { id: 'purpose', label: '使用目的', type: 'text' },
          { id: 'attendees', label: '参与人数', type: 'number' }
        ]
      },
      award: {
        name: '活动评奖',
        icon: '🏆',
        color: '#d03050',
        description: '在线评审，自动汇总学分',
        fields: [
          { id: 'activityName', label: '活动名称', type: 'text' },
          { id: 'works', label: '作品提交', type: 'attachment' },
          { id: 'teamMembers', label: '团队成员', type: 'multiselect' },
          { id: 'selfEval', label: '自我评价', type: 'textarea' }
        ]
      },
      certificate: {
        name: '证明开具',
        icon: '📜',
        color: '#7c4dff',
        description: '电子签章，扫码验真',
        fields: [
          { id: 'certType', label: '证明类型', type: 'select' },
          { id: 'purpose', label: '用途说明', type: 'text' },
          { id: 'copies', label: '份数', type: 'number' },
          { id: 'urgent', label: '是否加急', type: 'checkbox' }
        ]
      }
    }
    return configs[scenario.value]
  })

  // 计算流程路径
  const computeFlow = () => {
    const nodes: FlowNode[] = []
    const edges: FlowEdge[] = []

    if (scenario.value === 'leave') {
      const days = controls.value.leave.days

      nodes.push(
        { id: 'start', name: '提交申请', type: 'start', position: { x: 100, y: 200 } },
        { id: 'counselor', name: '辅导员', type: 'user', position: { x: 300, y: 200 } },
        { id: 'college', name: '学院', type: 'user', position: { x: 500, y: 150 } },
        { id: 'school', name: '校级', type: 'user', position: { x: 700, y: 100 } },
        { id: 'end', name: '完成', type: 'end', position: { x: 500, y: 300 } }
      )

      edges.push({ from: 'start', to: 'counselor', active: true })

      if (days <= 3) {
        edges.push(
          { from: 'counselor', to: 'end', condition: '≤3天', active: true },
          { from: 'counselor', to: 'college', condition: '>3天', active: false },
          { from: 'college', to: 'school', condition: '>7天', active: false },
          { from: 'college', to: 'end', active: false },
          { from: 'school', to: 'end', active: false }
        )
      } else if (days <= 7) {
        edges.push(
          { from: 'counselor', to: 'end', condition: '≤3天', active: false },
          { from: 'counselor', to: 'college', condition: '3-7天', active: true },
          { from: 'college', to: 'end', active: true },
          { from: 'college', to: 'school', condition: '>7天', active: false },
          { from: 'school', to: 'end', active: false }
        )
      } else {
        edges.push(
          { from: 'counselor', to: 'end', condition: '≤3天', active: false },
          { from: 'counselor', to: 'college', condition: '>3天', active: true },
          { from: 'college', to: 'school', condition: '>7天', active: true },
          { from: 'college', to: 'end', active: false },
          { from: 'school', to: 'end', active: true }
        )
      }
    } else if (scenario.value === 'reimburse') {
      const amount = controls.value.reimburse.amount

      nodes.push(
        { id: 'start', name: '提交报销', type: 'start', position: { x: 100, y: 200 } },
        { id: 'manager', name: '部门主管', type: 'user', position: { x: 300, y: 200 } },
        { id: 'finance', name: '财务审核', type: 'user', position: { x: 500, y: 150 } },
        { id: 'leader', name: '分管领导', type: 'user', position: { x: 700, y: 100 } },
        { id: 'end', name: '完成', type: 'end', position: { x: 500, y: 300 } }
      )

      edges.push({ from: 'start', to: 'manager', active: true })

      if (amount <= 500) {
        edges.push(
          { from: 'manager', to: 'end', condition: '≤500', active: true },
          { from: 'manager', to: 'finance', condition: '>500', active: false },
          { from: 'finance', to: 'leader', condition: '>5000', active: false },
          { from: 'finance', to: 'end', active: false },
          { from: 'leader', to: 'end', active: false }
        )
      } else if (amount <= 5000) {
        edges.push(
          { from: 'manager', to: 'end', condition: '≤500', active: false },
          { from: 'manager', to: 'finance', condition: '500-5000', active: true },
          { from: 'finance', to: 'end', active: true },
          { from: 'finance', to: 'leader', condition: '>5000', active: false },
          { from: 'leader', to: 'end', active: false }
        )
      } else {
        edges.push(
          { from: 'manager', to: 'end', condition: '≤500', active: false },
          { from: 'manager', to: 'finance', condition: '>500', active: true },
          { from: 'finance', to: 'leader', condition: '>5000', active: true },
          { from: 'finance', to: 'end', active: false },
          { from: 'leader', to: 'end', active: true }
        )
      }
    }
    // ... 其他场景类似

    flowData.value = { nodes, edges }
  }

  // 更新控制参数
  const updateControl = (key: string, value: unknown) => {
    const current = controls.value[scenario.value]
    if (current && key in current) {
      ;(current as Record<string, unknown>)[key] = value as never
      computeFlow()
      updateMetrics()
    }
  }

  // 更新指标
  const updateMetrics = () => {
    const currentScenario = scenario.value
    const current = controls.value[currentScenario]

    if (currentScenario === 'leave') {
      const { days } = current as LeaveControls
      etaMinutes.value = days <= 3 ? 30 : days <= 7 ? 120 : 240
      autoDecision.value = {
        pass: days <= 3 ? 85 : 60,
        reject: 5,
        manual: days <= 3 ? 10 : 35
      }
    } else if (currentScenario === 'reimburse') {
      const { amount, docsComplete } = current as ReimburseControls
      etaMinutes.value = amount <= 500 ? 20 : amount <= 5000 ? 90 : 180
      autoDecision.value = {
        pass: docsComplete && amount <= 500 ? 90 : 50,
        reject: !docsComplete ? 30 : 5,
        manual: docsComplete ? 10 : 20
      }
    } else if (currentScenario === 'room') {
      const { bufferMin } = current as RoomControls
      etaMinutes.value = bufferMin <= 5 ? 15 : bufferMin <= 10 ? 30 : 60
      autoDecision.value = {
        pass: 90,
        reject: 2,
        manual: 8
      }
    } else if (currentScenario === 'award') {
      const { approvers, strategy, percent } = current as AwardControls
      etaMinutes.value = approvers <= 3 ? 20 : approvers <= 5 ? 45 : 90
      autoDecision.value = {
        pass: percent >= 70 ? 80 : 50,
        reject: 5,
        manual: percent >= 70 ? 15 : 45
      }
    } else if (currentScenario === 'certificate') {
      const { urgent, eSeal } = current as CertificateControls
      etaMinutes.value = urgent ? 30 : 15
      autoDecision.value = {
        pass: eSeal ? 95 : 70,
        reject: 3,
        manual: eSeal ? 2 : 27
      }
    } else {
      // 默认值
      autoDecision.value = {
        pass: 70,
        reject: 10,
        manual: 20
      }
    }
  }

  // 切换场景
  const changeScenario = (newScenario: Scenario) => {
    scenario.value = newScenario
    computeFlow()
    updateMetrics()
  }

  // 自然语言生成表单
  const generateFormFromNL = (input: string) => {
    // 简单的规则匹配
    const fields: FieldSchema[] = []

    if (input.includes('主题') || input.includes('标题')) {
      fields.push({ id: 'title', label: '主题', type: 'text', required: true })
    }
    if (input.includes('时间') || input.includes('日期')) {
      if (input.includes('起止') || input.includes('范围')) {
        fields.push({ id: 'dateRange', label: '起止时间', type: 'date-range', required: true })
      } else {
        fields.push({ id: 'date', label: '日期', type: 'date', required: true })
      }
    }
    if (input.includes('人数')) {
      fields.push({ id: 'attendees', label: '人数', type: 'number', required: true })
    }
    if (input.includes('设备')) {
      fields.push({
        id: 'equipment',
        label: '设备需求',
        type: 'multiselect',
        options: [
          { label: '投影仪', value: 'projector' },
          { label: '音响', value: 'audio' },
          { label: '麦克风', value: 'microphone' }
        ]
      })
    }
    if (input.includes('备注') || input.includes('说明')) {
      fields.push({ id: 'remarks', label: '备注', type: 'textarea' })
    }

    formSchema.value = fields
  }

  return {
    scenario,
    formSchema,
    controls,
    flowData,
    autoDecision,
    etaMinutes,
    scenarioConfig,
    changeScenario,
    updateControl,
    generateFormFromNL,
    computeFlow,
    updateMetrics
  }
})