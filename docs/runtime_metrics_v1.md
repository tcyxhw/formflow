# Runtime Metrics System V1

> Minimal observability for runtime workflows

## Overview

Runtime Metrics V1 provides lightweight metrics collection from existing runtime workflow outputs without modifying business code or introducing external monitoring tools.

## Metrics Scope

| Category | Data Sources | Collected Metrics |
|----------|--------------|-------------------|
| Task | `task_context.json` | task_id, profile, predicted_domains, task_type |
| Checkpoint | `checkpoint_context.json` | review_run_id, profile, diff_summary, triggered_domains |
| Release Check | `release_check_context.json` | review_run_id, profile, diff_summary, file_groups, runtime_card_status |
| Gates | `gate_results.json`, `release_gate_results.json` | profile, triggered_domains, ran/passed/failed/skipped |
| Reviews | `review_output.json`, `release_review_output.json` | status, changed_files/lines, blocking_issues, final_decision |
| Benchmark | `benchmark_report.json` | total/passed/failed counts, group_stats |
| Evidence | `evidence/active/`, `evidence/proposals/`, `evidence/archive/` | counts by status, active_evidence_sample |

## Output Files

- `.runtime/runtime_metrics.json` - Machine-readable metrics
- `.runtime/runtime_metrics.md` - Human-readable report

## Usage

```bash
python3 scripts/runtime_metrics_report.py
```

## Script Location

- `scripts/runtime_metrics_report.py`

## Key Design Decisions

1. **Read-only**: Only reads existing runtime outputs, no business code modification
2. **Lightweight**: Single script, no external dependencies beyond stdlib
3. **Backward compatible**: Handles missing files gracefully
4. **Human + Machine readable**: JSON for automation, MD for quick review

## Version History

- V1 (2026-03-30): Initial release
