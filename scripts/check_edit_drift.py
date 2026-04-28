#!/usr/bin/env python3
"""
Edit Drift Checker

Analyzes actual code changes against expected edit scope to detect drift.
Generates .runtime/edit_drift_report.json

Usage:
    python3 scripts/check_edit_drift.py
    python3 scripts/check_edit_drift.py --mode staged
    python3 scripts/check_edit_drift.py --mode unstaged
    python3 scripts/check_edit_drift.py --mode diff HEAD~1
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = REPO_ROOT / ".runtime"
TASK_CONTEXT_FILE = RUNTIME_DIR / "task_context.json"
DRIFT_REPORT_FILE = RUNTIME_DIR / "edit_drift_report.json"


def load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_git_command(cmd: List[str], cwd: Path = REPO_ROOT) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""


def get_staged_files() -> List[str]:
    """Get list of staged files."""
    output = run_git_command(["diff", "--staged", "--name-only"])
    if not output:
        return []
    return [f for f in output.split("\n") if f]


def get_unstaged_files() -> List[str]:
    """Get list of unstaged (modified but not staged) files."""
    output = run_git_command(["diff", "--name-only"])
    if not output:
        return []
    return [f for f in output.split("\n") if f]


def get_diff_files(ref: str) -> List[str]:
    """Get list of changed files between commits."""
    output = run_git_command(["diff", "--name-only", ref])
    if not output:
        return []
    return [f for f in output.split("\n") if f]


def get_changed_lines(file_path: str, mode: str = "unstaged") -> int:
    """Get number of changed lines in a file."""
    try:
        if mode == "staged":
            result = subprocess.run(
                ["git", "diff", "--staged", "--", file_path],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
        elif mode == "unstaged":
            result = subprocess.run(
                ["git", "diff", "--", file_path],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            result = subprocess.run(
                ["git", "diff", mode, "--", file_path],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
        
        if result.returncode != 0:
            return 0
        
        lines = result.stdout.split("\n")
        added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
        return added + removed
    except Exception:
        return 0


def normalize_zone(zone: str) -> Set[str]:
    """Normalize a zone to set of path prefixes for matching."""
    zone = zone.lower().strip()
    prefixes = set()
    
    parts = zone.replace(":", "/").replace("\\", "/").split("/")
    for i in range(len(parts)):
        prefix = "/".join(parts[:i+1])
        prefixes.add(prefix)
        prefixes.add(parts[i])
    
    return prefixes


def is_file_in_zone(file_path: str, zones: List[str]) -> bool:
    """Check if a file path matches any of the expected zones."""
    file_path = file_path.lower()
    
    for zone in zones:
        zone_prefixes = normalize_zone(zone)
        for prefix in zone_prefixes:
            if prefix in file_path:
                return True
    
    return False


def calculate_drift_level(
    outside_count: int,
    total_count: int,
    budget_exceeded: bool,
    repair_loop_count: int = 0,
) -> str:
    """Calculate drift level based on metrics, with repair loop consideration."""
    if total_count == 0:
        return "none"
    
    outside_ratio = outside_count / total_count if total_count > 0 else 0
    
    if outside_count == 0 and not budget_exceeded:
        return "none"
    elif outside_count == 0 and budget_exceeded:
        return "low"
    elif outside_ratio <= 0.2 and not budget_exceeded:
        return "low"
    elif outside_ratio <= 0.5:
        return "medium"
    else:
        return "high"


def check_edit_drift(
    task_context: dict,
    changed_files: List[str],
    mode: str,
) -> dict:
    """Check drift between expected scope and actual changes."""
    now = datetime.now(timezone.utc).isoformat()
    
    edit_scope = task_context.get("edit_scope", {})
    expected_zones = edit_scope.get("expected_zones", [])
    budget = edit_scope.get("max_edit_budget", {})
    max_files = budget.get("max_files", 999)
    max_lines = budget.get("max_changed_lines", 99999)
    
    repair_mode = task_context.get("repair_mode", {})
    repair_loop_count = repair_mode.get("repair_loop_count", 0)
    repair_budget = task_context.get("repair_budget", {})
    
    if repair_mode.get("enabled") and repair_budget:
        max_files = min(max_files, repair_budget.get("max_files", max_files))
        max_lines = min(max_lines, repair_budget.get("max_changed_lines", max_lines))
    
    outside_expected_zone_files = []
    total_changed_lines = 0
    
    for f in changed_files:
        if not is_file_in_zone(f, expected_zones):
            outside_expected_zone_files.append(f)
        
        total_changed_lines += get_changed_lines(f, mode)
    
    file_count_exceeded = len(changed_files) > max_files
    line_count_exceeded = total_changed_lines > max_lines
    
    budget_check = {
        "file_count_exceeded": file_count_exceeded,
        "line_count_exceeded": line_count_exceeded,
        "actual_files": len(changed_files),
        "max_files": max_files,
        "actual_lines": total_changed_lines,
        "max_lines": max_lines,
    }
    
    drift_detected = (
        len(outside_expected_zone_files) > 0 or
        file_count_exceeded or
        line_count_exceeded
    )
    
    drift_level = calculate_drift_level(
        len(outside_expected_zone_files),
        len(changed_files),
        file_count_exceeded or line_count_exceeded,
        repair_loop_count,
    )
    
    repair_awareness = {
        "repair_loop_count": repair_loop_count,
        "repair_mode_enabled": repair_mode.get("enabled", False),
        "drift_level": drift_level,
        "recommendation": "",
    }
    
    if repair_loop_count >= 2:
        if drift_level == "high":
            repair_awareness["recommendation"] = "stop_loss"
        elif drift_level == "medium":
            repair_awareness["recommendation"] = "require_explanation"
        else:
            repair_awareness["recommendation"] = "continue"
    else:
        if drift_level == "high":
            repair_awareness["recommendation"] = "warn"
        else:
            repair_awareness["recommendation"] = "continue"
    
    notes = []
    if file_count_exceeded:
        notes.append(f"File count {len(changed_files)} exceeds budget {max_files}")
    if line_count_exceeded:
        notes.append(f"Changed lines {total_changed_lines} exceeds budget {max_lines}")
    if len(outside_expected_zone_files) > 0:
        notes.append(f"{len(outside_expected_zone_files)} files outside expected zones")
    if repair_awareness["recommendation"] in ("stop_loss", "require_explanation"):
        notes.append(f"Repair-aware recommendation: {repair_awareness['recommendation']}")
    
    return {
        "schema_version": "1.0",
        "generated_at": now,
        "mode": mode,
        "drift_detected": drift_detected,
        "drift_level": drift_level,
        "expected_zones": expected_zones,
        "actual_changed_files": changed_files,
        "outside_expected_zone_files": outside_expected_zone_files,
        "budget_check": budget_check,
        "repair_awareness": repair_awareness,
        "notes": notes,
    }


def main():
    parser = argparse.ArgumentParser(description="Check edit drift")
    parser.add_argument(
        "--mode",
        type=str,
        default="unstaged",
        choices=["staged", "unstaged", "diff"],
        help="Mode to check (staged, unstaged, or diff)",
    )
    parser.add_argument(
        "--ref",
        type=str,
        help="Git ref for diff mode (e.g., HEAD~1)",
    )
    args = parser.parse_args()
    
    task_context = load_json(TASK_CONTEXT_FILE)
    if task_context is None:
        print(f"Error: {TASK_CONTEXT_FILE} not found. Run prepare_task_context.py first.", file=sys.stderr)
        sys.exit(1)
    
    if args.mode == "staged":
        changed_files = get_staged_files()
    elif args.mode == "diff" and args.ref:
        changed_files = get_diff_files(args.ref)
    else:
        changed_files = get_unstaged_files()
    
    report = check_edit_drift(task_context, changed_files, args.mode)
    
    save_json(DRIFT_REPORT_FILE, report)
    print(f"Drift report written to: {DRIFT_REPORT_FILE}")
    
    print(f"\nDrift Detection Results:")
    print(f"  Drift Detected: {report['drift_detected']}")
    print(f"  Drift Level: {report['drift_level']}")
    print(f"  Changed Files: {len(changed_files)}")
    print(f"  Outside Zone Files: {len(report['outside_expected_zone_files'])}")
    
    if report.get("repair_awareness"):
        ra = report["repair_awareness"]
        print(f"\n[Repair Awareness]")
        print(f"  Repair Loop Count: {ra.get('repair_loop_count', 0)}")
        print(f"  Repair Mode Enabled: {ra.get('repair_mode_enabled', False)}")
        print(f"  Recommendation: {ra.get('recommendation', 'continue')}")
    
    if report["budget_check"]["file_count_exceeded"]:
        print(f"  ⚠️ File count exceeded budget")
    if report["budget_check"]["line_count_exceeded"]:
        print(f"  ⚠️ Line count exceeded budget")
    
    if report["notes"]:
        print(f"\nNotes:")
        for note in report["notes"]:
            print(f"  - {note}")
    
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
