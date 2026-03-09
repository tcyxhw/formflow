// src\constants\formulaFunctions.ts
/**
 * 公式函数定义（基于后端 FormulaService）
 */

export const FORMULA_FUNCTIONS = [
    // 数学函数
    { name: 'abs', label: '绝对值', syntax: 'abs(number)', example: 'abs(-5) → 5' },
    { name: 'round', label: '四舍五入', syntax: 'round(number, precision)', example: 'round(3.1415, 2) → 3.14' },
    { name: 'min', label: '最小值', syntax: 'min(a, b, ...)', example: 'min(1, 2, 3) → 1' },
    { name: 'max', label: '最大值', syntax: 'max(a, b, ...)', example: 'max(1, 2, 3) → 3' },
    { name: 'sum', label: '求和', syntax: 'sum(a, b, ...)', example: 'sum(1, 2, 3) → 6' },
    { name: 'avg', label: '平均值', syntax: 'avg(a, b, ...)', example: 'avg(1, 2, 3) → 2' },
    { name: 'floor', label: '向下取整', syntax: 'floor(number)', example: 'floor(3.9) → 3' },
    { name: 'ceil', label: '向上取整', syntax: 'ceil(number)', example: 'ceil(3.1) → 4' },
    
    // 日期函数
    { name: 'diffDays', label: '日期相差天数', syntax: 'diffDays(end, start)', example: 'diffDays(${end_date}, ${start_date})' },
    { name: 'diffHours', label: '日期相差小时', syntax: 'diffHours(end, start)', example: 'diffHours(${end_time}, ${start_time})' },
    { name: 'today', label: '今天日期', syntax: 'today()', example: 'today() → 2024-01-15' },
    { name: 'now', label: '当前时间', syntax: 'now()', example: 'now() → 2024-01-15T10:30:00' },
    
    // 文本函数
    { name: 'concat', label: '字符串拼接', syntax: 'concat(a, b, ...)', example: 'concat(${firstName}, " ", ${lastName})' },
    { name: 'length', label: '字符串长度', syntax: 'length(string)', example: 'length(${name})' },
    { name: 'upper', label: '转大写', syntax: 'upper(string)', example: 'upper(${name})' },
    { name: 'lower', label: '转小写', syntax: 'lower(string)', example: 'lower(${name})' },
    { name: 'trim', label: '去空格', syntax: 'trim(string)', example: 'trim(${name})' },
    
    // 条件函数
    { name: 'if', label: '条件判断', syntax: 'if(condition, trueValue, falseValue)', example: 'if(${age} >= 18, "成年", "未成年")' },
  ] as const
  
  export const FORMULA_SYNTAX_HELP = `
  # 公式语法说明
  
  ## 1. 引用字段值
  \${fieldId}                     // 引用字段值
  
  ## 2. 运算符
  +  -  *  /  %                  // 算术运算
  >  <  >=  <=  ==  !=           // 比较运算
  and  or  not                   // 逻辑运算
  
  ## 3. 函数调用
  functionName(arg1, arg2, ...)
  
  ## 4. 示例
  diffDays(\${end_date}, \${start_date})                    // 日期相差天数
  \${price} * \${quantity}                                  // 价格乘以数量
  if(\${age} >= 18, '成年', '未成年')                       // 条件判断
  round(\${score} * 0.8, 2)                                // 四舍五入
  `