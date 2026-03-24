

# 字段类型与运算符的准确对应关系

---

## 一、先确认你的表单系统有哪些字段类型

你的表单设计器里应该有这些组件，每个组件对应一个字段类型：

```
组件名称          字段类型编码          存储的值长什么样
──────────────────────────────────────────────────────────
单行文本          TEXT                 "张三"
多行文本          TEXTAREA             "这是一段很长的说明..."
数字              NUMBER               3  或  15000.5
单选              SINGLE_SELECT        "病假"
多选              MULTI_SELECT         ["紧急", "跨部门"]
日期              DATE                 "2024-12-01"
日期时间          DATETIME             "2024-12-01 14:30:00"
日期区间          DATE_RANGE           ["2024-12-01", "2024-12-05"]
人员单选          USER                 101（用户ID）
人员多选          USER_MULTI           [101, 102]
部门选择          DEPARTMENT           50（部门ID）
附件/图片         FILE                 [文件对象数组]
```

你先对照你的代码确认你到底有哪些字段类型，然后下面的映射表只取你有的部分就行。

---

## 二、每种字段类型对应哪些运算符

### TEXT（单行文本）

```
运算符              含义              值控件            value示例
────────────────────────────────────────────────────────────
EQUALS             等于              文本输入框         "张三"
NOT_EQUALS         不等于            文本输入框         "张三"
CONTAINS           包含              文本输入框         "张"
NOT_CONTAINS       不包含            文本输入框         "张"
IS_EMPTY           为空              不显示             null
IS_NOT_EMPTY       不为空            不显示             null
```

用户选了一个单行文本字段，比如"姓名"，运算符就只出现这6个。

---

### TEXTAREA（多行文本）

```
EQUALS             等于              文本输入框         "某段文字"
NOT_EQUALS         不等于            文本输入框         "某段文字"
CONTAINS           包含              文本输入框         "关键词"
NOT_CONTAINS       不包含            文本输入框         "关键词"
IS_EMPTY           为空              不显示             null
IS_NOT_EMPTY       不为空            不显示             null
```

和TEXT一样，因为本质都是文字。

---

### NUMBER（数字）

```
运算符              含义              值控件              value示例
────────────────────────────────────────────────────────────────
EQUALS             等于              数字输入框           3
NOT_EQUALS         不等于            数字输入框           3
GREATER_THAN       大于              数字输入框           3
GREATER_EQUAL      大于等于          数字输入框           3
LESS_THAN          小于              数字输入框           3
LESS_EQUAL         小于等于          数字输入框           3
BETWEEN            介于              两个数字输入框       [1, 5]
IS_EMPTY           为空              不显示               null
IS_NOT_EMPTY       不为空            不显示               null
```

**你说的"请假天数"就是这个类型。** 选了这个字段后运算符应该出现上面这9个，其中"大于""小于"这些才是数字字段最核心的运算符。你现在的问题就是这里没区分，所有字段都给的文本类型的运算符。

---

### SINGLE_SELECT（单选）

```
运算符              含义              值控件                      value示例
────────────────────────────────────────────────────────────────────────
EQUALS             等于              下拉单选（选项来自字段配置）   "病假"
NOT_EQUALS         不等于            下拉单选                     "病假"
IN                 属于              下拉多选                     ["病假", "事假"]
NOT_IN             不属于            下拉多选                     ["病假", "事假"]
IS_EMPTY           为空              不显示                       null
IS_NOT_EMPTY       不为空            不显示                       null
```

比如"请假类型"字段，选项有"事假/病假/年假"，用户选了这个字段后：
- 选"等于"→ 值控件变成下拉框，选项是事假/病假/年假，只能选一个
- 选"属于"→ 值控件变成多选下拉框，可以选多个，表示"值是这几个中的任何一个"

---

### MULTI_SELECT（多选）

```
运算符              含义              值控件              value示例
──────────────────────────────────────────────────────────────────
HAS_ANY            包含任一          下拉多选             ["紧急", "跨部门"]
HAS_ALL            包含全部          下拉多选             ["紧急", "跨部门"]
IS_EMPTY           为空              不显示               null
IS_NOT_EMPTY       不为空            不显示               null
```

