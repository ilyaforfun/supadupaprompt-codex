#!/usr/bin/env python3
"""Generate a compact supadupaprompt dogfood report."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent
REPO_CANDIDATE = SKILLS_ROOT.parent
IS_REPO_LAYOUT = (
    (REPO_CANDIDATE / "README.md").exists()
    and (REPO_CANDIDATE / "scripts" / "install.py").exists()
    and (REPO_CANDIDATE / "skills" / "prompt-rewrite" / "SKILL.md").exists()
)
REPO_ROOT = REPO_CANDIDATE if IS_REPO_LAYOUT else SKILLS_ROOT
FIXTURE_DIR = SKILL_DIR / "fixtures"
CHECKER = SCRIPT_DIR / "check_dogfood_fixtures.py"
REWRITE_ESTIMATOR = SCRIPT_DIR / "estimate_rewrite_tokens.py"
PROFILE_REVIEW_DIR = SKILLS_ROOT / "prompt-profile-review"
REVIEW_ESTIMATOR = PROFILE_REVIEW_DIR / "scripts" / "estimate_review_tokens.py"
PROFILE_PLANNER = PROFILE_REVIEW_DIR / "scripts" / "plan_review_evidence.py"
FORWARD_TEST_PLANNER = SCRIPT_DIR / "plan_forward_tests.py"
FORWARD_TEST_SCORER = SCRIPT_DIR / "score_forward_tests.py"
SKILL_SCANNER = SCRIPT_DIR / "list_installed_skills.py"

DEFAULT_SCAN_INTENTS = "browser-qa,qa-report,design-review,publish-pr,code-review,research,automation,profile-review"
DEFAULT_SCAN_QUERY = (
    "supadupaprompt,prompt-rewrite,prompt-profile-review,dogfood,pr,review,github,browser,qa,"
    "design,research,notion,gmail,google-drive,openai-developers,automation"
)
DEFAULT_REVIEW_GOAL = "review how the user prompts for PR/dogfood work without scanning everything"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False)


def run_json(cmd: list[str]) -> dict[str, Any]:
    result = run(cmd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def one_line(cmd: list[str], fallback: str = "unknown") -> str:
    result = run(cmd)
    if result.returncode != 0:
        return fallback
    return result.stdout.strip() or fallback


def optional_output(cmd: list[str]) -> str:
    result = run(cmd)
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def git_status() -> str | None:
    result = run(["git", "status", "--short"])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def command_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def issue_summary(issues: list[str]) -> str:
    if len(issues) <= 2:
        return "; ".join(issues)
    return f"{'; '.join(issues[:2])}; +{len(issues) - 2} more"


def github_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    return env


def fixture_prompt_type(path: Path) -> str:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return "unknown"
    prompt_type = data.get("prompt_type")
    return prompt_type if isinstance(prompt_type, str) and prompt_type else "unknown"


def estimate_fixture(path: Path) -> int:
    data = run_json(["python3", str(REWRITE_ESTIMATOR), "--fixture", str(path), "--format", "json"])
    return int(data["estimated_total_tokens"])


def estimate_review(path: Path) -> dict[str, Any]:
    return run_json(["python3", str(REVIEW_ESTIMATOR), "--evidence-file", str(path), "--format", "json"])


def plan_review_evidence(path: Path, goal: str, budget: int) -> dict[str, Any]:
    return run_json(
        [
            "python3",
            str(PROFILE_PLANNER),
            str(path),
            "--goal",
            goal,
            "--budget",
            str(budget),
            "--format",
            "json",
        ]
    )


def plan_forward_tests(limit: int) -> dict[str, Any]:
    return run_json(["python3", str(FORWARD_TEST_PLANNER), "--limit", str(limit), "--format", "json"])


def score_forward_tests(results_path: Path, limit: int) -> dict[str, Any]:
    result = run(
        [
            "python3",
            str(FORWARD_TEST_SCORER),
            "--results",
            str(results_path),
            "--limit",
            str(limit),
            "--format",
            "json",
        ]
    )
    if result.stdout.strip():
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
        else:
            data["command_returncode"] = result.returncode
            return data
    return {
        "results_file": str(results_path),
        "overall_status": "error",
        "case_count": 0,
        "complete_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "incomplete_count": 0,
        "cases": [],
        "error": result.stderr.strip() or result.stdout.strip() or "forward-test scorer failed",
    }


def pr_snapshot(pr_number: str) -> dict[str, Any] | None:
    result = run(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--json",
            "url,number,state,isDraft,mergeable,mergeStateStatus,headRefName,baseRefName,changedFiles,additions,deletions,statusCheckRollup",
        ],
        env=github_env(),
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip() or result.stdout.strip()}
    return json.loads(result.stdout)


def scan_skills(limit: int) -> list[str]:
    result = run(
        [
            "python3",
            str(SKILL_SCANNER),
            "--roots",
            str(SKILLS_ROOT),
            "~/.codex/skills",
            "~/.agents/skills",
            ".codex/skills",
            ".agents/skills",
            "skills",
            "--include-plugin-cache",
            "--no-cache",
            "--intent",
            DEFAULT_SCAN_INTENTS,
            "--query",
            DEFAULT_SCAN_QUERY,
            "--limit",
            str(limit),
        ]
    )
    if result.returncode != 0:
        return [f"skill scan failed: {result.stderr.strip() or result.stdout.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def recommendation(
    check_passed: bool,
    pr: dict[str, Any] | None,
    review_tokens: int | None,
    narrow_plan: dict[str, Any] | None,
    forward_plan: dict[str, Any] | None,
    forward_score: dict[str, Any] | None,
) -> str:
    if not check_passed:
        return "Fix fixture regressions before adding behavior."
    if pr and pr.get("error"):
        return "Resolve PR lookup/auth before trusting the loop boundary."
    if pr and pr.get("state") not in {None, "MERGED", "CLOSED"}:
        return "Finish the current PR state before starting a new feature lap."
    if forward_score:
        if forward_score.get("overall_status") == "incomplete":
            return "Finish the forward-test results file before adding another feature."
        if forward_score.get("overall_status") == "fail":
            failed = [
                case["name"]
                for case in forward_score.get("cases", [])
                if case.get("status") == "fail"
            ]
            if failed:
                return f"Fix forward-test failures before the next feature: {', '.join(failed)}."
            return "Fix forward-test scoring errors before the next feature."
        if forward_score.get("overall_status") == "error":
            return "Fix the forward-test results file or scorer invocation before adding another feature."
        if forward_score.get("overall_status") == "pass":
            return "Forward tests pass; pick the next user-facing improvement and keep it to one PR."
    if review_tokens and narrow_plan:
        narrow_tokens = int(narrow_plan["estimated_review_total_tokens"])
        if review_tokens > narrow_tokens:
            if forward_plan and forward_plan.get("case_count"):
                return "Run the manual forward-test plan, record results with score_forward_tests.py, then add the next feature."
            return "Use the narrow profile-review prompt shown above; broaden only if the selected evidence is thin."
    if review_tokens and review_tokens > 8000:
        return "Run the evidence planner before broad profile-review scans."
    return "Pick one small missing behavior from the latest dogfood prompt and cover it with a fixture before implementation."


def print_report(args: argparse.Namespace) -> int:
    branch = one_line(["git", "branch", "--show-current"])
    status = git_status()
    latest_commit = one_line(["git", "log", "-1", "--oneline"])

    checker_result = run(["python3", str(CHECKER)])
    check_passed = checker_result.returncode == 0

    fixture_rows: list[tuple[str, str, int]] = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture_rows.append((fixture_prompt_type(path), path.name, estimate_fixture(path)))

    review_data: dict[str, Any] | None = None
    narrow_plan: dict[str, Any] | None = None
    if args.evidence_file:
        review_data = estimate_review(args.evidence_file)
        narrow_plan = plan_review_evidence(args.evidence_file, args.evidence_goal, args.narrow_review_budget)

    pr = pr_snapshot(args.pr) if args.pr else None
    skill_lines = scan_skills(args.skill_scan_limit) if args.scan_skills else []
    forward_plan = plan_forward_tests(args.forward_test_limit)
    forward_score = score_forward_tests(args.forward_test_results, args.forward_test_limit) if args.forward_test_results else None
    review_tokens = int(review_data["estimated_total_tokens"]) if review_data else None

    print("# Dogfood Report")
    print()
    print(f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"- Repo: `{REPO_ROOT}`")
    print(f"- Branch: `{branch}`")
    print(f"- Latest commit: `{latest_commit}`")
    print(f"- Git status: {'unknown' if status is None else 'clean' if not status else 'dirty'}")
    if status:
        print()
        print("```text")
        print(status)
        print("```")

    if pr is not None:
        print()
        print("## PR")
        if pr.get("error"):
            print(f"- Error: {pr['error']}")
        else:
            print(f"- PR: [#{pr['number']}]({pr['url']})")
            print(f"- State: {pr['state']}")
            print(f"- Merge state: {pr.get('mergeStateStatus', 'unknown')} / {pr.get('mergeable', 'unknown')}")
            print(f"- Diff size: {pr.get('changedFiles', 0)} files, +{pr.get('additions', 0)} / -{pr.get('deletions', 0)}")

    print()
    print("## Fixture Suite")
    print(f"- Status: {'pass' if check_passed else 'fail'}")
    print(f"- Fixtures: {len(fixture_rows)}")
    print()
    print("| Prompt type | Fixture | Estimated rewrite tokens |")
    print("| --- | --- | ---: |")
    for prompt_type, file_name, tokens in fixture_rows:
        print(f"| {prompt_type} | `{file_name}` | {tokens} |")
    if fixture_rows:
        tokens = [row[2] for row in fixture_rows]
        print()
        print(f"- Rewrite token range: {min(tokens)}-{max(tokens)}")
        print(f"- Rewrite token average: {round(mean(tokens))}")
        print(f"- Rewrite token total across fixtures: {sum(tokens)}")

    if not check_passed:
        print()
        print("### Fixture Output")
        print("```text")
        print((checker_result.stdout + checker_result.stderr).strip())
        print("```")

    if review_data:
        print()
        print("## Profile Review Estimate")
        print(f"- Evidence file: `{args.evidence_file}`")
        print(f"- Broad estimated total tokens: {review_data['estimated_total_tokens']}")
        for component in review_data["components"]:
            print(f"- {component['component']}: {component['estimated_tokens']} tokens")
        if narrow_plan:
            print(f"- Narrow goal: {narrow_plan['goal']}")
            print(f"- Narrow budget: {narrow_plan['budget_tokens']}")
            print(f"- Narrow estimated total tokens: {narrow_plan['estimated_review_total_tokens']}")
            print(f"- Narrow selected snippets: {narrow_plan['selected_snippet_count']}")
            print(f"- Narrow selected evidence tokens: {narrow_plan['selected_evidence_tokens']}")
            print(f"- Narrow review command: {narrow_plan['commands']['review_command']}")

    if skill_lines:
        print()
        print("## Installed Skill Signal")
        for line in skill_lines[: args.skill_scan_limit]:
            print(line)

    if forward_plan:
        print()
        print("## Forward Tests")
        print(f"- Planned cases: {forward_plan['case_count']}")
        print(f"- Planner command: `python3 {command_path(FORWARD_TEST_PLANNER)} --limit {args.forward_test_limit}`")
        print(
            "- Results template command: "
            f"`python3 {command_path(FORWARD_TEST_SCORER)} --init-results /tmp/supaprompt-forward-results.json --limit {args.forward_test_limit}`"
        )
        for case in forward_plan["cases"]:
            print(f"- `{case['name']}` -> `${case['target_skill']}` ({case['prompt_type']})")
        if forward_score:
            print()
            print("### Forward Test Scores")
            print(f"- Results file: `{forward_score['results_file']}`")
            print(f"- Overall status: {forward_score['overall_status']}")
            print(f"- Complete: {forward_score['complete_count']}/{forward_score['case_count']}")
            print(f"- Passed: {forward_score['passed_count']}")
            print(f"- Failed: {forward_score['failed_count']}")
            print(f"- Incomplete: {forward_score['incomplete_count']}")
            if forward_score.get("error"):
                print(f"- Error: {forward_score['error']}")
            print()
            print("| Case | Status | Avg score | Points | Red flags | Issues |")
            print("| --- | --- | ---: | ---: | ---: | --- |")
            for case in forward_score["cases"]:
                issues = issue_summary(case["issues"]) if case["issues"] else ""
                print(
                    f"| `{case['name']}` | {case['status']} | {case['average_score']} | "
                    f"{case['expected_points']}/{case['expected_max_points']} | "
                    f"{case['red_flags_present']} | {issues} |"
                )

    print()
    print("## Next Loop Recommendation")
    print(f"- {recommendation(check_passed, pr, review_tokens, narrow_plan, forward_plan, forward_score)}")
    print("- Keep each lap to one coherent PR, then rerun this report from merged main.")
    forward_passed = forward_score is None or forward_score.get("overall_status") == "pass"
    return 0 if check_passed and forward_passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", help="Optional GitHub PR number to include in the report")
    parser.add_argument("--evidence-file", type=Path, help="Optional profile-review evidence file to estimate")
    parser.add_argument("--evidence-goal", default=DEFAULT_REVIEW_GOAL, help="Goal for narrow profile-review evidence planning")
    parser.add_argument("--narrow-review-budget", type=int, default=5000, help="Target total tokens for the narrow profile-review plan")
    parser.add_argument("--scan-skills", action="store_true", help="Include an installed-skill routing scan")
    parser.add_argument("--skill-scan-limit", type=int, default=12)
    parser.add_argument("--forward-test-limit", type=int, default=3, help="Number of manual forward tests to show")
    parser.add_argument("--forward-test-results", type=Path, help="Optional completed forward-test results JSON to score")
    return print_report(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
