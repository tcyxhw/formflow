#!/usr/bin/env python3
"""
Task Context 准备器

分析用户任务需求，生成 runtime context 和 capsule，供 /task 使用。

用法:
    python scripts/prepare_task_context.py --task "修复登录问题"
    python scripts/prepare_task_context.py --task "添加用户权限" --strict
    python scripts/prepare_task_context.py --task "优化查询性能" --lite
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".runtime"

TASK_PROFILES_FILE = REPO_ROOT / "policies" / "task_profiles.yaml"
RISK_KEYWORDS_FILE = REPO_ROOT / "policies" / "risk_keywords.yaml"
TASK_STAGE_ROUTING_FILE = REPO_ROOT / "policies" / "task_stage_routing.yaml"
REPO_PATHS_FILE = REPO_ROOT / "policies" / "repo_paths.yaml"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_task_keywords(task_text: str) -> List[str]:
    """Detect keywords in task description."""
    task_lower = task_text.lower()
    found = []
    
    keywords = [
        "auth", "permission", "security", "transaction", "state",
        "delete", "cascade", "migrate", "migration", "schema",
        "contract", "jwt", "tenant", "role", "workflow",
        "api", "type", "types", "frontend", "backend",
        "model", "service", "view", "component", "store",
        "bug", "fix", "optimize", "refactor", "test",
    ]
    
    for kw in keywords:
        if kw in task_lower:
            found.append(kw)
    
    return found


def detect_task_type(task_text: str, keywords: List[str]) -> Dict[str, bool]:
    """Detect task type (backend/frontend/fullstack)."""
    task_lower = task_text.lower()
    
    backend_indicators = [
        "backend", "api", "service", "model", "schema",
        "database", "sql", "auth", "permission", "security",
    ]
    frontend_indicators = [
        "frontend", "vue", "react", "component", "view",
        "page", "ui", "form", "button", "input",
    ]
    
    has_backend = any(ind in task_lower for ind in backend_indicators)
    has_frontend = any(ind in task_lower for ind in frontend_indicators)
    
    if has_backend and has_frontend:
        return {"backend": True, "frontend": True, "fullstack": True}
    elif has_backend:
        return {"backend": True, "frontend": False, "fullstack": False}
    elif has_frontend:
        return {"backend": False, "frontend": True, "fullstack": False}
    
    return {"backend": True, "frontend": True, "fullstack": False}


STYLE_UI_KEYWORDS = ["样式", "样式", "style", "css", "scss", "sass", "界面", "ui", "主题", "theme"]
RISK_KEYWORDS = ["auth", "permission", "security", "transaction", "state", "delete", "cascade", "migrate", "migration", "jwt", "tenant", "role", "workflow", "rollback", "权限", "删除", "安全", "事务"]
CONTRACT_KEYWORDS = ["schema", "contract", "api", "type", "types", "typescript", "interface", "schema", "dto", "payload", "response"]
FRONTEND_ONLY_KEYWORDS = ["样式", "样式", "style", "css", "vue", "component", "view", "page", "ui", "form", "button", "input", "display", "render"]
BACKEND_ONLY_KEYWORDS = ["backend", "service", "model", "database", "sql", "repository"]


def predict_domains(task_text: str, keywords: List[str], task_profiles: dict) -> List[str]:
    """Predict triggered domains based on task keywords with improved precision."""
    domains = []
    task_lower = task_text.lower()
    
    risk_keywords = task_profiles.get("strict", {}).get("triggers", {}).get("risky_keywords", [])
    
    has_style_ui = any(kw in task_lower for kw in STYLE_UI_KEYWORDS)
    has_risk = any(kw in task_lower for kw in RISK_KEYWORDS)
    has_contract = any(kw in task_lower for kw in CONTRACT_KEYWORDS)
    has_frontend_only = any(kw in task_lower for kw in FRONTEND_ONLY_KEYWORDS)
    has_backend_only = any(kw in task_lower for kw in BACKEND_ONLY_KEYWORDS)
    
    if has_style_ui and not has_risk and not has_contract:
        if "frontend" not in domains:
            domains.append("frontend")
        if "backend" not in domains:
            return domains
    
    if has_risk:
        if "risk" not in domains:
            domains.append("risk")
        if has_backend_only or "backend" not in domains:
            if "backend" not in domains:
                domains.append("backend")
    
    if has_contract:
        if "contract" not in domains:
            domains.append("contract")
    
    for kw in keywords:
        if kw in CONTRACT_KEYWORDS:
            if "contract" not in domains:
                domains.append("contract")
        elif kw in risk_keywords:
            if "risk" not in domains:
                domains.append("risk")
        elif kw in ["frontend", "vue", "component", "view", "page", "ui"]:
            if "frontend" not in domains and not has_risk:
                domains.append("frontend")
        elif kw in ["backend", "service", "model", "api", "database"]:
            if "backend" not in domains:
                domains.append("backend")
    
    if not domains:
        domains = ["backend", "frontend"]
    
    return domains


def determine_profile(
    task_text: str,
    keywords: List[str],
    explicit_profile: Optional[str],
    task_profiles: dict,
) -> Tuple[str, List[str]]:
    """Determine Lite/Normal/Strict profile."""
    reasons = []
    task_lower = task_text.lower()
    
    if explicit_profile:
        reasons.append(f"explicitly specified: {explicit_profile}")
        profile = explicit_profile
    else:
        profile = "Normal"
        reasons.append("default profile")
    
    strict_keywords = task_profiles.get("strict", {}).get("triggers", {}).get("risky_keywords", [])
    
    matched_risky = [kw for kw in keywords if kw in strict_keywords]
    if matched_risky:
        reasons.append(f"risky keywords: {', '.join(matched_risky)}")
        if profile != "Strict":
            profile = "Strict"
            reasons.append("upgraded to Strict due to risky keywords")
    
    forbidden = task_profiles.get("lite", {}).get("forbidden_domains", [])
    matched_forbidden = [kw for kw in keywords if kw in forbidden]
    if matched_forbidden:
        if profile == "Lite":
            profile = "Normal"
            reasons.append(f"upgraded from Lite: forbidden domain matched ({matched_forbidden[0]})")
        if profile in ("Lite", "Normal"):
            profile = "Strict"
            reasons.append(f"upgraded to Strict: high-risk domain ({matched_forbidden[0]})")
    
    critical_phrases = [
        "删除", "删除", "权限", "安全", "认证", "授权",
        "delete", "remove", "permission", "security", "auth",
        "transaction", "迁移", "migration", "cascade",
    ]
    if any(phrase in task_lower for phrase in critical_phrases):
        if profile != "Strict":
            profile = "Strict"
            reasons.append("upgraded to Strict: critical operation detected")
    
    return profile, reasons


def determine_routing(
    profile: str,
    task_type: Dict[str, bool],
    domains: List[str],
    task_stage_routing: dict,
) -> Dict[str, str]:
    """Determine routing agents."""
    pipeline = task_stage_routing.get("pipeline", {})
    
    routing = {
        "intake_agent": pipeline.get("intake", "task-intake"),
        "classifier_agent": pipeline.get("classifier", "risk-classifier"),
    }
    
    if profile in ("Lite", "Normal"):
        routing["planner_agent"] = pipeline.get("planner", {}).get("lite", "planner-lite")
    else:
        routing["planner_agent"] = pipeline.get("planner", {}).get("strict", "planner-strict")
    
    routing["implementer_agent"] = pipeline.get("executor", "implementer")
    
    return routing


def get_affected_area_hints(task_text: str, keywords: List[str], repo_paths: dict) -> List[str]:
    """Get affected area hints based on task keywords."""
    hints = []
    task_lower = task_text.lower()
    
    canonical = repo_paths.get("canonical_paths", {})
    
    backend_keywords = ["backend", "api", "service", "model", "schema", "auth", "permission"]
    frontend_keywords = ["frontend", "vue", "component", "view", "ui", "form"]
    
    for kw in keywords:
        if kw in backend_keywords:
            if "backend_app" in canonical:
                hints.append(f"backend: {canonical['backend_app']}")
            if "backend_api" in canonical:
                hints.append(f"api: {canonical['backend_api']}")
        if kw in frontend_keywords:
            if "frontend_src" in canonical:
                hints.append(f"frontend: {canonical['frontend_src']}")
            if "frontend_components" in canonical:
                hints.append(f"components: {canonical['frontend_components']}")
    
    if not hints:
        hints = ["backend/app/", "my-app/src/"]
    
    return hints[:5]


def generate_task_context(
    task_id: str,
    user_request: str,
    profile: str,
    profile_reasons: List[str],
    task_type: Dict[str, bool],
    predicted_domains: List[str],
    routing: Dict[str, str],
    affected_area_hints: List[str],
    keywords: List[str],
) -> dict:
    """Generate task_context.json content."""
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "schema_version": "1.0",
        "tool_mode": "task",
        "task_id": task_id,
        "generated_at": now,
        "user_request": user_request,
        "profile": profile,
        "initial_classification": {
            "profile": profile,
            "reasons": profile_reasons,
        },
        "task_type": task_type,
        "predicted_domains": predicted_domains,
        "routing": routing,
        "affected_area_hints": affected_area_hints,
        "detected_keywords": keywords,
        "required_runtime_refs": [
            "AGENTS.md",
            "standards/00_ai_digest.md",
            ".runtime/task_capsule.md",
        ],
        "allowed_capabilities": [
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


def generate_task_capsule(context: dict) -> str:
    """Generate task_capsule.md content."""
    lines = []
    lines.append("# Task Runtime Capsule")
    lines.append("")
    
    lines.append("## Task")
    lines.append(f"- ID: {context['task_id']}")
    lines.append(f"- Request: {context['user_request']}")
    lines.append(f"- Generated: {context['generated_at']}")
    lines.append("")
    
    lines.append("## Classification")
    lines.append(f"- Profile: **{context['profile']}**")
    for reason in context.get("initial_classification", {}).get("reasons", []):
        lines.append(f"- Reason: {reason}")
    lines.append("")
    
    task_type = context.get("task_type", {})
    lines.append("## Task Type")
    lines.append(f"- Backend: {'Yes' if task_type.get('backend') else 'No'}")
    lines.append(f"- Frontend: {'Yes' if task_type.get('frontend') else 'No'}")
    lines.append(f"- Fullstack: {'Yes' if task_type.get('fullstack') else 'No'}")
    lines.append("")
    
    domains = context.get("predicted_domains", [])
    lines.append("## Predicted Domains")
    if domains:
        for domain in domains:
            lines.append(f"- {domain}")
    else:
        lines.append("- (none)")
    lines.append("")
    
    routing = context.get("routing", {})
    lines.append("## Routing")
    lines.append(f"- Intake: {routing.get('intake_agent', 'N/A')}")
    lines.append(f"- Classifier: {routing.get('classifier_agent', 'N/A')}")
    lines.append(f"- Planner: {routing.get('planner_agent', 'N/A')}")
    lines.append(f"- Implementer: {routing.get('implementer_agent', 'N/A')}")
    lines.append("")
    
    hints = context.get("affected_area_hints", [])
    lines.append("## Affected Area Hints")
    if hints:
        for hint in hints:
            lines.append(f"- {hint}")
    else:
        lines.append("- (none)")
    lines.append("")
    
    keywords = context.get("detected_keywords", [])
    lines.append("## Detected Keywords")
    if keywords:
        lines.append(f"- {', '.join(keywords)}")
    else:
        lines.append("- (none)")
    lines.append("")
    
    lines.append("## Required References")
    refs = context.get("required_runtime_refs", [])
    for ref in refs:
        lines.append(f"- {ref}")
    lines.append("")
    
    lines.append("## Allowed Capabilities")
    caps = context.get("allowed_capabilities", [])
    for cap in caps:
        lines.append(f"- {cap}")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Prepare task runtime context")
    parser.add_argument("--task", type=str, required=True, help="User task description")
    parser.add_argument("--lite", action="store_true", help="Force Lite profile")
    parser.add_argument("--normal", action="store_true", help="Force Normal profile")
    parser.add_argument("--strict", action="store_true", help="Force Strict profile")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()
    
    explicit_profile = None
    if args.strict:
        explicit_profile = "Strict"
    elif args.normal:
        explicit_profile = "Normal"
    elif args.lite:
        explicit_profile = "Lite"
    
    task_profiles = load_yaml(TASK_PROFILES_FILE)
    risk_keywords = load_yaml(RISK_KEYWORDS_FILE)
    task_stage_routing = load_yaml(TASK_STAGE_ROUTING_FILE)
    repo_paths = load_yaml(REPO_PATHS_FILE)
    
    keywords = detect_task_keywords(args.task)
    task_type = detect_task_type(args.task, keywords)
    predicted_domains = predict_domains(args.task, keywords, task_profiles)
    profile, profile_reasons = determine_profile(
        args.task, keywords, explicit_profile, task_profiles
    )
    routing = determine_routing(profile, task_type, predicted_domains, task_stage_routing)
    affected_area_hints = get_affected_area_hints(args.task, keywords, repo_paths)
    
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    context = generate_task_context(
        task_id=task_id,
        user_request=args.task,
        profile=profile,
        profile_reasons=profile_reasons,
        task_type=task_type,
        predicted_domains=predicted_domains,
        routing=routing,
        affected_area_hints=affected_area_hints,
        keywords=keywords,
    )
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    context_path = output_dir / "task_context.json"
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
    print(f"Context written to: {context_path}")
    
    capsule_content = generate_task_capsule(context)
    capsule_path = output_dir / "task_capsule.md"
    with open(capsule_path, "w", encoding="utf-8") as f:
        f.write(capsule_content)
    print(f"Capsule written to: {capsule_path}")
    
    print(f"\nProfile: {profile}")
    print(f"Task Type: backend={task_type['backend']}, frontend={task_type['frontend']}, fullstack={task_type['fullstack']}")
    print(f"Predicted domains: {', '.join(predicted_domains) if predicted_domains else 'none'}")
    print(f"Routing: intake={routing['intake_agent']}, classifier={routing['classifier_agent']}, planner={routing['planner_agent']}, implementer={routing['implementer_agent']}")


if __name__ == "__main__":
    sys.exit(main())
