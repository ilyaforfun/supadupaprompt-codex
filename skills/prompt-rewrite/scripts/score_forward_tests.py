#!/usr/bin/env python3
"""Create and score manual forward-test result files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plan_forward_tests import agent_prompt, case_paths, load_cases


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def selected_cases(args: argparse.Namespace) -> list[dict[str, Any]]:
    cases = load_cases(case_paths(args))
    return cases[: args.limit] if args.limit else cases


def result_template(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": utc_now(),
        "mode": "manual-forward-test-results",
        "instructions": (
            "Run each agent_prompt in a fresh Codex thread or subagent. Paste only the final answer "
            "into agent_output, then score each expected behavior as 0, 1, or 2 and each red flag as "
            "true or false. Do not commit private outputs."
        ),
        "score_guide": {
            "expected_behavior": {
                "2": "present and specific",
                "1": "partially present or too generic",
                "0": "missing, contradicted, or unsafe",
            },
            "red_flags": "true means the red flag is present in the agent output.",
        },
        "cases": [
            {
                "name": case["name"],
                "target_skill": case["target_skill"],
                "prompt_type": case["prompt_type"],
                "source": case["_path"],
                "agent_prompt": agent_prompt(case),
                "agent_output": "",
                "scores": {
                    "expected_behavior": [
                        {"item": item, "score": None, "evidence": ""} for item in case["expected_behavior"]
                    ],
                    "red_flags": [
                        {"item": item, "present": None, "evidence": ""} for item in case["red_flags"]
                    ],
                },
                "reviewer_notes": "",
            }
            for case in cases
        ],
    }


def write_template(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result_template(cases), indent=2, ensure_ascii=False) + "\n")


def read_results(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"{path}: could not read file: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise SystemExit(f"{path}: expected a cases list")
    return data


def by_item(entries: Any, field: str) -> dict[str, Any]:
    if not isinstance(entries, list):
        return {}
    out: dict[str, Any] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("item"), str):
            out[entry["item"]] = entry.get(field)
    return out


def score_case(case: dict[str, Any], result: dict[str, Any] | None, min_average_score: float) -> dict[str, Any]:
    issues: list[str] = []
    if result is None:
        return {
            "name": case["name"],
            "target_skill": case["target_skill"],
            "prompt_type": case["prompt_type"],
            "status": "incomplete",
            "average_score": 0.0,
            "expected_points": 0,
            "expected_max_points": len(case["expected_behavior"]) * 2,
            "red_flags_present": 0,
            "issues": ["missing result entry"],
        }

    output = result.get("agent_output")
    if not isinstance(output, str) or not output.strip():
        issues.append("missing agent_output")

    scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    expected_scores = by_item(scores.get("expected_behavior"), "score")
    red_flag_scores = by_item(scores.get("red_flags"), "present")

    expected_points = 0
    expected_max = len(case["expected_behavior"]) * 2
    zero_scores = 0
    for item in case["expected_behavior"]:
        value = expected_scores.get(item)
        if value is None:
            issues.append(f"unscored expected behavior: {item}")
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value not in {0, 1, 2}:
            issues.append(f"invalid expected score for: {item}")
            continue
        expected_points += value
        if value == 0:
            zero_scores += 1

    red_flags_present = 0
    for item in case["red_flags"]:
        value = red_flag_scores.get(item)
        if value is None:
            issues.append(f"unscored red flag: {item}")
            continue
        if not isinstance(value, bool):
            issues.append(f"invalid red flag score for: {item}")
            continue
        if value:
            red_flags_present += 1

    average_score = expected_points / len(case["expected_behavior"]) if case["expected_behavior"] else 0.0
    incomplete = bool(issues)
    passed = (
        not incomplete
        and zero_scores == 0
        and red_flags_present == 0
        and average_score >= min_average_score
    )
    status = "pass" if passed else "incomplete" if incomplete else "fail"
    if not incomplete:
        if zero_scores:
            issues.append("one or more expected behaviors scored 0")
        if red_flags_present:
            issues.append("one or more red flags present")
        if average_score < min_average_score:
            issues.append(f"average score below {min_average_score:g}")

    return {
        "name": case["name"],
        "target_skill": case["target_skill"],
        "prompt_type": case["prompt_type"],
        "status": status,
        "average_score": round(average_score, 2),
        "expected_points": expected_points,
        "expected_max_points": expected_max,
        "red_flags_present": red_flags_present,
        "issues": issues,
    }


def score_results(
    cases: list[dict[str, Any]],
    results: dict[str, Any],
    results_path: Path,
    min_average_score: float,
) -> dict[str, Any]:
    result_lookup: dict[str, dict[str, Any]] = {}
    duplicate_names: set[str] = set()
    for entry in results["cases"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            continue
        name = entry["name"]
        if name in result_lookup:
            duplicate_names.add(name)
        result_lookup[name] = entry

    case_results = [score_case(case, result_lookup.get(case["name"]), min_average_score) for case in cases]
    status_counts = {
        "pass": sum(1 for case in case_results if case["status"] == "pass"),
        "fail": sum(1 for case in case_results if case["status"] == "fail"),
        "incomplete": sum(1 for case in case_results if case["status"] == "incomplete"),
    }
    errors = [f"duplicate result name: {name}" for name in sorted(duplicate_names)]
    overall_status = "pass"
    if errors or status_counts["fail"]:
        overall_status = "fail"
    if status_counts["incomplete"]:
        overall_status = "incomplete"

    return {
        "generated_at": utc_now(),
        "results_file": str(results_path),
        "case_count": len(case_results),
        "complete_count": status_counts["pass"] + status_counts["fail"],
        "passed_count": status_counts["pass"],
        "failed_count": status_counts["fail"],
        "incomplete_count": status_counts["incomplete"],
        "overall_status": overall_status,
        "min_average_score": min_average_score,
        "errors": errors,
        "cases": case_results,
    }


def print_markdown(summary: dict[str, Any]) -> None:
    def issue_summary(issues: list[str]) -> str:
        if len(issues) <= 2:
            return "; ".join(issues)
        return f"{'; '.join(issues[:2])}; +{len(issues) - 2} more"

    print("# Forward Test Score")
    print()
    print(f"- Generated: {summary['generated_at']}")
    print(f"- Results file: `{summary['results_file']}`")
    print(f"- Overall status: {summary['overall_status']}")
    print(f"- Cases: {summary['case_count']}")
    print(f"- Complete: {summary['complete_count']}")
    print(f"- Passed: {summary['passed_count']}")
    print(f"- Failed: {summary['failed_count']}")
    print(f"- Incomplete: {summary['incomplete_count']}")
    print()
    print("| Case | Status | Avg score | Points | Red flags | Issues |")
    print("| --- | --- | ---: | ---: | ---: | --- |")
    for case in summary["cases"]:
        issues = issue_summary(case["issues"]) if case["issues"] else ""
        print(
            f"| `{case['name']}` | {case['status']} | {case['average_score']} | "
            f"{case['expected_points']}/{case['expected_max_points']} | "
            f"{case['red_flags_present']} | {issues} |"
        )
    if summary["errors"]:
        print()
        print("Errors:")
        for error in summary["errors"]:
            print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", nargs="*", help="Specific forward-test JSON files. Defaults to all cases.")
    parser.add_argument("--limit", type=int, help="Maximum cases to include")
    parser.add_argument("--init-results", type=Path, help="Write a forward-test results template")
    parser.add_argument("--results", type=Path, help="Score a completed forward-test results file")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--min-average-score", type=float, default=1.5)
    args = parser.parse_args()

    if bool(args.init_results) == bool(args.results):
        raise SystemExit("Choose exactly one of --init-results or --results")

    cases = selected_cases(args)
    if args.init_results:
        write_template(args.init_results, cases)
        print(f"Wrote forward-test results template: {args.init_results}")
        return 0

    summary = score_results(cases, read_results(args.results), args.results, args.min_average_score)
    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_markdown(summary)
    return 0 if summary["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
