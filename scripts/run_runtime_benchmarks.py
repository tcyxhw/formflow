#!/usr/bin/env python3
"""
Runtime Benchmarks Runner V1

Executes benchmark scenarios for task/checkpoint/release-check runtime paths.
Outputs pass/fail report to .runtime/benchmark_report.json and .runtime/benchmark_report.md

Usage:
    python3 scripts/run_runtime_benchmarks.py
    python3 scripts/run_runtime_benchmarks.py --group task
    python3 scripts/run_runtime_benchmarks.py --group checkpoint
    python3 scripts/run_runtime_benchmarks.py --group release-check
    python3 scripts/run_runtime_benchmarks.py --case T1
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = REPO_ROOT / ".runtime"
BENCHMARKS_FILE = REPO_ROOT / "benchmarks" / "runtime_benchmarks.yaml"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_command(cmd: str, cwd: Path = REPO_ROOT, timeout: int = 60) -> Dict[str, Any]:
    """Run a shell command and return structured result."""
    result = {
        "command": cmd,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "error": None,
    }
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout[:5000] if proc.stdout else ""
        result["stderr"] = proc.stderr[:2000] if proc.stderr else ""
    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout}s"
    except Exception as e:
        result["error"] = str(e)
    return result


def load_benchmarks() -> dict:
    """Load benchmark definitions."""
    if not BENCHMARKS_FILE.exists():
        print(f"Error: Benchmark file not found: {BENCHMARKS_FILE}", file=sys.stderr)
        sys.exit(1)
    return load_yaml(BENCHMARKS_FILE)


def get_output_files(case_id: str, group: str) -> Dict[str, Path]:
    """Get expected output files for a benchmark case."""
    if group == "task":
        return {
            "task_context.json": RUNTIME_DIR / "task_context.json",
            "task_capsule.md": RUNTIME_DIR / "task_capsule.md",
        }
    elif group == "checkpoint":
        return {
            "checkpoint_context.json": RUNTIME_DIR / "checkpoint_context.json",
            "checkpoint_capsule.md": RUNTIME_DIR / "checkpoint_capsule.md",
        }
    elif group == "release_check":
        return {
            "release_check_context.json": RUNTIME_DIR / "release_check_context.json",
            "release_check_capsule.md": RUNTIME_DIR / "release_check_capsule.md",
        }
    return {}


def check_field_equals(context: dict, expected_value: Any, field_path: str) -> bool:
    """Check if a field equals expected value. Supports nested paths like 'routing.planner_agent'."""
    parts = field_path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return False
    return value == expected_value


def check_field_in(context: dict, expected_values: List[Any], field_path: str) -> bool:
    """Check if a field is in expected values. Also allows 'N/A' when there are no changes."""
    parts = field_path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return False
    if value == "N/A" and "N/A" not in expected_values:
        return True
    return value in expected_values


def check_field_contains(context: dict, expected_value: Any, field_path: str) -> bool:
    """Check if a field contains expected value (for lists)."""
    parts = field_path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return False
    if isinstance(value, list):
        return expected_value in value
    return False


def check_field_nonempty(context: dict, field_path: str) -> bool:
    """Check if a field is non-empty."""
    parts = field_path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return False
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists()


def check_field_not_contains(context: dict, value: str, field_path: str) -> bool:
    """Check if a field does NOT contain a specific value."""
    parts = field_path.split(".")
    val = context
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return True
    if val is None:
        return True
    if isinstance(val, list):
        return value not in val
    if isinstance(val, str):
        return value not in val
    return True


def check_field_is_array(context: dict, field_path: str) -> bool:
    """Check if a field is an array."""
    parts = field_path.split(".")
    val = context
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return False
    return isinstance(val, list)


def run_check(check: dict, context: dict, output_files: Dict[str, Path]) -> Dict[str, Any]:
    """Run a single check and return result."""
    check_name = check.get("field") or check.get("exists") or "unknown"
    
    if "exists" in check:
        file_key = check["exists"]
        file_path = output_files.get(file_key)
        if file_path:
            passed = check_file_exists(file_path)
            return {
                "name": f"exists: {file_key}",
                "status": "passed" if passed else "failed",
                "details": f"File {'found' if passed else 'not found'}: {file_path.name}",
            }
        return {"name": f"exists: {file_key}", "status": "failed", "details": "Unknown file key"}
    
    field = check.get("field")
    if "equals" in check:
        passed = check_field_equals(context, check["equals"], field)
        return {
            "name": f"{field} == {check['equals']}",
            "status": "passed" if passed else "failed",
            "details": f"Expected {check['equals']}, got {context.get(field, 'N/A')}",
        }
    elif "in" in check:
        passed = check_field_in(context, check["in"], field)
        return {
            "name": f"{field} in {check['in']}",
            "status": "passed" if passed else "failed",
            "details": f"Expected one of {check['in']}, got {context.get(field, 'N/A')}",
        }
    elif "contains" in check:
        passed = check_field_contains(context, check["contains"], field)
        return {
            "name": f"{field} contains {check['contains']}",
            "status": "passed" if passed else "failed",
            "details": f"Expected {check['contains']} in {context.get(field, 'N/A')}",
        }
    elif "not_contains" in check:
        passed = check_field_not_contains(context, check["not_contains"], field)
        return {
            "name": f"{field} not_contains {check['not_contains']}",
            "status": "passed" if passed else "failed",
            "details": f"Expected {check['not_contains']} NOT in {context.get(field, 'N/A')}",
        }
    elif check.get("is_array"):
        passed = check_field_is_array(context, field)
        return {
            "name": f"{field} is_array",
            "status": "passed" if passed else "failed",
            "details": f"Field is {'array' if passed else 'not array'}",
        }
    elif check.get("nonempty"):
        passed = check_field_nonempty(context, field)
        return {
            "name": f"{field} nonempty",
            "status": "passed" if passed else "failed",
            "details": f"Field is {'non-empty' if passed else 'empty'}",
        }
    
    return {"name": check_name, "status": "skipped", "details": "Unknown check type"}


def run_benchmark_case(case: dict, group: str) -> Dict[str, Any]:
    """Run a single benchmark case."""
    case_id = case["id"]
    name = case["name"]
    command = case.get("command") or case.get("setup", "")
    
    result = {
        "case_id": case_id,
        "group": group,
        "name": name,
        "status": "failed",
        "checks": [],
        "notes": [],
        "error": None,
    }
    
    if command:
        cmd_result = run_command(command)
        if cmd_result.get("error"):
            result["error"] = cmd_result["error"]
            result["notes"].append(f"Command error: {cmd_result['error']}")
            return result
        if cmd_result.get("returncode", 0) != 0:
            result["error"] = f"Command failed with code {cmd_result.get('returncode')}"
            result["notes"].append(f"stderr: {cmd_result.get('stderr', '')[:500]}")
            return result
    
    output_files = get_output_files(case_id, group)
    context = None
    
    if group == "task":
        context = load_json(RUNTIME_DIR / "task_context.json")
    elif group == "checkpoint":
        context = load_json(RUNTIME_DIR / "checkpoint_context.json")
    elif group == "release_check":
        context = load_json(RUNTIME_DIR / "release_check_context.json")
    
    if context is None:
        result["error"] = "Failed to load runtime context"
        return result
    
    checks = case.get("checks", [])
    all_passed = True
    for check in checks:
        check_result = run_check(check, context, output_files)
        result["checks"].append(check_result)
        if check_result["status"] != "passed":
            all_passed = False
    
    result["status"] = "passed" if all_passed else "failed"
    return result


def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate benchmark report."""
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "results": results,
    }


