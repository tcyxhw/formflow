# Runtime Benchmark - Minimal Baseline

> 固化日期：2026-03-30

本文档记录 `/release-check` runtime 化的最小验收基线，用于回归验证。

---

## 场景 A：普通 Backend Branch Diff

**输入特征**：
- 仅修改 `backend/app/services/` 或 `backend/app/api/` 下的文件
- 文件数 ≤ 8
- 变更行数 ≤ 400

**预期输出**：
| 字段 | 预期值 |
|:---|:---|
| `profile` | Normal |
| `triggered_domains` | ["backend"] |
| `required_runtime_cards` | [common, backend] |
| `final_decision.recommendation` | commit / push |

**验证命令**：
```bash
python3 scripts/prepare_checkpoint_context.py --mode release-check --base-ref origin/main
python3 scripts/run_checkpoint_gates.py --mode release-check
python3 scripts/generate_review_output.py --mode release-check
```

---

## 场景 B：Schema / Contract Branch Diff

**输入特征**：
- 修改 `backend/app/schemas/` 和/或 `my-app/src/types/`
- 或包含 `schema`、`contract` 关键词的变更

**预期输出**：
| 字段 | 预期值 |
|:---|:---|
| `profile` | Normal 或 Strict |
| `triggered_domains` | 包含 "contract" |
| `required_runtime_cards` | 包含 contract card |
| `final_decision.recommendation` | 不应过于宽松（需审查契约闭合） |

---

## 场景 C：Security / Permission / Migration Branch Diff

**输入特征**：
- 修改包含 `security`、`permission`、`auth`、`migrate`、`migration`、`delete` 关键词的文件
- 或涉及 `alembic/` 目录

**预期输出**：
| 字段 | 预期值 |
|:---|:---|
| `profile` | Strict |
| `triggered_domains` | 包含 "risk" |
| `required_runtime_cards` | 包含 risk card |
| `final_decision.recommendation` | manual-review 或 revise |

---

## 验证检查清单

- [ ] release_check_context.json 生成成功
- [ ] release_check_capsule.md 生成成功
- [ ] release_gate_results.json 生成成功
- [ ] release_review_output.json 生成成功
- [ ] summary.mode = "release-check"
- [ ] summary.base_ref 正确传递
- [ ] 工具缺失时标记为 skipped（不是 failed）
- [ ] triggered_domains 与实际变更匹配
