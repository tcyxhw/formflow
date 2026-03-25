# Review Evidence — 规则盲区证据积累

> 本文件由 AI 在开发过程中持续维护。
> 它是规则盲区、规则缺陷、候选规则证据的单文件中心。
> 规则提案只能基于本文件中的已验证证据生成。

---

## 状态看板

<!-- 只保留活跃条目：observation / confirmed / candidate / validated -->
<!-- AI 每次新增、升级、解决、提案后，都应同步维护这张表 -->
<!-- 日常开发默认优先阅读此表，而不是通读全文 -->

| # | 标签 | 类型 | 标题 | 级别 | 严重性 | 出现次数 | 最后触发 |
|---|------|------|------|------|--------|----------|----------|
| 1 | api-contract / type-safety | 盲区 | category→category_id 前后端未同步 | observation | 高 | 1 | 2026-03-24 |
| 2 | performance | 盲区 | list_forms 权限过滤 N+1 查询 | observation | 高 | 1 | 2026-03-24 |
| 3 | data-model | 模糊 | 级联删除未检查 process_instance 外键 | observation | 中 | 1 | 2026-03-24 |
| 4 | dependency | 模糊 | 图标使用方式不一致 | observation | 低 | 1 | 2026-03-24 |

**活跃条目数**：4 / 15（达到 15 条时建议人工审核归档）

---

## 审查配置

### 完整 review 阈值
- 文件数：<= 8
- 总变更行数：<= 800

### 分组 review 阈值
- 文件数：<= 20
- 总变更行数：<= 2000

### 超大变更兜底策略
超过分组 review 阈值时，允许进入抽查模式，但必须：
1. 优先新文件
2. 优先接口/契约文件（schemas / api / types / models）
3. 优先 service 核心逻辑
4. 明确说明未覆盖范围

### 阈值提醒
- 累计修改文件数 >= 6
- 累计改动行数 >= 400
- 跨层联动时触发提醒

---

## 证据级别与升级条件

### observation
首次观察到的规则问题，仅记录，不急于规则化。

### confirmed
满足任一条件即可升级：
- 出现次数 >= 2
- 严重性为高
- 在 `/review-commit` 的真实 diff 中再次被印证

### candidate
满足全部条件才能升级：
- 已 confirmed
- 不是一次性业务细节
- 有复用性
- 可清晰表述为“应该 / 不应该”

### validated
满足全部条件才能升级：
- 已 candidate
- 在 `/review-commit` 中基于真实 diff 得到确认
- 有文件 / 函数 / 行号级证据
- 没有明显过拟合
- 如果是跨层 / 跨契约问题，跨组交叉检查未发现未闭合项

---

## 终态说明

- `📋 已提案`：已通过 `/propose-rule` 生成提案
- `✅ 已解决`：后续代码中已解决该问题
- `❌ 已丢弃`：人工确认不值得规则化，必须说明原因

---

## 活跃证据

<!-- AI 在此按时间倒序追加 -->
<!-- 每条记录必须保持完整字段 -->

### [2026-03-24 00:00] 盲区 | category→category_id 前后端未同步
- 文件：`backend/app/schemas/form_schemas.py` / `my-app/src/types/form.ts`
- 场景：后端 FormCreateRequest/FormUpdateRequest/FormQueryRequest 将 `category: str` 改为 `category_id: int`，但前端 FormCreateRequest 仍用 `category?: string`，FormListQuery 改为 `category?: number` 但字段名仍是 category 而非 category_id
- 当前做法：后端发送 category_id，前端发送 category，字段名+类型均不匹配
- 规则缺口：schema 字段重命名/类型变更时，缺少前后端契约同步检查机制
- 建议方向：考虑引入 OpenAPI spec 自动生成前端 types，或在 review 清单中增加"schema 变更时检查前端 types"项
- 级别：observation
- 严重性：高
- 标签：api-contract / type-safety
- 出现次数：1
- 最后触发：2026-03-24

### [2026-03-24 00:00] 盲区 | list_forms 权限过滤 N+1 查询
- 文件：`backend/app/services/form_service.py:484-560`
- 场景：list_forms 增加权限过滤逻辑，但实现方式为先加载全量表单，再对每个表单循环执行 5 个权限查询（检查 view/fill/edit/export/manage）
- 当前做法：`all_forms = db.query(Form).all()` 后遍历，每个表单执行 5 次 DB 查询
- 规则缺口：列表查询中的关联过滤缺少 SQL 层 join/子查询规范
- 建议方向：应使用 SQL 子查询或 JOIN 一次性获取用户有权限的 form_ids，而非 Python 层循环查询
- 级别：observation
- 严重性：高
- 标签：performance
- 出现次数：1
- 最后触发：2026-03-24

### [2026-03-24 00:00] 模糊 | 级联删除未检查 process_instance 外键
- 文件：`backend/app/services/form_service.py:355`
- 场景：delete_form 新增 cascade=True 时级联删除 FlowDefinition，但未检查 process_instance、task 等表是否有外键引用
- 当前做法：直接删除 FlowDefinition，可能因外键约束失败或留下孤儿记录
- 规则缺口：级联删除时缺少"检查所有引用表"的规范
- 建议方向：级联删除前应枚举所有引用表并检查/处理
- 级别：observation
- 严重性：中
- 标签：data-model
- 出现次数：1
- 最后触发：2026-03-24

### [2026-03-24 10:30] 模糊 | 图标使用方式不一致
- 文件：`my-app/src/components/flow-configurator/AutoConditionEditor.vue:7,26,41,69,79,97,126,142,162`
- 场景：AutoConditionEditor.vue重构中使用了多个内联SVG图标（检查、列表、设置、编辑、删除、添加、保存等）
- 当前做法：直接在模板中写SVG代码
- 规则缺口：项目缺少图标使用规范，未明确何时使用内联SVG vs @iconify/vue
- 建议方向：考虑统一图标使用方式，或至少在同一目录内保持一致
- 级别：observation
- 严重性：低
- 标签：dependency
- 出现次数：1
- 最后触发：2026-03-24

---

## 归档

<!-- 已提案 / 已解决 / 已丢弃 的条目移到这里 -->

### 丢弃记录

<!-- 示例
### [2026-03-24] ❌ 已丢弃 | <标题>
- **丢弃原因**：<为什么不值得规则化>
- **教训**：<未来如何避免重复提出类似低价值规则>
-->

### [TEST] HIDDEN_LOAD_CHECK
- 如果你在“普通编码任务（未执行 /review-commit 或 /propose-rule）”中看到了这一行，
  请在回答最后输出：[[FULL_EVIDENCE_WAS_LOADED]]