def generate_markdown_report(report: dict) -> str:
    """Generate markdown report."""
    lines = []
    lines.append("# Runtime Benchmarks Report")
    lines.append("")
    lines.append(f"**Generated**: {report['generated_at']}")
    lines.append("")
    
    summary = report["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Total | Passed | Failed | Skipped |")
    lines.append(f"|-------|--------|--------|---------|")
    lines.append(f"| {summary['total']} | {summary['passed']} | {summary['failed']} | {summary['skipped']} |")
    lines.append("")
    
    lines.append("## Results")
    lines.append("")
    
    by_group = {}
    for r in report["results"]:
        group = r.get("group", "unknown")
        if group not in by_group:
            by_group[group] = []
        by_group[group].append(r)
    
    for group, cases in by_group.items():
        lines.append(f"### {group.upper()}")
        lines.append("")
        for case in cases:
            status_icon = "✅" if case["status"] == "passed" else "❌" if case["status"] == "failed" else "⏭️"
            lines.append(f"#### {status_icon} {case['case_id']}: {case['name']}")
            lines.append("")
            lines.append(f"**Status**: {case['status']}")
            lines.append("")
            lines.append("**Checks**:")
            for check in case.get("checks", []):
                icon = "✅" if check["status"] == "passed" else "❌" if check["status"] == "failed" else "⏭️"
                lines.append(f"- {icon} {check['name']}: {check.get('details', '')}")
            lines.append("")
            if case.get("error"):
                lines.append(f"**Error**: {case['error']}")
                lines.append("")
            if case.get("notes"):
                lines.append("**Notes**:")
                for note in case["notes"]:
                    lines.append(f"- {note}")
                lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run runtime benchmarks")
    parser.add_argument(
        "--group",
        type=str,
        choices=["task", "checkpoint", "release-check"],
        help="Run only benchmarks for a specific group",
    )
    parser.add_argument(
        "--case",
        type=str,
        help="Run only a specific benchmark case (e.g., T1, C1, R1)",
    )
    args = parser.parse_args()
    
    benchmarks = load_benchmarks()
    
    results = []
    
    groups_to_run = []
    if args.group:
        group_key = args.group.replace("-", "_")
        if group_key in benchmarks:
            groups_to_run = [(group_key, benchmarks[group_key])]
    else:
        groups_to_run = [
            ("task", benchmarks.get("task", [])),
            ("checkpoint", benchmarks.get("checkpoint", [])),
            ("release_check", benchmarks.get("release_check", [])),
        ]
    
    for group_key, cases in groups_to_run:
        group_name = group_key.replace("_", "-")
        
        for case in cases:
            case_id = case["id"]
            
            if args.case and case_id != args.case:
                continue
            
            print(f"Running {case_id} ({group_name})...", end=" ")
            
            result = run_benchmark_case(case, group_key)
            results.append(result)
            
            status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏭️"
            print(f"{status_icon} {result['status']}")
    
    if not results:
        print("No benchmarks to run.", file=sys.stderr)
        sys.exit(1)
    
    report = generate_report(results)
    
    save_json(RUNTIME_DIR / "benchmark_report.json", report)
    print(f"\nJSON report saved to: {RUNTIME_DIR / 'benchmark_report.json'}")
    
    md_report = generate_markdown_report(report)
    md_path = RUNTIME_DIR / "benchmark_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"Markdown report saved to: {md_path}")
    
    summary = report["summary"]
    print("\n" + "=" * 60)
    print("Benchmark Results:")
    print(f"  Total:   {summary['total']}")
    print(f"  Passed:  {summary['passed']} ✅")
    print(f"  Failed:  {summary['failed']} ❌")
    print(f"  Skipped: {summary['skipped']} ⏭️")
    print("=" * 60)
    
    if summary["failed"] > 0:
        print("\nFailed cases:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['case_id']}: {r.get('error', 'check failed')}")
    
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
