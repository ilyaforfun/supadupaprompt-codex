#!/usr/bin/env python3
"""Plan manual forward tests for supadupaprompt skills."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent
FORWARD_TEST_DIR = SKILL_DIR / "forward_tests"
TARGET_SKILLS = {
    "prompt-rewrite": SKILLS_ROOT / "prompt-rewrite",
    "prompt-profile-review": SKILLS_ROOT / "prompt-profile-review",
}
REQUIRED_KEYS = {
    "name",
    "target_skill",
    "prompt_type",
    "description",
    "user_request",
    "expected_behavior",
    "red_flags",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"{path}: could not read file: {exc}") from exc


def case_paths(args: argparse.Namespace) -> list[Path]:
    if args.cases:
        return [Path(item) for item in args.cases]
    return sorted(FORWARD_TEST_DIR.glob("*.json"))


def validate_case(case: dict[str, Any], path: Path) -> list[str]:
    failures: list[str] = []
    missing = REQUIRED_KEYS - set(case)
    if missing:
        failures.append(f"{path}: missing keys: {', '.join(sorted(missing))}")
        return failures
    for key in ("name", "target_skill", "prompt_type", "description", "user_request"):
        if not isinstance(case[key], str) or not case[key].strip():
            failures.append(f"{path}: {key} must be non-empty text")
    if case.get("target_skill") not in TARGET_SKILLS:
        failures.append(f"{path}: target_skill must be one of {', '.join(sorted(TARGET_SKILLS))}")
    for key in ("expected_behavior", "red_flags"):
        if not isinstance(case[key], list) or not case[key]:
            failures.append(f"{path}: {key} must be a non-empty list")
        elif not all(isinstance(item, str) and item.strip() for item in case[key]):
            failures.append(f"{path}: {key} must contain non-empty text items")
    context = case.get("context", [])
    if context and (not isinstance(context, list) or not all(isinstance(item, str) for item in context)):
        failures.append(f"{path}: context must be a list of text items")
    return failures


def load_cases(paths: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    failures: list[str] = []
    seen_names: set[str] = set()
    for path in paths:
        case = read_json(path)
        path_failures = validate_case(case, path)
        if path_failures:
            failures.extend(path_failures)
            continue
        if case["name"] in seen_names:
            failures.append(f"{path}: duplicate case name {case['name']!r}")
        seen_names.add(case["name"])
        case["_path"] = str(path)
        cases.append(case)
    if failures:
        for failure in failures:
            print(f"error: {failure}")
        raise SystemExit(1)
    return cases


def agent_prompt(case: dict[str, Any]) -> str:
    target = case["target_skill"]
    skill_path = TARGET_SKILLS[target]
    lines = [
        f"Use ${target} at {skill_path} to handle this user request.",
        "",
        "Treat this as a real user task. Do not inspect the forward_tests directory, expected behavior, rubrics, or prior test output. Use only the skill, the request, and any context below.",
        "",
        "User request:",
        case["user_request"],
    ]
    context = case.get("context", [])
    if context:
        lines.extend(["", "Context:"])
        lines.extend(f"- {item}" for item in context)
    lines.extend(
        [
            "",
            "Return the final answer you would give the user. Do not mention that this is a test.",
        ]
    )
    return "\n".join(lines)


def review_rubric(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "expected_behavior": case["expected_behavior"],
        "red_flags": case["red_flags"],
        "score_guide": [
            "2 = behavior is present and specific",
            "1 = partially present or too generic",
            "0 = missing, contradicted, or unsafe",
        ],
    }


def planned_cases(cases: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    selected = cases[:limit] if limit else cases
    out: list[dict[str, Any]] = []
    for case in selected:
        out.append(
            {
                "name": case["name"],
                "prompt_type": case["prompt_type"],
                "target_skill": case["target_skill"],
                "description": case["description"],
                "source": case["_path"],
                "agent_prompt": agent_prompt(case),
                "review_rubric": review_rubric(case),
            }
        )
    return out


def print_markdown(plan: dict[str, Any]) -> None:
    print("# Forward Test Plan")
    print()
    print(f"- Generated: {plan['generated_at']}")
    print(f"- Cases: {plan['case_count']}")
    print("- Mode: manual subagent forward tests; expected behavior is separated from agent prompts.")
    print()
    for case in plan["cases"]:
        print(f"## {case['name']}")
        print()
        print(f"- Type: {case['prompt_type']}")
        print(f"- Target skill: `${case['target_skill']}`")
        print(f"- Source: `{case['source']}`")
        print()
        print("### Agent Prompt")
        print()
        print("```text")
        print(case["agent_prompt"])
        print("```")
        print()
        print("### Review Rubric")
        print()
        print("Expected behavior:")
        for item in case["review_rubric"]["expected_behavior"]:
            print(f"- {item}")
        print()
        print("Red flags:")
        for item in case["review_rubric"]["red_flags"]:
            print(f"- {item}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", nargs="*", help="Specific forward-test JSON files. Defaults to all cases.")
    parser.add_argument("--limit", type=int, help="Maximum cases to include")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    cases = load_cases(case_paths(args))
    plan = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "case_count": len(cases[: args.limit] if args.limit else cases),
        "cases": planned_cases(cases, args.limit),
    }
    if args.format == "json":
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print_markdown(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
