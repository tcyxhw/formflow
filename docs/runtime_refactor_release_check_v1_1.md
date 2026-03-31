# /release-check Runtime 化 V1.1 完成说明

> 完成日期：2026-03-30

---

## 1. 背景

`/release-check` 是 push/PR 前的最终审查环节。在 V1.1 之前，release-check 流程与 `/checkpoint` 共用大部分逻辑，但缺乏独立的 runtime 上下文、capsule 生成和 final decision 语义。

V1.1 目标是让 `/release-check` 拥有完整的 runtime 化能力，与 `/checkpoint` 形成互补（commit 前 vs push 前）。

---

## 2. V1.1 已完成内容

| 功能 | 状态 | 说明 |
|:---|:---|:---|
| release-check context | ✅ | `prepare_checkpoint_context.py --mode release-check` |
| release-check capsule | ✅ | `.runtime/release_check_capsule.md` |
| release gate results | ✅ | `run_checkpoint_gates.py --mode release-check` |
| release_review_output.json | ✅ | `generate_review_output.py --mode release-check` |
| evidence 更新复用 | ✅ | 使用 `update_evidence_from_review.py` |
| final decision 语义 | ✅ | push / revise / manual-review |

---

## 3. 最终产物清单

```
.runtime/
├── release_check_context.json    # 运行时上下文
├── release_check_capsule.md       # 运行时胶囊
├── release_gate_results.json      # 门禁结果
└── release_review_output.json    # 结构化审查输出
```

---

## 4. 已验证场景

| 场景 | 触发域 | profile | 验证结果 |
|:---|:---|:---|:---|
| backend branch diff | backend | Strict | ✅ |
| frontend branch diff | frontend | Normal/Strict | ✅ |
| contract/schema diff | contract | Normal/Strict | ✅ |
| cross-layer (backend+frontend) | backend, frontend, contract | Strict | ✅ |

---

## 5. 当前已知限制

- gate 工具缺失时标记为 `skipped`，非 `failed`
- 仍依赖本地环境已有工具（ruff, mypy, npm）
- profile 强制基于 diff 规模，不支持 `--lite/--normal/--strict` 手动覆盖
- runtime cards 仍需手动编译（`build_rule_runtime_cards.py`）

---

## 6. Backlog（暂不实现）

| # | 项目 | 说明 |
|:---|:---|:---|
| 1 | `/release-check` 支持 `--lite/--normal/--strict` | 手动覆盖 profile |
| 2 | `/task runtime 化` | 将 task pipeline 也接入 runtime cards |
| 3 | benchmark 自动化 | 自动回归测试场景 |
| 4 | fallback 使用率统计 | 记录 runtime card fallback 频率 |
| 5 | evidence 去重/归档增强 | 自动清理 stale evidence |

---

## 7. V1.1 验收结论

> `/release-check runtime 化 V1.1` 已完成，建议标记为正式可用版本。

- 所有核心路径已验证可运行
- 与 `/checkpoint` 共用 runtime cards 机制
- final decision 语义已对齐（push/revise/manual-review）
- 文档已固化
