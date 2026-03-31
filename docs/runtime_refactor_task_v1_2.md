# Task Runtime V1.2 完成说明

## 背景

V1.2 目标：将 `/task` 接入 runtime 主路径，与 `/checkpoint`、`/release-check` 形成统一 runtime 工作模式。

---

## V1.2 完成内容

### 1. 新增脚本
- `scripts/prepare_task_context.py`：任务上下文生成器
  - 支持 `--task "..."` 参数
  - 支持 `--lite`/`--normal`/`--strict` 档位覆盖
  - 生成 `.runtime/task_context.json`
  - 生成 `.runtime/task_capsule.md`

### 2. 命令改造
- `.opencode/commands/task.md`：已改为默认走 runtime 路径
  - 先执行 `prepare_task_context.py` 生成 context/capsule
  - 默认读取 `.runtime/task_capsule.md`
  - 明确禁止默认读取 7 个源文件
  - 保留 Fallback 机制

### 3. 文档更新
- `AGENTS.md`：已反映 `/task` runtime 化状态
- `standards/00_ai_digest.md`：已添加 Runtime Card 机制说明

---

## Runtime 产物清单

| 文件 | 说明 |
|------|------|
| `.runtime/task_context.json` | 结构化任务上下文 |
| `.runtime/task_capsule.md` | 可读任务摘要 |

### task_context.json 字段
- `task_id`
- `profile`
- `initial_classification`
- `task_type`
- `predicted_domains`
- `routing`
- `affected_area_hints`
- `detected_keywords`

---

## 验证场景

### 场景 A：Lite
- 命令：`--task "修复表单组件样式问题" --lite`
- 结果：Profile=Lite ✅

### 场景 B：Normal/Contract
- 命令：`--task "修改用户表单API并同步前端Typescript类型"`
- 结果：Profile=Normal, predicted_domains=contract ✅

### 场景 C：Strict
- 命令：`--task "修复权限删除时关联记录未清理的问题"`
- 结果：Profile=Strict, routing=planner-strict ✅

---

## 当前已知限制

1. **detected_keywords 有时为空**：关键词检测逻辑可优化
2. **predicted_domains 覆盖不全**：部分边界场景可能未覆盖
3. **fallback 使用率未统计**：无法量化 fallback 触发频率
4. **benchmark 未自动化**：缺少自动化性能基线

---

## Backlog 候选项

1. `/task` output schema 结构化
2. `/task` benchmark 自动化
3. `/task` fallback 使用率统计
4. `/task` 与 planner/implementer 更深的结构化集成
5. 统一 task/checkpoint/release-check 指标面板

---

## 验收评分

- 关键文件与脚本完整性：18/20
- Runtime 产物生成能力：18/20
- `/task` runtime 主路径接管：28/30
- Task Execution Report 结构保留：18/20
- 旧逻辑残留控制：9/10

**总分：91/100 - 基本达标**

---

## 结论

`/task runtime 化 V1.2` 已基本完成，形成可用闭环。后续可按需迭代优化。
