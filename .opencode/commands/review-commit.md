---
description: 审查 staged 或 branch diff，验证证据并升级候选规则
agent: rule-reviewer
subtask: true
---

# Review Commit

## 参数
$ARGUMENTS

如果 $ARGUMENTS 为空，则执行 Staged 模式。  
如果 $ARGUMENTS 非空（如 `origin/main`），则执行 Branch 模式。

---

## 预读信息

### Staged 模式信息
!`git diff --cached --stat -- .`
!`git diff --cached --name-only -- .`

### Branch 模式信息
!`git diff --stat $ARGUMENTS...HEAD -- . 2>/dev/null || echo "INVALID_REF"`
!`git diff --name-only $ARGUMENTS...HEAD -- . 2>/dev/null`
!`git log --oneline $ARGUMENTS..HEAD 2>/dev/null`

### 当前证据库
@standards/review_evidence.md

### 审查规范
@standards/08_review_checklist.md
@standards/09_review_prompt.md

---

## 执行规则

### Step 1：确定模式
- 如果参数为空：Staged 模式
- 如果参数不为空：Branch 模式
- 如果 ref 无效：明确指出 ref 无效并停止

### Step 2：评估规模
根据 `review_evidence.md` 中的审查配置判断：

#### 2A. 完整 review
如果文件数 <= 8 且总变更行数 <= 800：
- 直接读取完整 diff 审查

#### 2B. 分组 review
如果超出完整 review 阈值，但仍在分组 review 范围内：
- 先根据 `--name-only` 按目录 / 层级 / 语义拆成 2~4 组
- 每组分别读取 diff 审查
- 所有分组审查完成后，必须执行一次跨组交叉检查
- 最后合并结论

分组示例：
- `app/api + app/schemas`
- `app/services + app/models`
- `src/api + src/types`
- `src/views + src/components`

必须在报告中列出分组情况。

#### 分组 review 的跨组合并阶段
在所有分组审查完成后，必须执行一次跨组交叉检查，再合并最终结论。

重点检查：

1. 接口契约闭合
   - 接口组（api / schemas / types）的变更，是否与实现组（services / models / views）一致？
   - 后端 schema / response 变更，前端 api/types 是否同步？
   - 路由参数、返回结构、错误码、状态字段是否前后一致？

2. 实现依赖闭合
   - models 字段变化是否同步影响 services / serializers / validators / migrations？
   - service 层行为变化是否同步反映到 api 编排或调用方？
   - 是否存在一个组修改了某个模式，而另一个组仍沿用旧模式？

3. 规则模式一致性
   - 同一类场景在不同组中是否使用了不同实现策略？
   - 是否出现“组内看起来合理，但组间标准不一致”的情况？

4. 未闭合项标记
   - 如果存在组间依赖但当前审查无法确认是否闭合，必须在报告中列为“待验证跨组项”
   - 对于存在未闭合项的候选规则，不得直接升级为 validated

#### 2C. 抽查 review（仅兜底）
如果分组 review 仍明显过大：
- 选 3~5 个最关键文件
- 优先新文件、接口文件、service 核心文件
- 仅对这些文件做深入审查
- 必须列出未覆盖文件
- 必须明确说明本次结论可信度受限

### Step 3：执行审查

对于本次覆盖范围，检查以下内容：

#### 3.1 规则合规性
是否违反既有规则？

#### 3.2 跨文件一致性
如果变更涉及多个文件，检查：
- 模式一致性
- 接口完整性
- 命名一致性
- 错误处理一致性

#### 3.3 历史证据验证
逐条检查 `review_evidence.md` 中活跃条目：

对每条活跃证据做判断：

1. 本次 diff 是否相关？
   - 不相关：跳过

2. 如果相关，本次 diff 是：
   - 支持：该问题在本次 diff 中仍然存在或再次出现
   - 反驳：本次 diff 体现为有意修复
   - 部分支持：部分印证，但证据不足以升级

3. 给出建议：
   - `observation -> confirmed`
   - `confirmed -> candidate`
   - `candidate -> validated`
   - `-> ✅ 已解决`
   - `保持不变`

对于涉及跨层契约、前后端同步、schema/model/service/api 联动的问题，
只有在跨组交叉检查未发现未闭合项时，candidate 才能升级为 validated。

#### 3.4 新发现
如果本次 diff 中出现新的规则问题，按以下类型记录：
- 盲区
- 模糊
- 冲突
- 过严
- 过松
- 过时

新发现必须有具体 diff 证据。

#### 3.5 丢弃记录检查
检查归档区中的 `❌ 已丢弃` 记录：
- 如果新发现与某条已丢弃模式属于同类问题，必须说明为什么这次不同
- 如果没有本质区别，则不要重复提案

### Step 4：输出报告

按以下结构输出：

1. 基本信息
- 模式：Staged / Branch
- 基准：branch 模式时填写
- 变更文件数
- 总变更行数
- 覆盖方式：完整 / 分组 / 抽查

2. 覆盖范围
- 已覆盖
- 未覆盖（如无则写 无）

3. 规则违反
表格列：
- 文件:行号
- 违反规则
- 严重性
- 描述

4. 跨文件一致性
表格列：
- 检查项
- 结果
- 详情

检查项至少包括：
- 模式一致性
- 接口完整性
- 命名一致性
- 错误处理一致性

5. 跨组交叉检查
表格列：
- 检查项
- 结果
- 详情

检查项至少包括：
- 接口契约闭合
- 实现依赖闭合
- 前后端同步
- 规则模式一致性

6. 待验证跨组项
- 若无则写 无

7. 证据验证与状态变更
表格列：
- 条目标题
- 当前级别
- 本次验证
- diff 证据
- 建议操作

8. 新发现
表格列：
- 类型
- 标签
- 描述
- 文件:行号
- 建议级别
- 严重性

9. 结论
- ✅ 通过
- ⚠️ 通过但有注意事项
- 🔧 建议修复后再提交

### Step 5：回写 `review_evidence.md`
根据报告执行以下更新：

1. 新发现 → 追加到活跃证据区，初始级别为 `observation`
2. 升级项 → 更新对应条目级别
3. 已解决项 → 移入归档区并标记 `✅ 已解决`
4. 已提案项不再保留在活跃区
5. 同步更新状态看板表格
6. 更新出现次数和最后触发时间

---

## 重要约束

1. 不要修改任何代码文件
2. 不要自动写入 stable 规则文件
3. 不要自动写入 experimental 规则文件
4. 大 diff 时优先分组 review，抽查仅为最后兜底
5. 证据验证以当前 diff 为准，不以历史摘要文本为准
6. 如果覆盖不完整，必须明确说明
