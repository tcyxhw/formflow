#!/usr/bin/env python3
"""
Domain Cards 自动编译器

将 standards/ 和 policies/ 中的人类维护规则，编译为 .runtime/domain_cards/ 下的运行时卡片。

用法:
    python scripts/build_rule_runtime_cards.py
    python scripts/build_rule_runtime_cards.py --card risk
    python scripts/build_rule_runtime_cards.py --changed-only
    python scripts/build_rule_runtime_cards.py --strict
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

GENERATOR_VERSION = "1.0"
SCHEMA_VERSION = "1.0"
REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = REPO_ROOT / "policies" / "runtime_card_map.yaml"
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".runtime" / "domain_cards"
MANIFEST_FILE = "manifest.json"


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_existing_manifest(output_dir: Path) -> dict:
    manifest_path = output_dir / MANIFEST_FILE
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def normalize_heading(heading: str) -> str:
    """Normalize heading for matching: strip, lowercase, spaces to dashes."""
    return heading.strip().lower().replace(" ", "-")


def heading_matches(normalized_heading: str, normalized_target: str) -> bool:
    """Check if a heading matches a target.

    Supports:
    - Exact match
    - Target is substring of heading (e.g., '通用行为规则' matches '一、通用行为规则')
    - Heading is substring of target
    """
    if normalized_heading == normalized_target:
        return True
    if normalized_target in normalized_heading:
        return True
    if normalized_heading in normalized_target:
        return True
    # Also try after stripping common prefixes like numbering
    stripped = re.sub(r'^[\d一二三四五六七八九十]+[、.]\s*', '', normalized_heading)
    if stripped == normalized_target or normalized_target in stripped:
        return True
    return False


def extract_markdown_section(file_path: Path, section_name: str) -> List[str]:
    """Extract a markdown section by heading name.

    Supports both exact match and normalized match.
    Returns list of content lines (without the heading itself).
    """
    if not file_path.exists():
        return []

    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    normalized_target = normalize_heading(section_name)
    section_start = None
    section_level = 0

    for i, line in enumerate(lines):
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            normalized_heading = normalize_heading(heading_text)

            if heading_matches(normalized_heading, normalized_target):
                section_start = i + 1
                section_level = level
            elif section_start is not None and level <= section_level:
                # Hit a same-level or higher-level heading, section ends
                return _clean_lines(lines[section_start:i])

    if section_start is not None:
        return _clean_lines(lines[section_start:])

    return []


def _clean_lines(lines: List[str]) -> List[str]:
    """Remove empty leading/trailing lines, normalize whitespace."""
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            result.append(stripped)
        elif result and result[-1] != "":
            result.append("")
    # Remove trailing empty lines
    while result and result[-1] == "":
        result.pop()
    return result


def extract_policy_value(file_path: Path, key_path: str) -> Any:
    """Extract a value from YAML/JSON by dot-separated key path."""
    if not file_path.exists():
        return None

    data = load_yaml(file_path)
    keys = key_path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def compute_source_hash(card_config: dict, map_config_hash: str) -> str:
    """Compute SHA256 hash of all source content for a card."""
    hasher = hashlib.sha256()
    hasher.update(map_config_hash.encode("utf-8"))

    for section_def in card_config.get("markdown_sections", []):
        file_path = REPO_ROOT / section_def["file"]
        for section in section_def.get("sections", []):
            content = extract_markdown_section(file_path, section)
            hasher.update("\n".join(content).encode("utf-8"))

    for policy_ref in card_config.get("policy_refs", []):
        file_path = REPO_ROOT / policy_ref["file"]
        key = policy_ref["key"]
        value = extract_policy_value(file_path, key)
        if value is not None:
            hasher.update(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8"))

    return hasher.hexdigest()


def classify_line_to_field(line: str, source_type: str, section_name: str = "") -> Optional[str]:
    """Classify a content line to a card field based on heuristics and section context."""
    line_lower = line.lower().strip("- ")
    section_lower = section_name.lower()

    # Output requirements - check FIRST to catch "输出要求" before it gets classified as responsibilities
    if any(kw in line_lower for kw in ["输出要求", "output requirement"]):
        return "output_requirements"

    # If the section is about a specific reviewer, items go to responsibilities
    if any(kw in section_lower for kw in ["reviewer", "审查", "orchestrator"]):
        if any(kw in line_lower for kw in ["职责", "负责", "审查", "关注", "输出重点"]):
            return "responsibilities"
        # Items in reviewer sections are generally responsibilities or required checks
        if any(kw in line_lower for kw in ["必须", "检查", "校验", "验证"]):
            return "required_checks"
        return "responsibilities"

    # Trigger patterns
    if any(kw in line_lower for kw in ["触发", "命中", "trigger", "when", "条件"]):
        return "trigger_patterns"

    # False positive hints
    if any(kw in line_lower for kw in ["误报", "不应", "不接受", "false positive", "不等于"]):
        return "false_positive_hints"

    # Escalation rules
    if any(kw in line_lower for kw in ["升级", "阻断", "escalation", "blocking", "->"]):
        return "escalation_rules"

    # Output requirements (fallback for other output-related keywords)
    if any(kw in line_lower for kw in ["输出", "必须包含", "格式"]):
        return "output_requirements"

    # Required checks
    if any(kw in line_lower for kw in ["必须", "检查", "check", "关注", "验证", "是否存在"]):
        return "required_checks"

    # Responsibilities
    if any(kw in line_lower for kw in ["职责", "负责", "用于", "目标"]):
        return "responsibilities"

    # Default: if from markdown, put in required_checks
    if source_type == "markdown":
        return "required_checks"

    return None


def extract_list_items(lines: List[str]) -> List[str]:
    """Extract list items from markdown content lines.

    Supports:
    - Bullet lists: - item, * item
    - Numbered lists: 1. item, 2. item
    - Indented items:   - item (nested under parent)
    - Paragraph items: lines that are content (not headings, not empty)
    """
    items = []
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        # Skip heading lines
        if re.match(r"^#{1,6}\s+", line):
            continue
        # Skip horizontal rules
        if re.match(r"^---+$", line):
            continue

        # Match list items: - item, * item
        match = re.match(r"^[-*]\s+(.+)$", line)
        if match:
            items.append(match.group(1).strip())
            continue

        # Match numbered lists: 1. item, 2. item
        match = re.match(r"^\d+\.\s+(.+)$", line)
        if match:
            items.append(match.group(1).strip())
            continue

        # If it's a non-empty line that's not a heading, treat as content
        stripped = line.strip()
        if stripped and len(stripped) > 3:
            items.append(stripped)

    return items


def build_card_fields(card_config: dict) -> Dict[str, List[str]]:
    """Build structured fields from markdown sections and policy refs."""
    fields: Dict[str, List[str]] = {
        "responsibilities": [],
        "trigger_patterns": [],
        "required_checks": [],
        "false_positive_hints": [],
        "escalation_rules": [],
        "output_requirements": [],
    }

    assembly = card_config.get("assembly", {})

    # Process markdown sections
    for section_def in card_config.get("markdown_sections", []):
        file_path = REPO_ROOT / section_def["file"]
        for section in section_def.get("sections", []):
            content_lines = extract_markdown_section(file_path, section)
            items = extract_list_items(content_lines)

            # Determine which field based on assembly config and content
            for item in items:
                classified = classify_line_to_field(item, "markdown", section)
                if classified and classified in fields:
                    fields[classified].append(item)
                elif classified is None:
                    # Default to required_checks for unclassified items
                    fields["required_checks"].append(item)

    # Process policy refs
    for policy_ref in card_config.get("policy_refs", []):
        file_path = REPO_ROOT / policy_ref["file"]
        key = policy_ref["key"]
        value = extract_policy_value(file_path, key)

        if value is None:
            continue

        if isinstance(value, list):
            # Keywords or paths -> trigger_patterns
            if key in ("strict_keywords", "cross_layer_path_sets"):
                for item in value:
                    if isinstance(item, list):
                        fields["trigger_patterns"].append(" -> ".join(item))
                    else:
                        fields["trigger_patterns"].append(str(item))
            elif "paths" in key or "keywords" in key:
                for item in value:
                    if isinstance(item, list):
                        fields["trigger_patterns"].append(" -> ".join(item))
                    else:
                        fields["trigger_patterns"].append(str(item))
        elif isinstance(value, dict):
            if "paths" in value:
                for p in value["paths"]:
                    fields["trigger_patterns"].append(f"path: {p}")
            if "keywords" in value:
                for k in value["keywords"]:
                    fields["trigger_patterns"].append(f"keyword: {k}")

    return fields


def dedupe_list(items: List[str]) -> List[str]:
    """Deduplicate items with normalization."""
    seen = set()
    result = []
    for item in items:
        normalized = item.lower().strip().rstrip("。.！!")
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(item.strip())
    return result


def apply_budget(fields: Dict[str, List[str]], budgets: dict) -> Tuple[Dict[str, List[str]], List[str]]:
    """Apply budget limits to fields. Returns (trimmed_fields, warnings)."""
    warnings = []
    max_lines = budgets.get("max_lines", 160)

    total_lines = sum(len(v) for v in fields.values())
    if total_lines <= max_lines:
        return fields, warnings

    # Priority order: responsibilities > required_checks > trigger_patterns > output_requirements > escalation_rules > false_positive_hints
    priority_order = [
        "responsibilities",
        "required_checks",
        "trigger_patterns",
        "output_requirements",
        "escalation_rules",
        "false_positive_hints",
    ]

    trimmed = {}
    remaining = max_lines
    for field_name in priority_order:
        items = fields.get(field_name, [])
        if remaining <= 0:
            trimmed[field_name] = []
            if items:
                warnings.append(f"Field '{field_name}' dropped due to budget limit")
        elif len(items) <= remaining:
            trimmed[field_name] = items
            remaining -= len(items)
        else:
            trimmed[field_name] = items[:remaining]
            warnings.append(f"Field '{field_name}' trimmed from {len(items)} to {remaining} items")
            remaining = 0

    return trimmed, warnings


def render_markdown_card(card_data: dict) -> str:
    """Render a markdown card from JSON card data."""
    lines = []
    domain = card_data["domain"].upper()
    lines.append(f"# {domain} Reviewer Card")
    lines.append("")
    lines.append(f"- schema_version: {card_data['schema_version']}")
    lines.append(f"- generated_at: {card_data['generated_at']}")
    lines.append(f"- generator_version: {card_data['generator_version']}")
    lines.append(f"- source_hash: {card_data['source_hash']}")
    lines.append("")

    lines.append("## Source Refs")
    for ref in card_data["source_refs"]:
        ref_str = ref["file"]
        if "section" in ref:
            ref_str += f"#{ref['section']}"
        elif "key" in ref:
            ref_str += f"#{ref['key']}"
        lines.append(f"- {ref_str}")
    lines.append("")

    field_titles = {
        "responsibilities": "Responsibilities",
        "trigger_patterns": "Trigger Patterns",
        "required_checks": "Required Checks",
        "false_positive_hints": "False Positive Hints",
        "escalation_rules": "Escalation Rules",
        "output_requirements": "Output Requirements",
    }

    for field_name, title in field_titles.items():
        items = card_data.get(field_name, [])
        lines.append(f"## {title}")
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("- (none)")
        lines.append("")

    return "\n".join(lines)


def build_source_refs(card_config: dict) -> List[dict]:
    """Build source_refs list from card config."""
    refs = []
    for section_def in card_config.get("markdown_sections", []):
        for section in section_def.get("sections", []):
            refs.append({"file": section_def["file"], "section": section})
    for policy_ref in card_config.get("policy_refs", []):
        refs.append({"file": policy_ref["file"], "key": policy_ref["key"]})
    return refs


def build_single_card(
    card_name: str,
    card_config: dict,
    map_config_hash: str,
    output_dir: Path,
    existing_manifest: dict,
) -> Tuple[bool, dict, List[str]]:
    """Build a single domain card. Returns (success, card_manifest_entry, warnings)."""
    warnings = []
    now = datetime.now(timezone.utc).isoformat()

    # Check if source files exist
    missing_files = []
    for section_def in card_config.get("markdown_sections", []):
        file_path = REPO_ROOT / section_def["file"]
        if not file_path.exists():
            missing_files.append(str(file_path))
    for policy_ref in card_config.get("policy_refs", []):
        file_path = REPO_ROOT / policy_ref["file"]
        if not file_path.exists():
            missing_files.append(str(file_path))

    if missing_files:
        warnings.append(f"Missing source files: {', '.join(missing_files)}")
        # Try fallback
        existing_card = existing_manifest.get("cards", {}).get(card_name, {})
        if existing_card.get("status") == "ok":
            return False, {
                "status": "stale_fallback",
                "last_success_generated_at": existing_card.get("generated_at", "unknown"),
                "source_hash": existing_card.get("source_hash", "unknown"),
                "line_count": existing_card.get("line_count", 0),
                "warnings": warnings,
            }, warnings
        return False, {"status": "error", "warnings": warnings}, warnings

    # Compute source hash
    source_hash = compute_source_hash(card_config, map_config_hash)

    # Check if unchanged (for changed-only mode)
    existing_card = existing_manifest.get("cards", {}).get(card_name, {})
    if existing_card.get("source_hash") == source_hash and existing_card.get("status") == "ok":
        return True, {**existing_card, "status": "ok", "unchanged": True}, []

    # Build fields
    fields = build_card_fields(card_config)

    # Deduplicate
    for key in fields:
        fields[key] = dedupe_list(fields[key])

    # Apply budget
    budgets = card_config.get("budgets", {"max_lines": 160, "max_chars": 8000})
    fields, budget_warnings = apply_budget(fields, budgets)
    warnings.extend(budget_warnings)

    # Build source refs
    source_refs = build_source_refs(card_config)

    # Compute stats
    content_lines = []
    for items in fields.values():
        content_lines.extend(items)
    line_count = len(content_lines)
    char_count = sum(len(item) for item in content_lines)

    # Check budget compliance
    if line_count > budgets.get("max_lines", 160):
        warnings.append(f"Card exceeds max_lines budget: {line_count} > {budgets['max_lines']}")
    if char_count > budgets.get("max_chars", 8000):
        warnings.append(f"Card exceeds max_chars budget: {char_count} > {budgets['max_chars']}")

    # Build JSON card
    card_data = {
        "schema_version": SCHEMA_VERSION,
        "domain": card_name,
        "generated_at": now,
        "generator_version": GENERATOR_VERSION,
        "source_hash": source_hash,
        "source_refs": source_refs,
        "responsibilities": fields["responsibilities"],
        "trigger_patterns": fields["trigger_patterns"],
        "required_checks": fields["required_checks"],
        "false_positive_hints": fields["false_positive_hints"],
        "escalation_rules": fields["escalation_rules"],
        "output_requirements": fields["output_requirements"],
        "budgets": budgets,
        "stats": {
            "line_count": line_count,
            "char_count": char_count,
        },
    }

    # Validate required fields
    required_non_empty = ["responsibilities", "required_checks", "output_requirements", "source_refs"]
    for field in required_non_empty:
        if not card_data.get(field):
            warnings.append(f"Required field '{field}' is empty")

    # Write JSON card
    json_path = output_dir / f"{card_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, indent=2, ensure_ascii=False)

    # Write Markdown card
    md_content = render_markdown_card(card_data)
    md_path = output_dir / f"{card_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    manifest_entry = {
        "status": "ok",
        "source_hash": source_hash,
        "generated_at": now,
        "line_count": line_count,
        "char_count": char_count,
        "warnings": warnings,
    }

    return True, manifest_entry, warnings


def compute_map_config_hash(map_config: dict) -> str:
    """Compute hash of the map config for change detection."""
    return hashlib.sha256(
        json.dumps(map_config, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Build runtime domain cards")
    parser.add_argument("--card", type=str, help="Build only specified card (common/backend/frontend/contract/risk)")
    parser.add_argument("--changed-only", action="store_true", help="Only rebuild cards with changed source hash")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any card fails")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load map config
    if not MAP_FILE.exists():
        print(f"ERROR: Map config not found: {MAP_FILE}", file=sys.stderr)
        sys.exit(1)

    map_config = load_yaml(MAP_FILE)
    map_config_hash = compute_map_config_hash(map_config)
    cards_config = map_config.get("cards", {})

    # Load existing manifest
    existing_manifest = load_existing_manifest(output_dir)

    # Determine which cards to build
    all_cards = list(cards_config.keys())
    if args.card:
        if args.card not in all_cards:
            print(f"ERROR: Unknown card '{args.card}'. Available: {', '.join(all_cards)}", file=sys.stderr)
            sys.exit(1)
        cards_to_build = [args.card]
    else:
        cards_to_build = all_cards

    # Build cards
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "map_config_hash": map_config_hash,
        "cards": {},
    }

    any_failure = False
    all_warnings = []

    for card_name in cards_to_build:
        card_config = cards_config[card_name]
        print(f"Building card: {card_name}...")

        success, entry, warnings = build_single_card(
            card_name, card_config, map_config_hash, output_dir, existing_manifest
        )

        if entry.get("unchanged"):
            print(f"  -> unchanged (skipped)")
            # Keep existing entry
            manifest["cards"][card_name] = existing_manifest.get("cards", {}).get(card_name, entry)
            manifest["cards"][card_name].pop("unchanged", None)
        elif success:
            print(f"  -> ok ({entry.get('line_count', 0)} lines)")
            manifest["cards"][card_name] = entry
        else:
            print(f"  -> {entry.get('status', 'error')}", file=sys.stderr)
            manifest["cards"][card_name] = entry
            any_failure = True

        if warnings:
            for w in warnings:
                print(f"  WARNING: {w}", file=sys.stderr)
            all_warnings.extend(warnings)

    # Write manifest
    manifest_path = output_dir / MANIFEST_FILE
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nManifest written to: {manifest_path}")

    if args.strict and any_failure:
        print("ERROR: Strict mode enabled and some cards failed", file=sys.stderr)
        sys.exit(1)

    if any_failure:
        print("WARNING: Some cards failed or fell back to stale versions", file=sys.stderr)
    else:
        print("All cards built successfully.")


if __name__ == "__main__":
    main()
