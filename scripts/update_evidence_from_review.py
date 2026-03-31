#!/usr/bin/env python3
"""
Update evidence from structured review output.

Reads review_output.json, validates against schema, deduplicates with existing
evidence, and writes new evidence to evidence/active/.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = REPO_ROOT / "evidence" / "active"
RENDER_SCRIPT = REPO_ROOT / "scripts" / "render_review_evidence.py"
SCHEMA_FILE = REPO_ROOT / "policies" / "review_output_schema.json"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON file atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


def load_schema() -> Optional[Dict[str, Any]]:
    """Load review output schema."""
    return load_json(SCHEMA_FILE)


def load_all_evidence() -> List[Dict[str, Any]]:
    """Load all active evidence."""
    if not EVIDENCE_DIR.exists():
        return []
    
    evidence_list = []
    for f in EVIDENCE_DIR.glob("*.json"):
        data = load_json(f)
        if data:
            evidence_list.append(data)
    return evidence_list


def is_duplicate(candidate: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    """Check if candidate is duplicate of existing evidence."""
    # Check domain/title/trigger similarity
    cand_title = candidate.get("title", "").lower().strip()
    exist_title = existing.get("title", "").lower().strip()
    
    if cand_title == exist_title:
        return True
    
    # Check if domain matches and reason/trigger is similar
    cand_domain = candidate.get("domain", "").lower()
    exist_domain = existing.get("domain", "").lower()
    
    if cand_domain == exist_domain and cand_domain:
        # Check files overlap
        cand_files = set(candidate.get("files", []))
        exist_files = set(existing.get("files", []))
        
        if cand_files & exist_files:  # Has overlap
            return True
    
    return False


def find_duplicate(candidate: Dict[str, Any], evidence_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find duplicate evidence."""
    for existing in evidence_list:
        if is_duplicate(candidate, existing):
            return existing
    return None


def generate_evidence_id() -> str:
    """Generate new evidence ID."""
    today = datetime.now().strftime("%Y%m%d")
    
    # Find existing IDs for today
    existing_ids = []
    for f in EVIDENCE_DIR.glob(f"EV-{today}-*.json"):
        existing_ids.append(f.stem)
    
    # Find next number
    next_num = 1
    for eid in existing_ids:
        try:
            num = int(eid.split("-")[-1])
            if num >= next_num:
                next_num = num + 1
        except ValueError:
            pass
    
    return f"EV-{today}-{next_num:03d}"


def convert_candidate_to_evidence(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Convert review candidate to evidence format."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    evidence = {
        "id": generate_evidence_id(),
        "title": candidate.get("title", "Untitled"),
        "type": "盲区" if candidate.get("level") == "盲区" else "observation",
        "level": candidate.get("level", "observation"),
        "severity": candidate.get("severity", "中"),
        "tags": candidate.get("tags", []),
        "status": "active",
        "first_seen": today,
        "last_seen": today,
        "header_time": f"{today} 00:00",
        "occurrences": 1,
        "files": candidate.get("files", []),
        "scenario": candidate.get("reason", ""),
        "current_practice": "",
        "rule_gap": candidate.get("reason", ""),
        "suggestion": "",
        "signals": [],
        "source": "review_output",
    }
    
    return evidence


def update_duplicate(duplicate: Dict[str, Any]) -> Dict[str, Any]:
    """Update existing duplicate evidence."""
    duplicate["last_seen"] = datetime.now().strftime("%Y-%m-%d")
    duplicate["occurrences"] = duplicate.get("occurrences", 1) + 1
    return duplicate


def validate_review_output(review_data: Dict[str, Any]) -> bool:
    """Basic validation of review output."""
    required_fields = [
        "schema_version",
        "generated_at",
        "tool_mode",
        "review_run_id",
        "profile",
        "triggered_domains",
        "summary",
        "final_decision",
    ]
    
    for field in required_fields:
        if field not in review_data:
            print(f"Warning: Missing required field: {field}", file=sys.stderr)
            return False
    
    return True


def render_dashboard() -> bool:
    """Render the evidence dashboard."""
    if not RENDER_SCRIPT.exists():
        print(f"Warning: Render script not found: {RENDER_SCRIPT}", file=sys.stderr)
        return False
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(RENDER_SCRIPT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"Warning: Render failed: {result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Warning: Render error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Update evidence from review output")
    parser.add_argument(
        "--input",
        type=str,
        default=".runtime/review_output.json",
        help="Path to review output JSON (default: .runtime/review_output.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write anything, just show what would be done",
    )
    args = parser.parse_args()
    
    input_path = REPO_ROOT / args.input
    
    print(f"Loading review output from: {input_path}")
    review_data = load_json(input_path)
    
    if review_data is None:
        print(f"Error: Could not load review output from {input_path}", file=sys.stderr)
        return 1
    
    # Validate
    if not validate_review_output(review_data):
        print("Warning: Review output validation failed, continuing anyway...", file=sys.stderr)
    
    # Get candidates
    candidates = review_data.get("evidence_candidates", [])
    if not candidates:
        print("No evidence candidates found in review output.")
        return 0
    
    print(f"Found {len(candidates)} evidence candidates")
    
    # Load existing evidence
    existing_evidence = load_all_evidence()
    print(f"Loaded {len(existing_evidence)} existing evidence entries")
    
    # Process candidates
    new_count = 0
    updated_count = 0
    
    for candidate in candidates:
        duplicate = find_duplicate(candidate, existing_evidence)
        
        if duplicate:
            # Update existing
            updated = update_duplicate(duplicate)
            if not args.dry_run:
                dup_path = EVIDENCE_DIR / f"{duplicate['id']}.json"
                save_json(dup_path, updated)
            print(f"  Updated: {duplicate['id']} (occurrences: {updated['occurrences']})")
            updated_count += 1
        else:
            # Create new
            new_evidence = convert_candidate_to_evidence(candidate)
            if not args.dry_run:
                new_path = EVIDENCE_DIR / f"{new_evidence['id']}.json"
                save_json(new_path, new_evidence)
            print(f"  New: {new_evidence['id']} - {new_evidence['title']}")
            new_count += 1
    
    print(f"\nSummary: {new_count} new, {updated_count} updated")
    
    # Render dashboard
    if new_count > 0 or updated_count > 0:
        if not args.dry_run:
            print("\nRendering dashboard...")
            if render_dashboard():
                print("Dashboard rendered successfully.")
            else:
                print("Warning: Dashboard render failed.")
        else:
            print("\n(Dry run - skipped dashboard render)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
