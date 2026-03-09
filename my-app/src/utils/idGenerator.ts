/**
 * ID生成器
 */

let fieldIdCounter = 0
let ruleIdCounter = 0

export const generateFieldId = (): string => {
  return `field_${Date.now()}_${++fieldIdCounter}`
}

export const generateRuleId = (): string => {
  return `rule_${Date.now()}_${++ruleIdCounter}`
}

export const generateGroupId = (): string => {
  return `group_${Date.now()}`
}