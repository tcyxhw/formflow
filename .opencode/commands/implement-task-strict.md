---
description: 严格实现一个开发任务，强制完整分析、最小改动、自检与规则演进判断
subtask: true
---

You are implementing a repository task under strict workflow control.

User task:
$ARGUMENTS

Follow this workflow strictly.

## Step 1: Before any editing, first inspect the minimum necessary context and print:

## 修改前分析

This section must contain all items below.

### 1. 对现有实现的理解
- Summarize the current implementation relevant to this task
- Explain where the current behavior lives
- Explain any nearby dependencies or coupling

### 2. 受影响的文件
- List the files likely to be touched
- Distinguish direct files and possible related files
- If scope is uncertain, say that explicitly

### 3. 最小改动方案
- Describe the smallest implementation plan
- Explain why this is the minimum viable change
- Explicitly avoid unrelated refactoring

### 4. 明确不会改变的行为
- State which behaviors, APIs, events, side effects, or flows must remain unchanged

### 5. 潜在风险点与不确定点
- List risk, ambiguity, dependency, migration cost, contract impact, or unknowns
- If none, say: 当前无明显风险点

Do not start editing before this section is printed.

## Step 2: Implement carefully
- Make only the necessary changes
- Follow existing repository style and local patterns
- Do not expand scope without explicit approval
- If the task turns out to require a larger structural change than expected, say so clearly

## Step 3: After editing, print:

## 改动报告

This section must contain:

### 1. 改动清单
- Which files were changed
- What changed in each file
- If a file was inspected but not modified, do not list it as changed

### 2. 影响范围
- What functionality, UI, API, data flow, or behavior may be affected

### 3. 风险点
- Remaining risks after implementation
- If none, say: 无明显功能风险

### 4. 行为变化
- Describe before vs after if behavior changed
- If only the requested output / display / layout changed, say so clearly

## Step 4: Then print:

## 规则合规自检

Always answer all items below.

### Q1 — 涉及哪些规则？
List the relevant repository rules, or clearly name the rule themes involved.

### Q2 — 是否完全遵守？
For each relevant rule or rule theme, state:
- 遵守
- 偏离
with a short explanation.

### Q3 — 是否做了规则未覆盖的决策？
Say whether this task required a technical decision not clearly covered by existing rules.

### Q4 — 是否有规则描述不清导致需要猜测？
Say whether any rule boundary was ambiguous or required interpretation.

### Q5 — 是否有规则在实际执行中感觉不合理？
Say whether any rule felt too strict, too weak, outdated, or impractical.

## Step 5: Finally print:

## 规则进化结论

This section must contain:

### 是否发现规则盲区
- 无
or
- A short list of real rule gaps worth recording

### 是否有候选新规则
- 无
or
- A short list of candidate rule directions

### 是否建议后续运行 /review-commit
Use practical judgment:
- If the task is multi-file, cross-layer, contract-sensitive, permission-sensitive, transaction-sensitive, or complexity is rising, recommend yes
- Otherwise no

## Hard constraints
- Do not skip these four top-level sections:
  - 修改前分析
  - 改动报告
  - 规则合规自检
  - 规则进化结论
- Keep answers structured and explicit
- Do not auto-write stable or experimental rule files
- Prefer correctness and traceability over brevity
