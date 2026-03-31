#!/usr/bin/env python3
"""
Generate structured review_output.json by merging gate results and runtime context.

This script helps the review orchestrator by:
1. Loading gate results from .runtime/gate_results.json
2. Loading runtime context from .runtime/checkpoint_context.json  
3. Generating a skeleton review_output.json matching the schema
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
RUNTIME_DIR = REPO_ROOT / ".runtime"
GATE_RESULTS_FILE = RUNTIME_DIR / "gate_results.json"
RELEASE_GATE_RESULTS_FILE = RUNTIME_DIR / "release_gate_results.json"
CONTEXT_FILE = RUNTIME_DIR / "checkpoint_context.json"
RELEASE_CONTEXT_FILE = RUNTIME_DIR / "release_check_context.json"
OUTPUT_FILE = RUNTIME_DIR / "review_output.json"
RELEASE_OUTPUT_FILE = RUNTIME_DIR / "release_review_output.json"
SCHEMA_FILE = REPO_ROOT / "policies" / "review_output_schema.json"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON file."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_tool_mode(args_mode: str, context: Dict[str, Any]) -> str:
    """Determine tool mode."""
    if args_mode:
        return args_mode
    return context.get("git_mode", "staged")


def extract_summary(context: Dict[str, Any], gate_results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary section from context."""
    diff_summary = context.get("diff_summary", {})
    git_mode = context.get("git_mode", "staged")
    
    summary = {
        "mode": git_mode,
        "status": "partial",
        "changed_files": diff_summary.get("changed_files", 0),
        "changed_lines": diff_summary.get("additions", 0) + diff_summary.get("deletions", 0),
    }
    
    if summary["changed_files"] == 0:
        summary["status"] = "no_changes"
    
    # Check gate results for status
    if gate_results:
        passed = gate_results.get("passed", [])
        failed = gate_results.get("failed", [])
        skipped = gate_results.get("skipped", [])
        if not failed and passed:
            summary["status"] = "passed"
        elif failed:
            summary["status"] = "failed"
        elif not passed and skipped:
            summary["status"] = "skipped"
    
    if git_mode == "staged":
        summary["staged_baseline"] = context.get("staged_baseline", "HEAD")
    elif git_mode == "branch":
        summary["branch_diff_base"] = context.get("branch_diff_base", "")
    elif git_mode == "release-check":
        summary["base_ref"] = context.get("base_ref", "origin/main")
        summary["target"] = "release check"
    
    return summary


def extract_triggered_domains(context: Dict[str, Any]) -> List[str]:
    """Extract triggered domains from context."""
    return context.get("triggered_domains", [])


def extract_profile(context: Dict[str, Any]) -> str:
    """Extract profile from context."""
    # Check initial_classification first
    initial = context.get("initial_classification", {})
    if initial.get("profile"):
        return initial["profile"]
    return context.get("profile", "Normal")


def format_gate_results(gate_results: Dict[str, Any]) -> Dict[str, Any]:
    """Format gate results for review output."""
    if not gate_results:
        return {"passed": [], "failed": [], "skipped": []}
    
    return {
        "passed": gate_results.get("passed", []),
        "failed": gate_results.get("failed", []),
        "skipped": gate_results.get("skipped", []),
    }


