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
REPO_ROOT = SCRIPT_DIR.parents[2]
FIXTURE_DIR = SKILL_DIR / "fixtures"
CHECKER = SCRIPT_DIR / "check_dogfood_fixtures.py"
REWRITE_ESTIMATOR = SCRIPT_DIR / "estimate_rewrite_tokens.py"
REVIEW_ESTIMATOR = REPO_ROOT / "skills" / "prompt-profile-review" / "scripts" / "estimate_review_tokens.py"
SKILL_SCANNER = SCRIPT_DIR / "list_installed_skills.py"

DEFAULT_SCAN_INTENTS = "browser-qa,qa-report,design-review,publish-pr,code-review,research,automation,profile-review"
DEFAULT_SCAN_QUERY = (
    "supadupaprompt,prompt-rewrite,prompt-profile-review,dogfood,pr,review,github,browser,qa,"
    "design,research,notion,gmail,google-drive,openai-developers,automation"
)


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


def recommendation(check_passed: bool, pr: dict[str, Any] | None, review_tokens: int | None) -> str:
    if not check_passed:
        return "Fix fixture regressions before adding behavior."
    if pr and pr.get("error"):
        return "Resolve PR lookup/auth before trusting the loop boundary."
    if pr and pr.get("state") not in {None, "MERGED", "CLOSED"}:
        return "Finish the current PR state before starting a new feature lap."
    if review_tokens and review_tokens > 8000:
        return "Optimize profile-review evidence narrowing before broad profile scans."
    return "Pick one small missing behavior from the latest dogfood prompt and cover it with a fixture before implementation."


def print_report(args: argparse.Namespace) -> int:
    branch = one_line(["git", "branch", "--show-current"])
    status = optional_output(["git", "status", "--short"])
    latest_commit = one_line(["git", "log", "-1", "--oneline"])

    checker_result = run(["python3", str(CHECKER)])
    check_passed = checker_result.returncode == 0

    fixture_rows: list[tuple[str, str, int]] = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture_rows.append((fixture_prompt_type(path), path.name, estimate_fixture(path)))

    review_data: dict[str, Any] | None = None
    if args.evidence_file:
        review_data = estimate_review(args.evidence_file)

    pr = pr_snapshot(args.pr) if args.pr else None
    skill_lines = scan_skills(args.skill_scan_limit) if args.scan_skills else []
    review_tokens = int(review_data["estimated_total_tokens"]) if review_data else None

    print("# Dogfood Report")
    print()
    print(f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"- Repo: `{REPO_ROOT}`")
    print(f"- Branch: `{branch}`")
    print(f"- Latest commit: `{latest_commit}`")
    print(f"- Git status: {'clean' if not status else 'dirty'}")
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
        print(f"- Estimated total tokens: {review_data['estimated_total_tokens']}")
        for component in review_data["components"]:
            print(f"- {component['component']}: {component['estimated_tokens']} tokens")

    if skill_lines:
        print()
        print("## Installed Skill Signal")
        for line in skill_lines[: args.skill_scan_limit]:
            print(line)

    print()
    print("## Next Loop Recommendation")
    print(f"- {recommendation(check_passed, pr, review_tokens)}")
    print("- Keep each lap to one coherent PR, then rerun this report from merged main.")
    return 0 if check_passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", help="Optional GitHub PR number to include in the report")
    parser.add_argument("--evidence-file", type=Path, help="Optional profile-review evidence file to estimate")
    parser.add_argument("--scan-skills", action="store_true", help="Include an installed-skill routing scan")
    parser.add_argument("--skill-scan-limit", type=int, default=12)
    return print_report(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
