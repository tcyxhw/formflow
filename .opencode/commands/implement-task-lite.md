---
description: 轻量实现一个开发任务，先简要分析，再修改，再做简洁自检
subtask: true
---

You are implementing a normal development task in this repository.

User task:
$ARGUMENTS

Follow this workflow.

## Step 1: Before editing, first print:

## 修改前分析

This section must contain:

### 1. 当前理解
- Briefly summarize the current relevant implementation
- Explain where the requested behavior likely lives

### 2. 预计受影响文件
- List the likely files to touch
- If only one file is expected, say that explicitly

### 3. 最小改动方案
- Explain the smallest reasonable implementation approach
- Avoid unrelated refactoring

### 4. 风险与不确定点
- List any obvious risk or uncertainty
- If none, say: 当前无明显风险点

Keep this section concise.

## Step 2: Implement
Make the minimum necessary code changes only.
Do not expand scope without explicit user approval.
Prefer existing patterns, existing files, and local consistency.

## Step 3: After editing, print:

## 改动报告

This section must contain:

### 1. 改动清单
- Which files were changed
- What was changed in each file

### 2. 影响范围
- What behavior or UI area is affected

### 3. 风险点
- Any remaining risk
- If none, say: 无明显功能风险

### 4. 行为变化
- Describe whether behavior changed
- If behavior is unchanged except for the requested adjustment, say so clearly

## Step 4: Then print:

## 规则合规自检

Use this decision logic:

### 低风险任务
If the task is mainly:
- style / layout / text / small display fix
- a small localized logic fix
- fully following an existing pattern

Then keep this section short and output:

- 本次为低风险或局部变更。
- 涉及规则：简要列出或写“主要涉及最小改动、保持行为稳定、一致性复用”
- 合规判断：未发现明显偏离
- 盲区判断：无明显规则盲区

### 非低风险任务
If not low risk, briefly answer:

#### 1. 涉及哪些规则
#### 2. 是否有偏离
#### 3. 是否有规则盲区或需要猜测的地方

Keep this section concise and practical.

## Step 5: Finally print:

## 规则进化结论

This section must contain:

### 是否发现规则盲区
- 无
or
- Briefly list real gaps worth recording

### 是否有候选新规则
- 无
or
- Briefly list possible rule directions

### 是否建议后续运行 /review-commit
Use practical judgment:
- Tiny isolated change: usually no
- Multi-file / cross-layer / growing complexity: yes

## Hard constraints
- Do not skip these four top-level sections:
  - 修改前分析
  - 改动报告
  - 规则合规自检
  - 规则进化结论
- Keep output concise and developer-friendly
- Do not turn a small coding task into a heavy audit report
- Do not auto-write stable or experimental rule files
