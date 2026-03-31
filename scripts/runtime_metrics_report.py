#!/usr/bin/env python3
"""
Runtime Metrics Report - V1
Collects metrics from runtime workflow outputs.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(".runtime")
EVIDENCE_DIR = Path("evidence")

METRICS_OUTPUT_JSON = RUNTIME_DIR / "runtime_metrics.json"
METRICS_OUTPUT_MD = RUNTIME_DIR / "runtime_metrics.md"


def load_json(path: Path) -> dict | None:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def count_evidence_by_status() -> dict:
    counts = {"active": 0, "proposals": 0, "archive": 0}
    for subdir in ["active", "proposals", "archive"]:
        dir_path = EVIDENCE_DIR / subdir
        if dir_path.exists():
            counts[subdir] = len(list(dir_path.glob("*.json")))
    return counts


def collect_task_metrics() -> dict:
    data = load_json(RUNTIME_DIR / "task_context.json")
    if not data:
        return {"available": False}
    
    return {
        "available": True,
        "task_id": data.get("task_id"),
        "profile": data.get("profile"),
        "task_type": data.get("task_type"),
        "predicted_domains": data.get("predicted_domains", []),
        "detected_keywords": data.get("detected_keywords", []),
        "generated_at": data.get("generated_at"),
    }


def collect_checkpoint_metrics() -> dict:
    data = load_json(RUNTIME_DIR / "checkpoint_context.json")
    if not data:
        return {"available": False}
    
    diff_summary = data.get("diff_summary", {})
    return {
        "available": True,
        "review_run_id": data.get("review_run_id"),
        "profile": data.get("profile"),
        "changed_files": diff_summary.get("changed_files", 0),
        "additions": diff_summary.get("additions", 0),
        "deletions": diff_summary.get("deletions", 0),
        "cross_layer": diff_summary.get("cross_layer", False),
        "triggered_domains": data.get("triggered_domains", []),
        "generated_at": data.get("generated_at"),
    }


def collect_release_check_metrics() -> dict:
    data = load_json(RUNTIME_DIR / "release_check_context.json")
    if not data:
        return {"available": False}
    
    diff_summary = data.get("diff_summary", {})
    return {
        "available": True,
        "review_run_id": data.get("review_run_id"),
        "profile": data.get("profile"),
        "changed_files": diff_summary.get("changed_files", 0),
        "additions": diff_summary.get("additions", 0),
        "deletions": diff_summary.get("deletions", 0),
        "cross_layer": diff_summary.get("cross_layer", False),
        "file_groups": diff_summary.get("file_groups", {}),
        "triggered_domains": data.get("triggered_domains", []),
        "runtime_card_status": data.get("runtime_card_status", {}),
        "generated_at": data.get("generated_at"),
    }


def collect_gate_metrics() -> dict:
    data = load_json(RUNTIME_DIR / "gate_results.json")
    release_data = load_json(RUNTIME_DIR / "release_gate_results.json")
    
    result = {
        "checkpoint": {"available": False},
        "release": {"available": False},
    }
    
    if data:
        result["checkpoint"] = {
            "available": True,
            "profile": data.get("profile"),
            "triggered_domains": data.get("triggered_domains", []),
            "ran": data.get("ran", []),
            "passed": data.get("passed", []),
            "failed": data.get("failed", []),
            "skipped": data.get("skipped", []),
            "generated_at": data.get("generated_at"),
        }
    
    if release_data:
        result["release"] = {
            "available": True,
            "profile": release_data.get("profile"),
            "triggered_domains": release_data.get("triggered_domains", []),
            "ran": release_data.get("ran", []),
            "passed": release_data.get("passed", []),
            "failed": release_data.get("failed", []),
            "skipped": release_data.get("skipped", []),
            "generated_at": release_data.get("generated_at"),
        }
    
    return result


def collect_review_metrics() -> dict:
    data = load_json(RUNTIME_DIR / "review_output.json")
    release_data = load_json(RUNTIME_DIR / "release_review_output.json")
    
    result = {
        "checkpoint": {"available": False},
        "release": {"available": False},
    }
    
    if data:
        summary = data.get("summary", {})
        domain_findings = data.get("domain_findings", {})
        result["checkpoint"] = {
            "available": True,
            "review_run_id": data.get("review_run_id"),
            "profile": data.get("profile"),
            "status": summary.get("status"),
            "changed_files": summary.get("changed_files", 0),
            "changed_lines": summary.get("changed_lines", 0),
            "triggered_domains": data.get("triggered_domains", []),
            "blocking_issues": len(data.get("blocking_issues", [])),
            "non_blocking_issues": len(data.get("non_blocking_issues", [])),
            "final_decision": data.get("final_decision", {}),
            "generated_at": data.get("generated_at"),
        }
    
    if release_data:
        summary = release_data.get("summary", {})
        result["release"] = {
            "available": True,
            "review_run_id": release_data.get("review_run_id"),
            "profile": release_data.get("profile"),
            "status": summary.get("status"),
            "changed_files": summary.get("changed_files", 0),
            "changed_lines": summary.get("changed_lines", 0),
            "triggered_domains": release_data.get("triggered_domains", []),
            "blocking_issues": len(release_data.get("blocking_issues", [])),
            "non_blocking_issues": len(release_data.get("non_blocking_issues", [])),
            "final_decision": release_data.get("final_decision", {}),
            "generated_at": release_data.get("generated_at"),
        }
    
    return result


def collect_benchmark_metrics() -> dict:
    data = load_json(RUNTIME_DIR / "benchmark_report.json")
    if not data:
        return {"available": False}
    
    summary = data.get("summary", {})
    results = data.get("results", [])
    
    group_stats = {}
    for r in results:
        group = r.get("group", "unknown")
        if group not in group_stats:
            group_stats[group] = {"total": 0, "passed": 0, "failed": 0}
        group_stats[group]["total"] += 1
        if r.get("status") == "passed":
            group_stats[group]["passed"] += 1
        elif r.get("status") == "failed":
            group_stats[group]["failed"] += 1
    
    return {
        "available": True,
        "summary": summary,
        "group_stats": group_stats,
        "generated_at": data.get("generated_at"),
    }


def collect_evidence_metrics() -> dict:
    counts = count_evidence_by_status()
    
    active_evidence = []
    active_dir = EVIDENCE_DIR / "active"
    if active_dir.exists():
        for f in sorted(active_dir.glob("*.json")):
            ev = load_json(f)
            if ev:
                active_evidence.append({
                    "id": ev.get("id"),
                    "title": ev.get("title"),
                    "severity": ev.get("severity"),
                    "tags": ev.get("tags", []),
                })
    
    return {
        "available": True,
        "counts": counts,
        "active_evidence_sample": active_evidence[:5],
    }


def generate_markdown(metrics: dict) -> str:
    lines = [
        "# Runtime Metrics Report",
        "",
        f"Generated: {metrics['generated_at']}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Task Runs | {1 if metrics.get('task', {}).get('available') else 0} |",
        f"| Checkpoint Runs | {1 if metrics.get('checkpoint', {}).get('available') else 0} |",
        f"| Release Check Runs | {1 if metrics.get('release_check', {}).get('available') else 0} |",
        f"| Benchmark Cases | {metrics.get('benchmark', {}).get('summary', {}).get('total', 0)} |",
        f"| Benchmark Passed | {metrics.get('benchmark', {}).get('summary', {}).get('passed', 0)} |",
        f"| Evidence Active | {metrics.get('evidence', {}).get('counts', {}).get('active', 0)} |",
        f"| Evidence Archived | {metrics.get('evidence', {}).get('counts', {}).get('archive', 0)} |",
        "",
    ]
    
    if metrics.get("task", {}).get("available"):
        t = metrics["task"]
        lines.extend([
            "## Task Metrics",
            "",
            f"- Task ID: `{t.get('task_id')}`",
            f"- Profile: `{t.get('profile')}`",
            f"- Predicted Domains: {', '.join(t.get('predicted_domains', []))}",
            "",
        ])
    
    if metrics.get("release_check", {}).get("available"):
        rc = metrics["release_check"]
        lines.extend([
            "## Release Check Metrics",
            "",
            f"- Review Run ID: `{rc.get('review_run_id')}`",
            f"- Profile: `{rc.get('profile')}`",
            f"- Changed Files: {rc.get('changed_files')}",
            f"- Cross-layer: {rc.get('cross_layer')}",
            f"- Triggered Domains: {', '.join(rc.get('triggered_domains', []))}",
            "",
        ])
    
    if metrics.get("benchmark", {}).get("available"):
        b = metrics["benchmark"]
        bs = b.get("group_stats", {})
        lines.extend([
            "## Benchmark Metrics",
            "",
            f"- Total Cases: {b.get('summary', {}).get('total', 0)}",
            f"- Passed: {b.get('summary', {}).get('passed', 0)}",
            f"- Failed: {b.get('summary', {}).get('failed', 0)}",
            "",
            "### By Group",
            "",
        ])
        for group, stats in bs.items():
            lines.append(f"- {group}: {stats['passed']}/{stats['total']} passed")
        lines.append("")
    
    if metrics.get("evidence", {}).get("available"):
        e = metrics["evidence"]
        lines.extend([
            "## Evidence Metrics",
            "",
            f"- Active: {e.get('counts', {}).get('active', 0)}",
            f"- Proposals: {e.get('counts', {}).get('proposals', 0)}",
            f"- Archived: {e.get('counts', {}).get('archive', 0)}",
            "",
        ])
    
    return "\n".join(lines)


def main():
    metrics = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "task": collect_task_metrics(),
        "checkpoint": collect_checkpoint_metrics(),
        "release_check": collect_release_check_metrics(),
        "gates": collect_gate_metrics(),
        "reviews": collect_review_metrics(),
        "benchmark": collect_benchmark_metrics(),
        "evidence": collect_evidence_metrics(),
    }
    
    RUNTIME_DIR.mkdir(exist_ok=True)
    
    with open(METRICS_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Written: {METRICS_OUTPUT_JSON}")
    
    md_content = generate_markdown(metrics)
    with open(METRICS_OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Written: {METRICS_OUTPUT_MD}")


if __name__ == "__main__":
    main()