多选字段的值本身是一个数组，所以不能用EQUALS，要用HAS_ANY/HAS_ALL。

- HAS_ANY：用户填的多选值中包含我指定的任意一个就算命中
- HAS_ALL：用户填的多选值中必须包含我指定的全部才算命中

---

### DATE（日期）

```
运算符              含义              值控件              value示例
──────────────────────────────────────────────────────────────────
EQUALS             等于              日期选择器           "2024-12-01"
NOT_EQUALS         不等于            日期选择器           "2024-12-01"
GREATER_THAN       晚于              日期选择器           "2024-12-01"
GREATER_EQUAL      不早于            日期选择器           "2024-12-01"
LESS_THAN          早于              日期选择器           "2024-12-01"
LESS_EQUAL         不晚于            日期选择器           "2024-12-01"
BETWEEN            介于              两个日期选择器       ["2024-01-01", "2024-12-31"]
IS_EMPTY           为空              不显示               null
IS_NOT_EMPTY       不为空            不显示               null
```

注意：日期类型的运算符编码和数字一样（GREATER_THAN、LESS_THAN），但前端**显示的中文名不一样**：
- 数字的 GREATER_THAN 显示 "大于"
- 日期的 GREATER_THAN 显示 "晚于"

---

### DATETIME（日期时间）

```
和 DATE 完全一样的运算符列表，只是值控件从日期选择器换成日期时间选择器。
```

---

### DATE_RANGE（日期区间）

```
这种字段存的是 ["开始日期", "结束日期"]，用在条件里比较特殊。

你有两种处理方式：

方式A：拆成两个虚拟字段
  在字段列表里把一个日期区间字段拆成"请假开始日期"和"请假结束日期"两个可选字段
  每个虚拟字段当作普通 DATE 类型来处理
  这样用户可以分别对开始日期和结束日期设条件

方式B：直接不支持对日期区间做条件判断
  日期区间通常会自动计算出一个"天数"字段
  用户直接对天数（NUMBER类型）做判断就行
  比如"请假天数 > 3"
```

建议用方式A或方式B看你实际情况选一个。

---

### USER（人员单选）

```
运算符              含义              值控件              value示例
──────────────────────────────────────────────────────────────────
EQUALS             等于              人员选择器(单选)     101
NOT_EQUALS         不等于            人员选择器(单选)     101
IN                 属于              人员选择器(多选)     [101, 102, 103]
NOT_IN             不属于            人员选择器(多选)     [101, 102, 103]
IS_EMPTY           为空              不显示               null
IS_NOT_EMPTY       不为空            不显示               null
```

比如表单里有个"项目负责人"字段，条件可以设成"项目负责人 等于 张三"或"项目负责人 属于 [张三, 李四, 王五]"。

---

### USER_MULTI（人员多选）

```
HAS_ANY            包含任一          人员选择器(多选)     [101, 102]
HAS_ALL            包含全部          人员选择器(多选)     [101, 102]
IS_EMPTY           为空              不显示               null
IS_NOT_EMPTY       不为空            不显示               null
```

和MULTI_SELECT逻辑一样，只是值控件换成人员选择器。

---

### DEPARTMENT（部门选择）

```
EQUALS             等于              部门选择器(单选)     50
NOT_EQUALS         不等于            部门选择器(单选)     50
IN                 属于              部门选择器(多选)     [50, 51, 52]
NOT_IN             不属于            部门选择器(多选)     [50, 51, 52]
IS_EMPTY           为空              不显示               null
IS_NOT_EMPTY       不为空            不显示               null
```

---

### FILE（附件/图片）

```
IS_EMPTY           为空（没上传）     不显示              null
IS_NOT_EMPTY       不为空（有上传）   不显示              null
```

附件只能判断有没有上传，不能判断内容。

---

## 三、完整映射配置（直接拿去写代码）

