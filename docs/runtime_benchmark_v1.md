# Runtime Benchmark V1 完成说明

## 背景

V1 目标：实现最小可用 benchmark 系统，固化当前 `/task`、`/checkpoint`、`/release-check` runtime 场景，形成可重复执行的自动回归基线。

---

## 新增/修改文件

| 文件 | 职责 |
|------|------|
| `benchmarks/runtime_benchmarks.yaml` | benchmark 场景定义文件 |
| `scripts/run_runtime_benchmarks.py` | benchmark 执行脚本 |
| `scripts/prepare_checkpoint_context.py` | 修复 profile 字段为空的问题 |
| `.runtime/benchmark_report.json` | benchmark 报告 (JSON) |
| `.runtime/benchmark_report.md` | benchmark 报告 (Markdown) |

---

## Benchmark 结构

### 场景定义
- `benchmarks/runtime_benchmarks.yaml` - 统一场景定义
- 3 类命令：`task` / `checkpoint` / `release_check`
- 每类至少 3 个场景

### 执行脚本
- `scripts/run_runtime_benchmarks.py` - 自动执行 benchmark

### 报告输出
- `.runtime/benchmark_report.json` - 结构化报告
- `.runtime/benchmark_report.md` - 可读报告

---

## 使用方法

```bash
# 全量运行
python3 scripts/run_runtime_benchmarks.py

# 按组运行
python3 scripts/run_runtime_benchmarks.py --group task
python3 scripts/run_runtime_benchmarks.py --group checkpoint
python3 scripts/run_runtime_benchmarks.py --group release-check

# 单 case 运行
python3 scripts/run_runtime_benchmarks.py --case T1
```

---

## 验证结果

### 全量运行
- Total: 9
- Passed: 9 ✅
- Failed: 0
- Skipped: 0

### 分组运行
- task: 3/3 ✅
- checkpoint: 3/3 ✅
- release-check: 3/3 ✅

### 单 case 运行
- T1: ✅

---

## 当前限制

1. **checkpoint/release-check 依赖真实 git 状态**：无 staged changes 时 profile 为 N/A
2. **gate 检查未纳入 V1**：gates (ruff/mypy/npm) 需单独验证
3. **无 CI 集成**：需要手动运行或配置 CI
4. **场景数量有限**：后续可扩展更多边界场景

---

## Backlog 候选项

1. 自动化 gate 检查集成
2. 场景数量扩展
3. 回归趋势统计
4. CI 集成
5. 指标面板

---

## 结论

**benchmark 自动化 V1 已完成**，满足最小可用要求：
- ✅ 有 benchmark 场景定义文件
- ✅ 有 benchmark 执行脚本
- ✅ 能输出 benchmark_report.json/md
- ✅ 覆盖 task/checkpoint/release-check 三类场景
- ✅ 能执行全量/分组/单 case
- ✅ 能稳定输出 pass/fail 结果
