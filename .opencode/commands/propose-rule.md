---
description: 从已验证证据生成规则提案，写入提案隔离目录
agent: rule-proposer
subtask: true
---

# Propose Rule

基于 `review_evidence.md` 中的高质量证据生成规则提案。

## 输入
@standards/review_evidence.md
@standards/10_rule_proposal_template.md
@standards/03_python_rules_stable.md
@standards/04_python_rules_experimental.md
@standards/05_vue3_rules_stable.md
@standards/06_vue3_rules_experimental.md

---

## 执行规则

### Step 0：检查丢弃记录
先读取归档区中的 `❌ 已丢弃` 记录。
如果本次候选与历史丢弃项属于同类问题，必须说明：
- 为什么这次不同
- 为什么这次值得重新提案

否则不要重复生成低价值提案。

### Step 1：筛选候选项
优先筛选：
- 级别为 `validated` 的条目

次优先筛选：
- 级别为 `candidate`
- 且出现次数 >= 3
- 且严重性不低于中

排除：
- `📋 已提案`
- `✅ 已解决`
- `❌ 已丢弃`

如果没有符合条件的项，输出以下信息并结束：

当前无符合条件的候选。
- validated 条目数：0
- 高频 candidate 条目数：0
建议继续开发积累证据，或运行 `/review-commit` 验证现有 candidate。

### Step 2：与现有规则去重
对每个候选检查：
- 是否已被 stable 完全覆盖
- 是否已被 experimental 基本覆盖
- 是否只是某条规则的修订建议而不是新规则

结论分三类：
1. 完全覆盖 → 跳过
2. 部分覆盖 → 生成为规则修订建议
3. 完全未覆盖 → 生成为新规则提案

### Step 3：生成提案
每条提案必须包含以下字段：

- proposal_id: `PROP-YYYYMMDD-序号`
- created: 日期
- source_evidence: 对应证据标题列表
- category: Python / Vue3 / 通用
- type: 新规则 / 规则修订
- target_file: 目标 experimental 文件
- severity: 高 / 中
- status: pending_review

正文部分必须包含：
1. 规则名称
2. 规则内容
3. 正例（来自项目实际代码，标注文件路径）
4. 反例（来自 review 证据或项目代码，标注文件路径）
5. 适用场景
6. 不适用场景
7. 与现有规则的关系
8. 证据链
   - 首次发现
   - 确认验证
   - 最终验证

### Step 4：写入提案文件
将提案写入：

`standards/rule_proposals/<YYYYMMDD>-<category>.md`

例如：
- `standards/rule_proposals/20260324-python.md`
- `standards/rule_proposals/20260324-vue3.md`

如果同日同分类文件已存在，则追加到末尾。

### Step 5：更新 `review_evidence.md`
对已生成提案的条目：
- 标记为 `📋 已提案`
- 从活跃区移入归档区
- 同步更新状态看板

---

## 输出格式

1. 生成的提案
表格列：
- 编号
- 规则名称
- 分类
- 类型
- 来源证据数
- 写入文件

2. 跳过的条目
表格列：
- 条目
- 跳过原因

3. 后续建议
- 请人工审核 `standards/rule_proposals/<文件名>`
- 审核通过后，再手动复制到对应 experimental 文件
- 若不通过，请把丢弃原因回写到 `review_evidence.md`

---

## 严格约束

1. 绝不写入 stable 规则文件
2. 绝不写入 experimental 规则文件
3. 只能写入 `standards/rule_proposals/`
4. 每条提案必须有真实代码正例和反例
5. 证据不足宁可不提
