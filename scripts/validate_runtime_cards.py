#!/usr/bin/env python3
"""
Runtime Domain Cards 校验器

校验 .runtime/domain_cards/ 下的卡片是否符合运行时要求。

用法:
    python scripts/validate_runtime_cards.py
    python scripts/validate_runtime_cards.py --card risk
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = REPO_ROOT / ".runtime" / "domain_cards"
SCHEMA_FILE = REPO_ROOT / "policies" / "domain_card_schema.json"
MAP_FILE = REPO_ROOT / "policies" / "runtime_card_map.yaml"

VALID_CARD_NAMES = ["common", "backend", "frontend", "contract", "risk"]


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(card_data: dict, schema: dict) -> List[str]:
    """Basic schema validation without jsonschema library."""
    errors = []

    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in card_data:
            errors.append(f"Missing required field: {field}")

    properties = schema.get("properties", {})
    for field, field_schema in properties.items():
        if field not in card_data:
            continue

        expected_type = field_schema.get("type")
        value = card_data[field]

        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"Field '{field}' should be array, got {type(value).__name__}")
        elif expected_type == "object" and not isinstance(value, dict):
            errors.append(f"Field '{field}' should be object, got {type(value).__name__}")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"Field '{field}' should be integer, got {type(value).__name__}")

        if "enum" in field_schema and value not in field_schema["enum"]:
            errors.append(f"Field '{field}' value '{value}' not in enum {field_schema['enum']}")

    return errors


def validate_budget(card_data: dict) -> List[str]:
    """Validate card doesn't exceed budget limits."""
    errors = []

    budgets = card_data.get("budgets", {})
    stats = card_data.get("stats", {})

    max_lines = budgets.get("max_lines", float("inf"))
    max_chars = budgets.get("max_chars", float("inf"))
    line_count = stats.get("line_count", 0)
    char_count = stats.get("char_count", 0)

    if line_count > max_lines:
        errors.append(f"Card exceeds max_lines: {line_count} > {max_lines}")

    if char_count > max_chars:
        errors.append(f"Card exceeds max_chars: {char_count} > {max_chars}")

    return errors


def validate_required_fields_non_empty(card_data: dict) -> List[str]:
    """Validate that required fields are non-empty."""
    errors = []
    required_non_empty = ["responsibilities", "required_checks", "output_requirements", "source_refs"]

    for field in required_non_empty:
        value = card_data.get(field)
        if not value:
            errors.append(f"Required field '{field}' is empty or missing")
        elif isinstance(value, list) and len(value) == 0:
            errors.append(f"Required field '{field}' is empty list")

    return errors


def validate_no_duplicates(card_data: dict) -> List[str]:
    """Check for duplicate items within each field."""
    errors = []
    array_fields = [
        "responsibilities", "trigger_patterns", "required_checks",
        "false_positive_hints", "escalation_rules", "output_requirements",
    ]

    for field in array_fields:
        items = card_data.get(field, [])
        if not isinstance(items, list):
            continue

        seen = set()
        for item in items:
            normalized = item.lower().strip().rstrip("。.！!")
            if normalized in seen:
                errors.append(f"Duplicate item in '{field}': '{item}'")
            seen.add(normalized)

    return errors


def validate_source_refs(card_data: dict) -> List[str]:
    """Validate that source_ref files exist."""
    errors = []
    source_refs = card_data.get("source_refs", [])

    for ref in source_refs:
        file_path = REPO_ROOT / ref.get("file", "")
        if not file_path.exists():
            errors.append(f"Source ref file not found: {ref.get('file')}")

    return errors


def validate_single_card(card_name: str) -> Tuple[bool, List[str]]:
    """Validate a single card. Returns (valid, errors)."""
    errors = []

    json_path = CARDS_DIR / f"{card_name}.json"
    md_path = CARDS_DIR / f"{card_name}.md"

    if not json_path.exists():
        return False, [f"JSON card not found: {json_path}"]

    if not md_path.exists():
        errors.append(f"Markdown card not found: {md_path}")

    # Load and validate JSON
    try:
        card_data = load_json(json_path)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in {json_path}: {e}"]

    # Load schema
    schema = {}
    if SCHEMA_FILE.exists():
        try:
            schema = load_json(SCHEMA_FILE)
        except Exception:
            pass

    # Run validations
    errors.extend(validate_schema(card_data, schema))
    errors.extend(validate_budget(card_data))
    errors.extend(validate_required_fields_non_empty(card_data))
    errors.extend(validate_no_duplicates(card_data))
    errors.extend(validate_source_refs(card_data))

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="Validate runtime domain cards")
    parser.add_argument("--card", type=str, help="Validate only specified card")
    args = parser.parse_args()

    if args.card:
        if args.card not in VALID_CARD_NAMES:
            print(f"ERROR: Unknown card '{args.card}'. Valid: {', '.join(VALID_CARD_NAMES)}", file=sys.stderr)
            sys.exit(1)
        cards_to_validate = [args.card]
    else:
        cards_to_validate = VALID_CARD_NAMES

    all_valid = True

    for card_name in cards_to_validate:
        valid, errors = validate_single_card(card_name)
        if valid:
            print(f"✅ {card_name}: valid")
        else:
            all_valid = False
            print(f"❌ {card_name}: {len(errors)} error(s)")
            for err in errors:
                print(f"   - {err}")

    if not all_valid:
        sys.exit(1)

    print("\nAll cards validated successfully.")


if __name__ == "__main__":
    main()
