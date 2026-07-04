#!/usr/bin/env python3
"""Run local health checks for supadupaprompt-codex."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROMPT_REWRITE_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = PROMPT_REWRITE_DIR.parent
REPO_CANDIDATE = SKILLS_ROOT.parent
IS_REPO_LAYOUT = (
    (REPO_CANDIDATE / "README.md").exists()
    and (REPO_CANDIDATE / "scripts" / "install.py").exists()
    and (REPO_CANDIDATE / "skills" / "prompt-rewrite" / "SKILL.md").exists()
)
REPO_ROOT = REPO_CANDIDATE if IS_REPO_LAYOUT else SKILLS_ROOT
PROFILE_REVIEW_DIR = SKILLS_ROOT / "prompt-profile-review"
SYSTEM_VALIDATOR = Path("~/.codex/skills/.system/skill-creator/scripts/quick_validate.py").expanduser()

REQUIRED_PROMPT_REWRITE_FILES = [
    PROMPT_REWRITE_DIR / "SKILL.md",
    PROMPT_REWRITE_DIR / "references" / "prompt-types.md",
    PROMPT_REWRITE_DIR / "references" / "quality-rubric.md",
    PROMPT_REWRITE_DIR / "references" / "skill-routing.md",
    PROMPT_REWRITE_DIR / "scripts" / "check_dogfood_fixtures.py",
    PROMPT_REWRITE_DIR / "scripts" / "dogfood_report.py",
    PROMPT_REWRITE_DIR / "scripts" / "estimate_rewrite_tokens.py",
    PROMPT_REWRITE_DIR / "scripts" / "list_installed_skills.py",
    PROMPT_REWRITE_DIR / "scripts" / "plan_forward_tests.py",
    PROMPT_REWRITE_DIR / "scripts" / "score_forward_tests.py",
    PROMPT_REWRITE_DIR / "scripts" / "supaprompt_doctor.py",
]

OPTIONAL_PACK_FILES = [
    PROFILE_REVIEW_DIR / "SKILL.md",
    PROFILE_REVIEW_DIR / "references" / "profile-schema.md",
    PROFILE_REVIEW_DIR / "references" / "source-guide.md",
    PROFILE_REVIEW_DIR / "scripts" / "collect_user_prompts.py",
    PROFILE_REVIEW_DIR / "scripts" / "estimate_review_tokens.py",
    PROFILE_REVIEW_DIR / "scripts" / "plan_review_evidence.py",
]
if IS_REPO_LAYOUT:
    OPTIONAL_PACK_FILES = [REPO_ROOT / "README.md", REPO_ROOT / "scripts" / "install.py", *OPTIONAL_PACK_FILES]

SCRIPT_FILES = [
    PROMPT_REWRITE_DIR / "scripts" / "check_dogfood_fixtures.py",
    PROMPT_REWRITE_DIR / "scripts" / "dogfood_report.py",
    PROMPT_REWRITE_DIR / "scripts" / "estimate_rewrite_tokens.py",
    PROMPT_REWRITE_DIR / "scripts" / "list_installed_skills.py",
    PROMPT_REWRITE_DIR / "scripts" / "plan_forward_tests.py",
    PROMPT_REWRITE_DIR / "scripts" / "score_forward_tests.py",
    PROMPT_REWRITE_DIR / "scripts" / "supaprompt_doctor.py",
    PROFILE_REVIEW_DIR / "scripts" / "collect_user_prompts.py",
    PROFILE_REVIEW_DIR / "scripts" / "estimate_review_tokens.py",
    PROFILE_REVIEW_DIR / "scripts" / "plan_review_evidence.py",
]
if IS_REPO_LAYOUT:
    SCRIPT_FILES = [REPO_ROOT / "scripts" / "install.py", *SCRIPT_FILES]


@dataclass
class CheckResult:
    name: str
    status: str
    summary: str
    details: list[str]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def display_path(path: Path) -> str:
    for root in (REPO_ROOT, SKILLS_ROOT):
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)


def truncate(text: str, max_chars: int = 700) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(errors="ignore")
    match = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
    if not match:
        return {}
    parsed: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^(name|description):\s*(.+)$", line)
        if item:
            parsed[item.group(1)] = item.group(2).strip().strip("\"'")
    return parsed


def check_required_files() -> CheckResult:
    missing_required = [display_path(path) for path in REQUIRED_PROMPT_REWRITE_FILES if not path.exists()]
    missing_optional = [display_path(path) for path in OPTIONAL_PACK_FILES if not path.exists()]
    if missing_required:
        return CheckResult(
            "required-files",
            "fail",
            f"Missing {len(missing_required)} required prompt-rewrite files.",
            missing_required,
        )
    if missing_optional:
        return CheckResult(
            "required-files",
            "warn",
            "Prompt-rewrite files are present, but optional pack files are missing.",
            missing_optional,
        )
    total = len(REQUIRED_PROMPT_REWRITE_FILES) + len(OPTIONAL_PACK_FILES)
    return CheckResult("required-files", "pass", f"Found {total} required and optional pack files.", [])


def check_skill_frontmatter() -> CheckResult:
    failures: list[str] = []
    warnings: list[str] = []
    for skill_dir in (PROMPT_REWRITE_DIR, PROFILE_REVIEW_DIR):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            warnings.append(f"{skill_md}: not installed")
            continue
        metadata = parse_frontmatter(skill_md)
        for key in ("name", "description"):
            if not metadata.get(key):
                failures.append(f"{skill_md}: missing {key}")
    if failures:
        return CheckResult("skill-frontmatter", "fail", "Skill frontmatter is incomplete.", failures)
    if warnings:
        return CheckResult("skill-frontmatter", "warn", "Optional skill frontmatter could not be checked.", warnings)
    return CheckResult("skill-frontmatter", "pass", "Skill frontmatter has name and description fields.", [])


def check_script_syntax() -> CheckResult:
    existing = [str(path) for path in SCRIPT_FILES if path.exists()]
    if not existing:
        return CheckResult("script-syntax", "fail", "No Python scripts were found to compile.", [])
    result = run([sys.executable, "-m", "py_compile", *existing])
    if result.returncode != 0:
        return CheckResult("script-syntax", "fail", "Python syntax check failed.", [truncate(result.stderr or result.stdout)])
    return CheckResult("script-syntax", "pass", f"Compiled {len(existing)} scripts.", [])


def check_fixture_suite() -> CheckResult:
    result = run([sys.executable, str(PROMPT_REWRITE_DIR / "scripts" / "check_dogfood_fixtures.py")])
    if result.returncode != 0:
        return CheckResult("dogfood-fixtures", "fail", "Fixture validation failed.", [truncate(result.stdout + result.stderr)])
    ok_count = sum(1 for line in result.stdout.splitlines() if line.startswith("ok: "))
    return CheckResult("dogfood-fixtures", "pass", f"Fixture validation passed for {ok_count} fixtures.", [])


def check_token_estimators(evidence_file: Path | None) -> CheckResult:
    commands = [
        [
            sys.executable,
            str(PROMPT_REWRITE_DIR / "scripts" / "estimate_rewrite_tokens.py"),
            "--fixture",
            str(PROMPT_REWRITE_DIR / "fixtures" / "review_handoff_rewrite.json"),
            "--format",
            "json",
        ],
    ]
    if (PROFILE_REVIEW_DIR / "scripts" / "estimate_review_tokens.py").exists():
        commands.append(
            [
                sys.executable,
                str(PROFILE_REVIEW_DIR / "scripts" / "estimate_review_tokens.py"),
                "--format",
                "json",
            ]
        )
    else:
        commands.append([])

    if evidence_file and commands[-1]:
        commands[-1].extend(["--evidence-file", str(evidence_file)])

    details: list[str] = []
    skipped_review = False
    for command in commands:
        if not command:
            skipped_review = True
            continue
        result = run(command)
        if result.returncode != 0:
            return CheckResult("token-estimators", "fail", "Token estimator failed.", [truncate(result.stderr or result.stdout)])
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return CheckResult("token-estimators", "fail", "Token estimator returned invalid JSON.", [str(exc)])
        details.append(f"{payload['mode']}: {payload['estimated_total_tokens']} estimated tokens")
    if skipped_review:
        details.append("review estimator skipped because prompt-profile-review is not installed")
        return CheckResult("token-estimators", "warn", "Rewrite token estimator passed; profile estimator was skipped.", details)
    return CheckResult("token-estimators", "pass", "Token estimators returned JSON totals.", details)


def check_installed_skill_scan() -> CheckResult:
    result = run(
        [
            sys.executable,
            str(PROMPT_REWRITE_DIR / "scripts" / "list_installed_skills.py"),
            "--no-cache",
            "--format",
            "json",
            "--roots",
            str(SKILLS_ROOT),
            "--query",
            "prompt-rewrite,prompt-profile-review",
            "--limit",
            "20",
        ]
    )
    if result.returncode != 0:
        return CheckResult("installed-skill-scan", "fail", "Installed-skill scan failed.", [truncate(result.stderr or result.stdout)])
    try:
        skills = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return CheckResult("installed-skill-scan", "fail", "Installed-skill scan returned invalid JSON.", [str(exc)])
    invocations = {skill.get("invocation") for skill in skills if isinstance(skill, dict)}
    if "prompt-rewrite" not in invocations:
        return CheckResult("installed-skill-scan", "fail", "prompt-rewrite was not discoverable from local roots.", sorted(invocations))
    if "prompt-profile-review" not in invocations:
        return CheckResult(
            "installed-skill-scan",
            "warn",
            "prompt-rewrite is discoverable; prompt-profile-review is not installed or not discoverable.",
            sorted(invocations),
        )
    return CheckResult("installed-skill-scan", "pass", "Local skill scan found both Supaprompt skills.", sorted(invocations))


def check_plugin_cache(limit: int) -> CheckResult:
    cache_root = Path("~/.codex/plugins/cache").expanduser()
    if not cache_root.is_dir():
        return CheckResult("plugin-cache", "warn", "Plugin cache directory was not found.", [str(cache_root)])
    result = run(
        [
            sys.executable,
            str(PROMPT_REWRITE_DIR / "scripts" / "list_installed_skills.py"),
            "--include-plugin-cache",
            "--no-cache",
            "--format",
            "json",
            "--query",
            "github,gmail,google-drive,notion,openai-developers,browser,vercel",
            "--limit",
            str(limit),
        ]
    )
    if result.returncode != 0:
        return CheckResult("plugin-cache", "fail", "Plugin-cache skill scan failed.", [truncate(result.stderr or result.stdout)])
    try:
        skills = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return CheckResult("plugin-cache", "fail", "Plugin-cache scan returned invalid JSON.", [str(exc)])
    plugin_invocations = sorted(
        skill["invocation"]
        for skill in skills
        if isinstance(skill, dict) and ":" in str(skill.get("invocation", ""))
    )
    if not plugin_invocations:
        return CheckResult("plugin-cache", "warn", "Plugin cache exists but no plugin-prefixed skills matched.", [])
    return CheckResult("plugin-cache", "pass", f"Found {len(plugin_invocations)} plugin-prefixed skills.", plugin_invocations[:limit])


def check_forward_test_tools() -> CheckResult:
    with tempfile.TemporaryDirectory(prefix="supaprompt-doctor-") as temp_dir:
        result_path = Path(temp_dir) / "forward-results.json"
        init_result = run(
            [
                sys.executable,
                str(PROMPT_REWRITE_DIR / "scripts" / "score_forward_tests.py"),
                "--init-results",
                str(result_path),
                "--limit",
                "1",
            ]
        )
        if init_result.returncode != 0:
            return CheckResult("forward-test-tools", "fail", "Could not create forward-test result template.", [truncate(init_result.stderr or init_result.stdout)])
        score_result = run(
            [
                sys.executable,
                str(PROMPT_REWRITE_DIR / "scripts" / "score_forward_tests.py"),
                "--results",
                str(result_path),
                "--limit",
                "1",
                "--format",
                "json",
            ]
        )
        if score_result.returncode == 0:
            return CheckResult("forward-test-tools", "fail", "Empty forward-test template unexpectedly passed.", [])
        try:
            payload = json.loads(score_result.stdout)
        except json.JSONDecodeError as exc:
            return CheckResult("forward-test-tools", "fail", "Forward-test scorer returned invalid JSON.", [str(exc)])
        if payload.get("overall_status") != "incomplete":
            return CheckResult("forward-test-tools", "fail", "Empty forward-test template did not report incomplete.", [json.dumps(payload, indent=2)])
    return CheckResult("forward-test-tools", "pass", "Forward-test template creation and incomplete scoring behaved as expected.", [])


def check_system_validator() -> CheckResult:
    if not SYSTEM_VALIDATOR.exists():
        return CheckResult("system-validator", "warn", "System quick_validate.py was not found.", [str(SYSTEM_VALIDATOR)])
    details: list[str] = []
    for skill_dir in (PROMPT_REWRITE_DIR, PROFILE_REVIEW_DIR):
        if not (skill_dir / "SKILL.md").exists():
            details.append(f"{skill_dir.name}: skipped because not installed")
            continue
        result = run([sys.executable, str(SYSTEM_VALIDATOR), str(skill_dir)])
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            details.append(f"{skill_dir.name}: ok")
            continue
        if "No module named 'yaml'" in combined:
            return CheckResult(
                "system-validator",
                "warn",
                "System validator is installed but PyYAML is missing in this Python environment.",
                ["Install PyYAML or run the validator with the Codex-bundled Python environment."],
            )
        return CheckResult("system-validator", "fail", "System validator failed.", [truncate(combined)])
    return CheckResult("system-validator", "pass", "System validator passed for both skills.", details)


def check_git_state() -> CheckResult:
    branch = run(["git", "branch", "--show-current"])
    status = run(["git", "status", "--short"])
    if branch.returncode != 0 or status.returncode != 0:
        return CheckResult("git-state", "warn", "Could not read git state.", [truncate(branch.stderr + status.stderr)])
    details = [f"branch: {branch.stdout.strip() or 'unknown'}"]
    if status.stdout.strip():
        details.append("working tree has local changes")
        return CheckResult("git-state", "warn", "Git working tree is not clean.", details)
    return CheckResult("git-state", "pass", "Git working tree is clean.", details)


def run_checks(args: argparse.Namespace) -> list[CheckResult]:
    evidence_file = args.evidence_file.expanduser() if args.evidence_file else None
    return [
        check_required_files(),
        check_skill_frontmatter(),
        check_script_syntax(),
        check_fixture_suite(),
        check_token_estimators(evidence_file),
        check_installed_skill_scan(),
        check_plugin_cache(args.plugin_scan_limit),
        check_forward_test_tools(),
        check_system_validator(),
        check_git_state(),
    ]


def overall_status(results: list[CheckResult]) -> str:
    statuses = {result.status for result in results}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def print_markdown(results: list[CheckResult]) -> None:
    status = overall_status(results)
    print("# Supaprompt Doctor")
    print()
    print(f"- Overall status: {status}")
    print()
    print("| Check | Status | Summary |")
    print("| --- | --- | --- |")
    for result in results:
        print(f"| {result.name} | {result.status} | {result.summary} |")
    details = [result for result in results if result.details]
    if details:
        print()
        print("## Details")
        for result in details:
            print()
            print(f"### {result.name}")
            for detail in result.details:
                print(f"- {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--evidence-file", type=Path, help="Optional evidence file for review token estimation")
    parser.add_argument("--plugin-scan-limit", type=int, default=8)
    args = parser.parse_args()

    results = run_checks(args)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "overall_status": overall_status(results),
                    "checks": [asdict(result) for result in results],
                },
                indent=2,
            )
        )
    else:
        print_markdown(results)
    return 1 if overall_status(results) == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
