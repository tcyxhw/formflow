# 云雾AI定价数据字段说明

## 模型信息字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| model_name | string | 模型唯一标识名称 |
| provider | string | 模型供应商 |
| input_price | float/null | 输入价格（按量计费） |
| output_price | float/null | 输出价格（按量计费） |
| model_price | float/null | 模型价格（按次/按张计费） |
| price_unit | string | 价格单位 |
| currency | string | 货币符号 |
| description | string | 模型描述 |
| tags | array | 功能标签 |
| billing_type | string | 计费类型 |
| model_multiplier | float/null | 模型倍率 |
| completion_multiplier | float/null | 补全倍率 |
| group_multiplier | float/null | 分组倍率 |

## 筛选选项字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| category | string | 筛选分类 |
| name | string | 选项名称 |
| count | int/null | 该选项的模型数量 |
| multiplier | string/null | 倍率（如x1.6） |