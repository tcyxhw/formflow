#!/usr/bin/env python3
"""
Run checkpoint/release gates based on context.

Executes machine-readable gates (ruff, mypy, npm type-check) based on
triggered domains and profile, outputs structured results to:
- .runtime/gate_results.json (for checkpoint)
- .runtime/release_gate_results.json (for release-check)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
RUNTIME_DIR = REPO_ROOT / ".runtime"
CONTEXT_FILE = RUNTIME_DIR / "checkpoint_context.json"
RELEASE_CONTEXT_FILE = RUNTIME_DIR / "release_check_context.json"
OUTPUT_FILE = RUNTIME_DIR / "gate_results.json"
RELEASE_OUTPUT_FILE = RUNTIME_DIR / "release_gate_results.json"


def load_context(mode: str = "checkpoint") -> Optional[Dict[str, Any]]:
    """Load checkpoint or release-check context."""
    context_file = RELEASE_CONTEXT_FILE if mode == "release-check" else CONTEXT_FILE
    if not context_file.exists():
        print(f"Warning: {context_file} not found", file=sys.stderr)
        return None
    with open(context_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(results: Dict[str, Any], mode: str = "checkpoint") -> None:
    """Save gate results to JSON."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RELEASE_OUTPUT_FILE if mode == "release-check" else OUTPUT_FILE
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Gate results written to: {output_file}")


def run_command(
    cmd: List[str],
    cwd: Path = REPO_ROOT,
    timeout: int = 120
) -> Dict[str, Any]:
    """Run a command and return structured result."""
    result = {
        "command": " ".join(cmd),
        "cwd": str(cwd),
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "error": None,
    }
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout[:5000] if proc.stdout else ""
        result["stderr"] = proc.stderr[:5000] if proc.stderr else ""
    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout}s"
    except FileNotFoundError:
        result["error"] = f"Command not found: {cmd[0]}"
    except Exception as e:
        result["error"] = str(e)
    return result


def run_ruff(cwd: Path = REPO_ROOT) -> Dict[str, Any]:
    """Run ruff linter."""
    return run_command(["ruff", "check", "."], cwd=cwd)


def run_mypy(cwd: Path = REPO_ROOT) -> Dict[str, Any]:
    """Run mypy type checker on backend."""
    backend_path = cwd / "backend"
    if not backend_path.exists():
        return {"command": "mypy backend", "error": "backend/ not found", "skipped": True}
    return run_command(["mypy", "backend/app", "--ignore-missing-imports"], cwd=cwd, timeout=180)


def run_npm_typecheck(cwd: Path = REPO_ROOT) -> Dict[str, Any]:
    """Run npm type-check for frontend."""
    frontend_path = cwd / "my-app"
    if not frontend_path.exists():
        return {"command": "npm type-check", "error": "my-app/ not found", "skipped": True}
    
    # Try different type-check commands
    for cmd in [
        ["npm", "run", "type-check"],
        ["npx", "vue-tsc", "--noEmit"],
        ["npx", "tsc", "--noEmit"],
    ]:
        result = run_command(cmd, cwd=frontend_path, timeout=180)
        if result.get("error") and "not found" in result["error"].lower():
            continue
        return result
    
    return {"command": "npm type-check", "error": "No type-check command available", "skipped": True}


def run_backend_gates(profile: str) -> List[Dict[str, Any]]:
    """Run backend-specific gates."""
    results = []
    
    # Ruff is always run for backend
    ruff_result = run_ruff()
    ruff_result["gate"] = "ruff"
    results.append(ruff_result)
    
    # MyPy only for Normal/Strict
    if profile in ("Normal", "Strict"):
        mypy_result = run_mypy()
        mypy_result["gate"] = "mypy"
        results.append(mypy_result)
    
    return results


def run_frontend_gates(profile: str) -> List[Dict[str, Any]]:
    """Run frontend-specific gates."""
    results = []
    
    npm_result = run_npm_typecheck()
    npm_result["gate"] = "npm-type-check"
    results.append(npm_result)
    
    return results


def determine_gates_to_run(
    triggered_domains: List[str],
    profile: str
) -> List[str]:
    """Determine which gates to run based on domains and profile."""
    gates = []
    
    if "backend" in triggered_domains:
        gates.append("backend")
    
    if "frontend" in triggered_domains:
        gates.append("frontend")
    
    # For contract/risk, always run backend gates at minimum
    if not gates and triggered_domains:
        gates.append("backend")
    
    # Lite only runs basic gates
    if profile == "Lite":
        gates = [g for g in gates if g == "backend"]
    
    return gates


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run checkpoint/release gates")
    parser.add_argument("--mode", type=str, choices=["checkpoint", "release-check"],
                        default="checkpoint", help="Gate mode")
    args = parser.parse_args()

    mode = args.mode
    is_release = mode == "release-check"

    print("=" * 60)
    print(f"Running {mode} gates...")
    print("=" * 60)
    
    # Load context
    context = load_context(mode)
    if context is None:
        ctx_file = RELEASE_CONTEXT_FILE if is_release else CONTEXT_FILE
        results = {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "profile": "Unknown",
            "triggered_domains": [],
            "ran": [],
            "passed": [],
            "failed": [],
            "skipped": [],
            "details": [],
            "error": f"No {ctx_file.name} found",
        }
        save_results(results, mode)
        return 1
    
    profile = context.get("profile", "Normal")
    triggered_domains = context.get("triggered_domains", [])
    
    print(f"Profile: {profile}")
    print(f"Triggered domains: {triggered_domains}")
    
    # Determine gates
    gates_to_run = determine_gates_to_run(triggered_domains, profile)
    print(f"Gates to run: {gates_to_run}")
    
    # Run gates
    all_details = []
    passed = []
    failed = []
    skipped = []
    
    for gate_type in gates_to_run:
        print(f"\nRunning {gate_type} gates...")
        
        if gate_type == "backend":
            gate_results = run_backend_gates(profile)
        elif gate_type == "frontend":
            gate_results = run_frontend_gates(profile)
        else:
            continue
        
        for gr in gate_results:
            gate_name = gr.pop("gate", "unknown")
            all_details.append({**gr, "gate": gate_name})
            
            # Check if explicitly marked as skipped
            if gr.get("skipped"):
                skipped.append(gate_name)
            # Check if tool not found - mark as skipped
            elif gr.get("error") and "not found" in gr.get("error", "").lower():
                skipped.append(gate_name)
            elif gr.get("returncode", 1) == 0:
                passed.append(gate_name)
            else:
                failed.append(gate_name)
    
    # Build results
    results = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "profile": profile,
        "triggered_domains": triggered_domains,
        "ran": passed + failed + skipped,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "details": all_details,
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Gate Results Summary:")
    print(f"  Passed: {len(passed)} - {passed}")
    print(f"  Failed: {len(failed)} - {failed}")
    print(f"  Skipped: {len(skipped)} - {skipped}")
    print("=" * 60)
    
    save_results(results, mode)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