前端维护一份配置，核心就是这个 Map：

```
FIELD_OPERATOR_MAP = {

  "TEXT":           ["EQUALS", "NOT_EQUALS", "CONTAINS", "NOT_CONTAINS", "IS_EMPTY", "IS_NOT_EMPTY"],

  "TEXTAREA":       ["EQUALS", "NOT_EQUALS", "CONTAINS", "NOT_CONTAINS", "IS_EMPTY", "IS_NOT_EMPTY"],

  "NUMBER":         ["EQUALS", "NOT_EQUALS", "GREATER_THAN", "GREATER_EQUAL", "LESS_THAN", "LESS_EQUAL", "BETWEEN", "IS_EMPTY", "IS_NOT_EMPTY"],

  "SINGLE_SELECT":  ["EQUALS", "NOT_EQUALS", "IN", "NOT_IN", "IS_EMPTY", "IS_NOT_EMPTY"],

  "MULTI_SELECT":   ["HAS_ANY", "HAS_ALL", "IS_EMPTY", "IS_NOT_EMPTY"],

  "DATE":           ["EQUALS", "NOT_EQUALS", "GREATER_THAN", "GREATER_EQUAL", "LESS_THAN", "LESS_EQUAL", "BETWEEN", "IS_EMPTY", "IS_NOT_EMPTY"],

  "DATETIME":       ["EQUALS", "NOT_EQUALS", "GREATER_THAN", "GREATER_EQUAL", "LESS_THAN", "LESS_EQUAL", "BETWEEN", "IS_EMPTY", "IS_NOT_EMPTY"],

  "USER":           ["EQUALS", "NOT_EQUALS", "IN", "NOT_IN", "IS_EMPTY", "IS_NOT_EMPTY"],

  "USER_MULTI":     ["HAS_ANY", "HAS_ALL", "IS_EMPTY", "IS_NOT_EMPTY"],

  "DEPARTMENT":     ["EQUALS", "NOT_EQUALS", "IN", "NOT_IN", "IS_EMPTY", "IS_NOT_EMPTY"],

  "FILE":           ["IS_EMPTY", "IS_NOT_EMPTY"]
}
```

运算符的中文显示名，默认一套，日期类型覆盖一套：

```
OPERATOR_LABELS = {
  "EQUALS":        "等于",
  "NOT_EQUALS":    "不等于",
  "GREATER_THAN":  "大于",
  "GREATER_EQUAL": "大于等于",
  "LESS_THAN":     "小于",
  "LESS_EQUAL":    "小于等于",
  "BETWEEN":       "介于",
  "CONTAINS":      "包含",
  "NOT_CONTAINS":  "不包含",
  "IN":            "属于",
  "NOT_IN":        "不属于",
  "HAS_ANY":       "包含任一",
  "HAS_ALL":       "包含全部",
  "IS_EMPTY":      "为空",
  "IS_NOT_EMPTY":  "不为空"
}

// 日期类型的运算符显示名覆盖
DATE_OPERATOR_LABELS = {
  "GREATER_THAN":  "晚于",
  "GREATER_EQUAL": "不早于",
  "LESS_THAN":     "早于",
  "LESS_EQUAL":    "不晚于"
}
```

获取某个字段的运算符列表：

```
function getOperators(fieldType) {
  let operatorCodes = FIELD_OPERATOR_MAP[fieldType] || []
  
  return operatorCodes.map(code => {
    let label
    if ((fieldType === "DATE" || fieldType === "DATETIME") && DATE_OPERATOR_LABELS[code]) {
      label = DATE_OPERATOR_LABELS[code]
    } else {
      label = OPERATOR_LABELS[code]
    }
    return { code: code, label: label }
  })
}
```

---

## 四、前端联动逻辑

你现在的问题就是选字段后运算符没有跟着变。联动要做三件事：

### 第1步：选字段时触发