def extract_top_issues(gate_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract top issues from gate results."""
    issues = []
    
    if not gate_results:
        return issues
    
    for detail in gate_results.get("details", []):
        # Skip if tool was not found (marked as skipped)
        error = detail.get("error", "")
        if error and "not found" in error.lower():
            continue
        
        # Only create issue if gate actually ran and failed
        if detail.get("returncode", 0) != 0:
            gate_name = detail.get("gate", "unknown")
            issues.append({
                "title": f"{gate_name} check failed",
                "severity": "high",
                "location": "gate",
                "description": detail.get("stderr", "")[:500],
                "domain": "backend" if gate_name in ("ruff", "mypy") else "frontend",
            })
    
    return issues[:5]  # Max 5 issues


def generate_review_run_id() -> str:
    """Generate unique review run ID."""
    return f"review-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def get_runtime_cards_used(context: Dict[str, Any]) -> List[str]:
    """Get list of runtime cards that should be used."""
    cards = [".runtime/domain_cards/common.md"]
    
    domains = context.get("triggered_domains", [])
    domain_map = {
        "backend": ".runtime/domain_cards/backend.md",
        "frontend": ".runtime/domain_cards/frontend.md",
        "contract": ".runtime/domain_cards/contract.md",
        "risk": ".runtime/domain_cards/risk.md",
    }
    
    for domain in domains:
        if domain in domain_map:
            cards.append(domain_map[domain])
    
    return cards


def create_review_output(
    context: Dict[str, Any],
    gate_results: Dict[str, Any],
    tool_mode: str = "staged"
) -> Dict[str, Any]:
    """Create structured review output."""
    
    profile = extract_profile(context)
    triggered_domains = extract_triggered_domains(context)
    summary = extract_summary(context, gate_results)
    gate_formatted = format_gate_results(gate_results)
    top_issues = extract_top_issues(gate_results)
    runtime_cards = get_runtime_cards_used(context)
    
    # Determine if there's a blocking issue
    has_blocking = any(issue.get("severity") == "high" for issue in top_issues)
    
    is_release_check = tool_mode == "release-check"
    
    # Check if gates were skipped (tool not found)
    skipped_gates = gate_results.get("skipped", [])
    has_skipped = bool(skipped_gates)
    
    # For skipped gates, don't treat as blocking - just warn
    if has_skipped and not has_blocking:
        recommendation = "manual-review" if is_release_check else "commit"
        reason = "Gate checks passed but some tools were skipped"
    else:
        recommendation = "release" if is_release_check else ("commit" if not has_blocking else "revise")
        reason = "Gate checks passed" if not has_blocking else "Gate checks failed"
    
    review_output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool_mode": tool_mode,
        "review_run_id": generate_review_run_id(),
        "profile": profile,
        "triggered_domains": triggered_domains,
        "summary": summary,
        "blocking_issues": top_issues if has_blocking else [],
        "non_blocking_issues": top_issues if not has_blocking else [],
        "domain_findings": {
            domain: {
                "triggered": domain in triggered_domains,
                "issues": [],
                "coverage": "full" if domain in triggered_domains else "none",
                "confidence": "high" if domain in triggered_domains else "low",
            }
            for domain in ["backend", "frontend", "contract", "risk"]
        },
        "evidence_candidates": [],
        "gate_results": gate_formatted,
        "release_check_hints": {
            "should_release": not has_blocking and not has_skipped,
            "conditions": [],
            "warnings": [f"Tools skipped: {', '.join(skipped_gates)}"] if has_skipped else [],
        },
        "final_decision": {
            "checkpoint_pass": not has_blocking,
            "release_pass": not has_blocking and not has_skipped if is_release_check else None,
            "human_attention_required": has_blocking or has_skipped,
            "reason": reason,
            "recommendation": recommendation,
            "commit_message_suggestion": "",
        },
        "source_context": {
            "runtime_cards_used": runtime_cards,
            "fallback_sources": [],
            "fallback_reasons": [],
        },
        "fallback": {
            "used": False,
            "reasons": [],
            "source_reads": [],
        },
    }
    
    return review_output


def main():
    parser = argparse.ArgumentParser(description="Generate review_output.json")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["staged", "branch", "release-check"],
        help="Override tool mode",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path (default: .runtime/review_output.json or .runtime/release_review_output.json)",
    )
    args = parser.parse_args()

    # Determine if release-check mode
    is_release = args.mode == "release-check"
    
    # Load context
    context_file = RELEASE_CONTEXT_FILE if is_release else CONTEXT_FILE
    context = load_json(context_file)
    if context is None:
        print(f"Warning: {context_file} not found, creating minimal output", file=sys.stderr)
        context = {}
    
    # Load gate results
    gate_file = RELEASE_GATE_RESULTS_FILE if is_release else GATE_RESULTS_FILE
    gate_results = load_json(gate_file)
    if gate_results is None:
        print(f"Warning: {gate_file} not found, proceeding without", file=sys.stderr)
        gate_results = {}
    
    # Determine tool mode
    tool_mode = get_tool_mode(args.mode, context)
    
    # Create review output
    review_output = create_review_output(context, gate_results, tool_mode)
    
    # Update for release-check specific fields
    if is_release:
        review_output["release_check_hints"]["should_release"] = (
            not review_output.get("blocking_issues") and 
            not review_output.get("final_decision", {}).get("human_attention_required")
        )
        review_output["final_decision"]["recommendation"] = (
            "release" if review_output["release_check_hints"]["should_release"] 
            else "manual-review"
        )
    
    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = RELEASE_OUTPUT_FILE if is_release else OUTPUT_FILE
    save_json(output_path, review_output)
    
    print(f"Review output written to: {output_path}")
    print(f"  Mode: {tool_mode}")
    print(f"  Profile: {review_output['profile']}")
    print(f"  Triggered domains: {review_output['triggered_domains']}")
    print(f"  Gate status: {review_output['summary']['status']}")
    print(f"  Checkpoint pass: {review_output['final_decision']['checkpoint_pass']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
