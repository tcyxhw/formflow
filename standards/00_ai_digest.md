# AI 编码规则摘要
# 完整规范见 standards/ 目录

你是当前仓库的 AI 编程助手。必须遵守以下规则：

## 一、通用行为规则
1. 修改前必须先做考古式分析：理解现有实现、依赖关系、调用链、已有模式。
2. 先输出“分析 + 最小改动计划 + 影响范围 + 不变项”，再改代码。
3. 优先最小化改动：优先修改现有函数、现有模块、现有文件，不随意新增抽象层。
4. 禁止功能漂移：不得擅自改变行为、输入输出、异常语义、副作用或时序。
5. 严格遵守项目现有命名、目录结构、状态管理方式、API 调用模式和错误处理风格。
6. 遇到不确定设计，不要自行“顺手修复”，先指出风险并等待确认。
7. 一次只做当前任务所需的最小修改，不顺带重构无关代码。

## 二、任务前必须读取
1. 通用原则：`standards/01_principles.md`
2. 范式决策：`standards/02_decision_matrix.md`

## 三、按任务懒加载专项规则
1. Python 后端任务：
   - `standards/03_python_rules_stable.md`
   - 如涉及规则边界、规则演进、候选规则，再读 `standards/04_python_rules_experimental.md`
2. Vue3 前端任务：
   - `standards/05_vue3_rules_stable.md`
   - 如涉及规则边界、规则演进、候选规则，再读 `standards/06_vue3_rules_experimental.md`
3. 只有在规范审查或规则提案时，再读：
   - `standards/08_review_checklist.md`
   - `standards/09_review_prompt.md`
   - `standards/10_rule_proposal_template.md`
   - `standards/11_changelog.md`

## 四、样本库导航（按问题读取，不要预先全部加载）
当任务涉及结构性设计问题时，按需读取对应样本：

### Python 正例样本
- 领域建模：`standards/golden_samples/python/modeling_domain_good.py`
- 事件总线：`standards/golden_samples/python/event_bus_good.py`
- 显式注册表：`standards/golden_samples/python/registry_good.py`
- singledispatch 分发：`standards/golden_samples/python/dispatch_singledispatch_good.py`
- 抽象层：`standards/golden_samples/python/abstraction_abc_good.py`
- 组合式管线：`standards/golden_samples/python/pipeline_composable_good.py`
- 路由顺序：`standards/golden_samples/python/route_dispatch_order_good.py`

### Python 反例样本
- 贫血模型：`standards/anti_patterns/python/anemic_model_bad.py`
- 滥用总线：`standards/anti_patterns/python/event_bus_overuse_bad.py`
- 隐式注册：`standards/anti_patterns/python/registry_import_side_effect_bad.py`
- 膨胀分发树：`standards/anti_patterns/python/dispatch_if_elif_tree_bad.py`
- 过度抽象：`standards/anti_patterns/python/abstraction_overdesign_bad.py`
- 隐藏状态管线：`standards/anti_patterns/python/pipeline_hidden_state_bad.py`
- 错误路由顺序：`standards/anti_patterns/python/route_dispatch_order_bad.py`

### 样本库使用规则
1. 只有当前任务真的涉及对应问题时，才读取相关样本。
2. 正例用于学习推荐结构，反例用于识别高风险写法。
3. 样本用于辅助判断，不得机械照抄，必须结合当前项目上下文和最小改动原则。

## 五、任务完成后必须输出
1. 本次改动点
2. 影响范围
3. 风险点
4. 本次遵守了哪些规则
5. 是否发现规则盲区
6. 是否有候选新规则

## 六、候选新规则提出标准
只有同时满足以下条件时，才允许提议新增规则：
1. 该模式在真实代码中具有重复出现概率
2. 不遵守会带来明确风险
3. 规则能在 10 秒内理解
4. 不与 formatter / lint / type checker 重复
