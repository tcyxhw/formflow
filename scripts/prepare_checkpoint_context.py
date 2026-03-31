#!/usr/bin/env python3
"""
Checkpoint Context 准备器

分析 staged diff，生成 runtime capsule 和 context JSON，供 /checkpoint 使用。

用法:
    python scripts/prepare_checkpoint_context.py --staged
    python scripts/prepare_checkpoint_context.py --branch origin/main
    python scripts/prepare_checkpoint_context.py --staged --output-dir .runtime
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".runtime"
CARDS_DIR = REPO_ROOT / ".runtime" / "domain_cards"

# Policy files
REVIEW_DOMAINS_FILE = REPO_ROOT / "policies" / "review_domains.yaml"
RISK_KEYWORDS_FILE = REPO_ROOT / "policies" / "risk_keywords.yaml"
TASK_PROFILES_FILE = REPO_ROOT / "policies" / "task_profiles.yaml"
CARD_MANIFEST_FILE = CARDS_DIR / "manifest.json"


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_git(args: List[str]) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=30,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_staged_diff_summary() -> Dict[str, Any]:
    """Get staged diff summary."""
    stat = run_git(["diff", "--cached", "--stat", "--", "."])
    names = run_git(["diff", "--cached", "--name-only", "--", "."])
    numstat = run_git(["diff", "--cached", "--numstat", "--", "."])

    changed_files = []
    if names:
        changed_files = [f.strip() for f in names.split("\n") if f.strip()]

    total_additions = 0
    total_deletions = 0
    if numstat:
        for line in numstat.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    add = int(parts[0]) if parts[0] != "-" else 0
                    delete = int(parts[1]) if parts[1] != "-" else 0
                    total_additions += add
                    total_deletions += delete
                except ValueError:
                    pass

    return {
        "stat": stat,
        "changed_files": changed_files,
        "additions": total_additions,
        "deletions": total_deletions,
        "total_lines": total_additions + total_deletions,
    }


def get_branch_diff_summary(ref: str) -> Dict[str, Any]:
    """Get branch diff summary."""
    stat = run_git(["diff", "--stat", f"{ref}...HEAD", "--", "."])
    names = run_git(["diff", "--name-only", f"{ref}...HEAD", "--", "."])
    numstat = run_git(["diff", "--numstat", f"{ref}...HEAD", "--", "."])

    changed_files = []
    if names:
        changed_files = [f.strip() for f in names.split("\n") if f.strip()]

    total_additions = 0
    total_deletions = 0
    if numstat:
        for line in numstat.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    add = int(parts[0]) if parts[0] != "-" else 0
                    delete = int(parts[1]) if parts[1] != "-" else 0
                    total_additions += add
                    total_deletions += delete
                except ValueError:
                    pass

    return {
        "stat": stat,
        "changed_files": changed_files,
        "additions": total_additions,
        "deletions": total_deletions,
        "total_lines": total_additions + total_deletions,
    }


def classify_files_by_domain(changed_files: List[str], review_domains: dict) -> Dict[str, List[str]]:
    """Classify changed files into domains."""
    domains_config = review_domains.get("domains", {})
    file_groups: Dict[str, List[str]] = {
        "backend": [],
        "frontend": [],
        "contract": [],
        "risk": [],
        "other": [],
    }

    for f in changed_files:
        matched = False
        for domain, config in domains_config.items():
            paths = config.get("paths", [])
            for path_prefix in paths:
                if f.startswith(path_prefix) or f"/{path_prefix}" in f:
                    if domain not in file_groups:
                        file_groups[domain] = []
                    file_groups[domain].append(f)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            file_groups["other"].append(f)

    return file_groups


def detect_cross_layer(changed_files: List[str], cross_layer_path_sets: list) -> bool:
    """Detect if changes span multiple layers."""
    for path_set in cross_layer_path_sets:
        if isinstance(path_set, list) and len(path_set) >= 2:
            matched_paths = set()
            for path in path_set:
                for f in changed_files:
                    if path in f:
                        matched_paths.add(path)
                        break
            if len(matched_paths) >= 2:
                return True
    return False


def detect_risky_keywords(changed_files: List[str], risky_keywords: List[str]) -> List[str]:
    """Detect risky keywords in file paths."""
    found = []
    for keyword in risky_keywords:
        for f in changed_files:
            if keyword.lower() in f.lower():
                found.append(keyword)
                break
    return found


def determine_profile(
    changed_files_count: int,
    total_lines: int,
    cross_layer: bool,
    risky_keywords: List[str],
    task_profiles: dict,
) -> Tuple[str, List[str]]:
    """Determine Lite/Normal/Strict profile."""
    reasons = []
    strict_config = task_profiles.get("strict", {})
    triggers = strict_config.get("triggers", {})

    # Check strict triggers
    if changed_files_count >= triggers.get("changed_files_gte", 999):
        reasons.append(f"multi-file change ({changed_files_count} files)")

    if total_lines >= triggers.get("changed_lines_gte", 999):
        reasons.append(f"large change ({total_lines} lines)")

    if cross_layer:
        reasons.append("cross-layer change detected")

    if risky_keywords:
        reasons.append(f"risky keywords matched: {', '.join(risky_keywords[:5])}")

    if reasons:
        return "Strict", reasons

    # Check lite constraints
    lite_config = task_profiles.get("lite", {})
    if (changed_files_count <= lite_config.get("max_files", 2) and
        total_lines <= lite_config.get("max_changed_lines", 120) and
        not cross_layer):
        return "Lite", ["small change within lite bounds"]

    return "Normal", ["default profile"]


def get_required_runtime_cards(triggered_domains: List[str]) -> List[str]:
    """Get list of required runtime card paths."""
    cards = [".runtime/domain_cards/common.md"]
    for domain in triggered_domains:
        if domain in ("backend", "frontend", "contract", "risk"):
            cards.append(f".runtime/domain_cards/{domain}.md")
    return cards


KEYWORD_TO_DOMAIN_MAP = {
    "schema": "contract",
    "contract": "contract",
    "api": "contract",
    "types": "contract",
    "type": "contract",
    "security": "risk",
    "permission": "risk",
    "auth": "risk",
    "jwt": "risk",
    "tenant": "risk",
    "role": "risk",
    "delete": "risk",
    "cascade": "risk",
    "migrate": "risk",
    "migration": "risk",
    "transaction": "risk",
    "workflow": "risk",
    "rollback": "risk",
}


def enhance_triggered_domains(
    triggered_domains: List[str],
    risky_keywords: List[str]
) -> List[str]:
    """Enhance triggered domains based on risky keywords.
    
    If risky keywords are found that map to specific domains (contract/risk),
    add those domains to triggered_domains.
    """
    result = list(set(triggered_domains))  # Deduplicate
    
    for keyword in risky_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in KEYWORD_TO_DOMAIN_MAP:
            domain = KEYWORD_TO_DOMAIN_MAP[keyword_lower]
            if domain not in result:
                result.append(domain)
    
    return result


def load_card_manifest() -> dict:
    """Load runtime card manifest."""
    if CARD_MANIFEST_FILE.exists():
        return load_json(CARD_MANIFEST_FILE)
    return {}


def get_card_status(manifest: dict, domain: str) -> str:
    """Get card status from manifest."""
    cards = manifest.get("cards", {})
    card_info = cards.get(domain, {})
    return card_info.get("status", "missing")


def generate_context_json(
    git_mode: str,
    diff_summary: Dict[str, Any],
    file_groups: Dict[str, List[str]],
    profile: str,
    profile_reasons: List[str],
    triggered_domains: List[str],
    required_cards: List[str],
    card_manifest: dict,
    cross_layer: bool,
    risky_keywords: List[str],
) -> dict:
    """Generate checkpoint_context.json content."""
    now = datetime.now(timezone.utc).isoformat()

    card_status = {}
    for domain in ["common", "backend", "frontend", "contract", "risk"]:
        card_status[domain] = get_card_status(card_manifest, domain)

    domain_routing = {}
    for domain, files in file_groups.items():
        if files and domain != "other":
            domain_routing[domain] = {"matched_files": files[:5]}  # Limit to 5 files

    return {
        "review_run_id": f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "git_mode": git_mode,
        "generated_at": now,
        "target": "commit checkpoint",
        "profile": profile,  # Top-level profile for easy access
        "diff_summary": {
            "changed_files": len(diff_summary["changed_files"]),
            "additions": diff_summary["additions"],
            "deletions": diff_summary["deletions"],
            "file_groups": {k: len(v) for k, v in file_groups.items() if v},
            "cross_layer": cross_layer,
        },
        "initial_classification": {
            "profile": profile,
            "reasons": profile_reasons,
        },
        "triggered_domains": triggered_domains,
        "domain_routing": domain_routing,
        "required_runtime_cards": required_cards,
        "runtime_card_status": card_status,
        "allowed_capabilities": [
            "read_git_diff",
            "read_repository_files",
            "run_approved_analysis_scripts",
            "write_runtime_temp_outputs",
        ],
        "fallback": {
            "used": False,
            "reasons": [],
            "source_reads": [],
        },
    }


def generate_capsule_md(context: dict) -> str:
    """Generate checkpoint_capsule.md content."""
    lines = []
    lines.append("# Checkpoint Runtime Capsule")
    lines.append("")

    # Review Run
    lines.append("## Review Run")
    lines.append(f"- ID: {context['review_run_id']}")
    lines.append(f"- Mode: {context['git_mode']}")
    lines.append(f"- Generated: {context['generated_at']}")
    lines.append("")

    # Diff Summary
    diff = context["diff_summary"]
    lines.append("## Diff Summary")
    lines.append(f"- {diff['changed_files']} files changed (+{diff['additions']}, -{diff['deletions']})")

    groups = diff.get("file_groups", {})
    if groups:
        group_str = " | ".join(f"{k}: {v}" for k, v in groups.items())
        lines.append(f"- {group_str}")

    if diff.get("cross_layer"):
        lines.append("- Cross-layer: Yes")
    lines.append("")

    # Risk Classification
    classification = context["initial_classification"]
    lines.append("## Risk Classification")
    lines.append(f"- Profile: **{classification['profile']}**")
    for reason in classification.get("reasons", []):
        lines.append(f"- Reason: {reason}")
    lines.append("")

    # Triggered Domains
    domains = context.get("triggered_domains", [])
    lines.append("## Triggered Domains")
    if domains:
        for domain in domains:
            routing = context.get("domain_routing", {}).get(domain, {})
            files = routing.get("matched_files", [])
            file_str = ", ".join(files[:3]) if files else "by keyword"
            lines.append(f"- ✅ {domain} — matched: {file_str}")
    else:
        lines.append("- (none)")
    lines.append("")

    # Runtime Cards
    card_status = context.get("runtime_card_status", {})
    required_cards = context.get("required_runtime_cards", [])
    lines.append("## Runtime Cards")
    for card_path in required_cards:
        domain = Path(card_path).stem
        status = card_status.get(domain, "unknown")
        lines.append(f"- {domain} → {status}")
    lines.append("")

    # Allowed Capabilities
    lines.append("## Allowed Capabilities")
    caps = context.get("allowed_capabilities", [])
    for cap in caps:
        lines.append(f"- {cap}")
    lines.append("- NO arbitrary destructive shell")
    lines.append("- NO network")
    lines.append("- NO dependency install")
    lines.append("")

    # Lazy Load Manifest
    lines.append("## Lazy Load")
    for card_path in required_cards:
        if card_path != ".runtime/domain_cards/common.md":
            domain = Path(card_path).stem
            lines.append(f"- {domain} → {card_path}")
    lines.append("")

    return "\n".join(lines)


def generate_release_context_json(
    diff_summary: Dict[str, Any],
    file_groups: Dict[str, List[str]],
    profile: str,
    profile_reasons: List[str],
    triggered_domains: List[str],
    required_cards: List[str],
    card_manifest: dict,
    cross_layer: bool,
    risky_keywords: List[str],
    base_ref: str,
) -> dict:
    """Generate release_check_context.json content."""
    now = datetime.now(timezone.utc).isoformat()

    card_status = {}
    for domain in ["common", "backend", "frontend", "contract", "risk"]:
        card_status[domain] = get_card_status(card_manifest, domain)

    domain_routing = {}
    for domain, files in file_groups.items():
        if files and domain != "other":
            domain_routing[domain] = {"matched_files": files[:5]}

    return {
        "review_run_id": f"release_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "git_mode": "release-check",
        "base_ref": base_ref,
        "generated_at": now,
        "target": "release check",
        "profile": profile,
        "diff_summary": {
            "changed_files": len(diff_summary["changed_files"]),
            "additions": diff_summary["additions"],
            "deletions": diff_summary["deletions"],
            "file_groups": {k: len(v) for k, v in file_groups.items() if v},
            "cross_layer": cross_layer,
        },
        "initial_classification": {
            "profile": profile,
            "reasons": profile_reasons,
        },
        "triggered_domains": triggered_domains,
        "domain_routing": domain_routing,
        "required_runtime_cards": required_cards,
        "runtime_card_status": card_status,
        "allowed_capabilities": [
            "read_git_diff",
            "read_repository_files",
            "run_approved_analysis_scripts",
            "write_runtime_temp_outputs",
        ],
        "fallback": {
            "used": False,
            "reasons": [],
            "source_reads": [],
        },
    }


def generate_release_capsule_md(context: dict) -> str:
    """Generate release_check_capsule.md content."""
    lines = []
    lines.append("# Release Check Runtime Capsule")
    lines.append("")

    lines.append("## Review Run")
    lines.append(f"- ID: {context['review_run_id']}")
    lines.append(f"- Mode: {context['git_mode']}")
    lines.append(f"- Base Ref: {context['base_ref']}")
    lines.append(f"- Generated: {context['generated_at']}")
    lines.append("")

    diff = context["diff_summary"]
    lines.append("## Diff Summary")
    lines.append(f"- {diff['changed_files']} files changed (+{diff['additions']}, -{diff['deletions']})")

    groups = diff.get("file_groups", {})
    if groups:
        group_str = " | ".join(f"{k}: {v}" for k, v in groups.items())
        lines.append(f"- {group_str}")

    if diff.get("cross_layer"):
        lines.append("- Cross-layer: Yes")
    lines.append("")

    classification = context["initial_classification"]
    lines.append("## Risk Classification")
    lines.append(f"- Profile: **{classification['profile']}**")
    for reason in classification.get("reasons", []):
        lines.append(f"- Reason: {reason}")
    lines.append("")

    domains = context.get("triggered_domains", [])
    lines.append("## Triggered Domains")
    if domains:
        for domain in domains:
            routing = context.get("domain_routing", {}).get(domain, {})
            files = routing.get("matched_files", [])
            file_str = ", ".join(files[:3]) if files else "by keyword"
            lines.append(f"- ✅ {domain} — matched: {file_str}")
    else:
        lines.append("- (none)")
    lines.append("")

    card_status = context.get("runtime_card_status", {})
    required_cards = context.get("required_runtime_cards", [])
    lines.append("## Runtime Cards")
    for card_path in required_cards:
        domain = Path(card_path).stem
        status = card_status.get(domain, "unknown")
        lines.append(f"- {domain} → {status}")
    lines.append("")

    lines.append("## Release Focus")
    lines.append("- Contract final closure")
    lines.append("- Cumulative risk review")
    lines.append("- Release blockers")
    lines.append("")

    lines.append("## Allowed Capabilities")
    caps = context.get("allowed_capabilities", [])
    for cap in caps:
        lines.append(f"- {cap}")
    lines.append("- NO arbitrary destructive shell")
    lines.append("- NO network")
    lines.append("- NO dependency install")
    lines.append("")

    lines.append("## Lazy Load")
    for card_path in required_cards:
        if card_path != ".runtime/domain_cards/common.md":
            domain = Path(card_path).stem
            lines.append(f"- {domain} → {card_path}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Prepare checkpoint/release runtime context")
    parser.add_argument("--staged", action="store_true", help="Analyze staged changes")
    parser.add_argument("--branch", type=str, help="Analyze branch diff against ref")
    parser.add_argument("--mode", type=str, choices=["checkpoint", "release-check"],
                       help="Runtime mode: checkpoint or release-check (default: checkpoint)")
    parser.add_argument("--base-ref", type=str, default="origin/main",
                       help="Base ref for release-check mode (default: origin/main)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    # Determine mode and required parameters
    is_release_check = args.mode == "release-check"
    
    # Validate parameters
    if is_release_check:
        # release-check mode: use base-ref vs HEAD
        git_mode = "release-check"
        base_ref = args.base_ref
    elif args.staged:
        # staged mode
        git_mode = "staged"
        base_ref = "HEAD"
    elif args.branch:
        # branch mode
        git_mode = "branch"
        base_ref = args.branch
    else:
        # Default: staged mode
        git_mode = "staged"
        args.staged = True
        base_ref = "HEAD"

    # Get diff based on mode
    if args.staged:
        diff_summary = get_staged_diff_summary()
    else:
        diff_summary = get_branch_diff_summary(base_ref)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load policies
    review_domains = load_yaml(REVIEW_DOMAINS_FILE) if REVIEW_DOMAINS_FILE.exists() else {}
    risk_keywords = load_yaml(RISK_KEYWORDS_FILE) if RISK_KEYWORDS_FILE.exists() else {}
    task_profiles = load_yaml(TASK_PROFILES_FILE) if TASK_PROFILES_FILE.exists() else {}

    changed_files = diff_summary["changed_files"]

    if not changed_files:
        print("No changes detected.", file=sys.stderr)
        # Write minimal context
        context = {
            "review_run_id": f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "git_mode": git_mode,
            "base_ref": base_ref,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target": "release check" if is_release_check else "commit checkpoint",
            "profile": "N/A",
            "diff_summary": {"changed_files": 0, "additions": 0, "deletions": 0, "file_groups": {}, "cross_layer": False},
            "initial_classification": {"profile": "N/A", "reasons": ["no changes"]},
            "triggered_domains": [],
            "domain_routing": {},
            "required_runtime_cards": [],
            "runtime_card_status": {},
            "allowed_capabilities": [],
            "fallback": {
                "used": False,
                "reasons": [],
                "source_reads": [],
            },
        }
        context_path = output_dir / "release_check_context.json" if is_release_check else output_dir / "checkpoint_context.json"
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        print(f"Context written to: {context_path}")
        sys.exit(0)

    # Classify files
    file_groups = classify_files_by_domain(changed_files, review_domains)

    # Detect cross-layer
    cross_layer_sets = risk_keywords.get("cross_layer_path_sets", [])
    cross_layer = detect_cross_layer(changed_files, cross_layer_sets)

    # Detect risky keywords
    risky_kw_list = risk_keywords.get("strict_keywords", [])
    # Also check from review_domains keywords
    for domain, config in review_domains.get("domains", {}).items():
        for kw in config.get("keywords", []):
            if kw not in risky_kw_list:
                risky_kw_list.append(kw)

    risky_keywords_found = detect_risky_keywords(changed_files, risky_kw_list)

    # Determine profile
    profile, profile_reasons = determine_profile(
        len(changed_files),
        diff_summary["total_lines"],
        cross_layer,
        risky_keywords_found,
        task_profiles,
    )

    # Determine triggered domains
    triggered_domains = [d for d, files in file_groups.items() if files and d != "other"]
    
    # Enhance triggered domains based on risky keywords
    triggered_domains = enhance_triggered_domains(triggered_domains, risky_keywords_found)

    # Load card manifest
    card_manifest = load_card_manifest()

    # Get required cards
    required_cards = get_required_runtime_cards(triggered_domains)

    # Generate context
    if is_release_check:
        context = generate_release_context_json(
            diff_summary=diff_summary,
            file_groups=file_groups,
            profile=profile,
            profile_reasons=profile_reasons,
            triggered_domains=triggered_domains,
            required_cards=required_cards,
            card_manifest=card_manifest,
            cross_layer=cross_layer,
            risky_keywords=risky_keywords_found,
            base_ref=base_ref,
        )
    else:
        context = generate_context_json(
            git_mode=git_mode,
            diff_summary=diff_summary,
            file_groups=file_groups,
            profile=profile,
            profile_reasons=profile_reasons,
            triggered_domains=triggered_domains,
            required_cards=required_cards,
            card_manifest=card_manifest,
            cross_layer=cross_layer,
            risky_keywords=risky_keywords_found,
        )

    # Write context JSON
    if is_release_check:
        context_path = output_dir / "release_check_context.json"
    else:
        context_path = output_dir / "checkpoint_context.json"
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
    print(f"Context written to: {context_path}")

    # Write capsule
    if is_release_check:
        capsule_content = generate_release_capsule_md(context)
        capsule_path = output_dir / "release_check_capsule.md"
    else:
        capsule_content = generate_capsule_md(context)
        capsule_path = output_dir / "checkpoint_capsule.md"
    with open(capsule_path, "w", encoding="utf-8") as f:
        f.write(capsule_content)
    print(f"Capsule written to: {capsule_path}")

    # Print summary
    print(f"\nProfile: {profile}")
    print(f"Triggered domains: {', '.join(triggered_domains) if triggered_domains else 'none'}")
    print(f"Required cards: {len(required_cards)}")


if __name__ == "__main__":
    main()