```
用户选了一个字段：
  ① 拿到这个字段的 fieldType
  ② 用 FIELD_OPERATOR_MAP[fieldType] 拿到运算符列表
  ③ 刷新运算符下拉框的选项
  ④ 清空之前选的运算符（因为之前的运算符在新类型下可能不存在）
  ⑤ 清空之前填的值
  ⑥ 隐藏值输入控件（等用户选了运算符再显示）
```

### 第2步：选运算符时触发

```
用户选了一个运算符：
  ① 清空之前填的值
  ② 根据运算符决定值控件的渲染方式：

     IS_EMPTY / IS_NOT_EMPTY:
       → 隐藏值控件

     BETWEEN:
       → 显示两个值输入控件
       → 控件类型由字段类型决定（NUMBER→两个数字框，DATE→两个日期框）

     IN / NOT_IN / HAS_ANY / HAS_ALL:
       → 显示多选控件
       → 控件类型由字段类型决定：
         SINGLE_SELECT → 下拉多选（选项来自字段配置）
         USER / USER_MULTI → 人员多选器
         DEPARTMENT → 部门多选器

     其他:
       → 显示单个值输入控件
       → 控件类型由字段类型决定：
         TEXT / TEXTAREA → 文本输入框
         NUMBER → 数字输入框
         DATE → 日期选择器
         DATETIME → 日期时间选择器
         SINGLE_SELECT → 下拉单选（选项来自字段配置）
         USER → 人员单选器
         DEPARTMENT → 部门单选器
```

### 第3步：值控件类型速查表

把字段类型和运算符组合起来，值控件到底长什么样：

```
字段类型           运算符                    值控件

TEXT              普通运算符                 文本输入框
TEXT              IS_EMPTY/IS_NOT_EMPTY     无

NUMBER            普通运算符                 数字输入框
NUMBER            BETWEEN                   两个数字输入框
NUMBER            IS_EMPTY/IS_NOT_EMPTY     无

SINGLE_SELECT     EQUALS/NOT_EQUALS         下拉单选（选项从字段配置读）
SINGLE_SELECT     IN/NOT_IN                 下拉多选（选项从字段配置读）
SINGLE_SELECT     IS_EMPTY/IS_NOT_EMPTY     无

MULTI_SELECT      HAS_ANY/HAS_ALL           下拉多选（选项从字段配置读）
MULTI_SELECT      IS_EMPTY/IS_NOT_EMPTY     无

DATE              普通运算符                 日期选择器
DATE              BETWEEN                   两个日期选择器
DATE              IS_EMPTY/IS_NOT_EMPTY     无

USER              EQUALS/NOT_EQUALS         人员选择器（单选）
USER              IN/NOT_IN                 人员选择器（多选）
USER              IS_EMPTY/IS_NOT_EMPTY     无

DEPARTMENT        EQUALS/NOT_EQUALS         部门选择器（单选）
DEPARTMENT        IN/NOT_IN                 部门选择器（多选）
DEPARTMENT        IS_EMPTY/IS_NOT_EMPTY     无

FILE              IS_EMPTY/IS_NOT_EMPTY     无
```

---

## 五、你现在代码里要改什么

你现在的问题是所有字段类型都给了同一套运算符，说明你的运算符列表是写死的，没有根据字段类型去取。

你需要做的事情：

```
① 在前端定义 FIELD_OPERATOR_MAP 这个映射配置（就是上面第三节那个Map）

② 在字段下拉框的 onChange 事件里：
   拿到选中字段的 fieldType
   用 fieldType 去 FIELD_OPERATOR_MAP 里取对应的运算符数组
   把运算符下拉框的选项替换成这个数组
   清空运算符和值

③ 在运算符下拉框的 onChange 事件里：
   根据当前字段类型 + 当前运算符，决定值控件怎么渲染
   清空值

④ 确保你的表单字段数据里带了 type 字段
   你从后端拿表单字段列表时，每个字段必须有 type 信息
   如果你现在的字段数据里没有 type，那运算符就没法区分
```

最关键的就是第④点：**你前端拿到的字段列表里每个字段必须有类型信息**。如果这个信息丢了，前面所有联动逻辑都做不了。