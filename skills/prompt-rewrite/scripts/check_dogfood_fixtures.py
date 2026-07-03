#!/usr/bin/env python3
"""Validate golden dogfood fixtures for review -> handoff -> rewrite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "name",
    "prompt_type",
    "source_prompts",
    "golden_profile",
    "golden_handoff",
    "rough_prompt",
    "golden_rewrite",
    "checks",
}

HANDOFF_KEYS = {"preserve", "add_by_default", "ask_before", "avoid"}


def normalized(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_fixture(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]

    missing = REQUIRED_TOP_LEVEL - set(data)
    require(not missing, f"{path}: missing top-level keys: {', '.join(sorted(missing))}", failures)
    if missing:
        return failures

    require(isinstance(data["source_prompts"], list) and data["source_prompts"], f"{path}: source_prompts must be a non-empty list", failures)
    require(isinstance(data["prompt_type"], str) and data["prompt_type"].strip(), f"{path}: prompt_type must be non-empty text", failures)
    require(isinstance(data["golden_profile"], dict) and data["golden_profile"], f"{path}: golden_profile must be a non-empty object", failures)
    require(isinstance(data["golden_handoff"], dict), f"{path}: golden_handoff must be an object", failures)
    require(isinstance(data["rough_prompt"], str) and data["rough_prompt"].strip(), f"{path}: rough_prompt must be non-empty text", failures)
    require(isinstance(data["golden_rewrite"], str) and data["golden_rewrite"].strip(), f"{path}: golden_rewrite must be non-empty text", failures)

    handoff = data.get("golden_handoff", {})
    missing_handoff = HANDOFF_KEYS - set(handoff)
    require(not missing_handoff, f"{path}: missing handoff keys: {', '.join(sorted(missing_handoff))}", failures)
    for key in HANDOFF_KEYS.intersection(handoff):
        require(isinstance(handoff[key], list) and handoff[key], f"{path}: handoff.{key} must be a non-empty list", failures)

    checks = data.get("checks", {})
    labeled_handoff = {key.replace("_", " "): value for key, value in handoff.items()}
    handoff_text = normalized(labeled_handoff)
    rewrite_text = normalized(data.get("golden_rewrite", ""))
    skill_snapshot_text = normalized(data.get("installed_skill_snapshot", []))
    for needle in checks.get("handoff_must_include", []):
        require(needle.lower() in handoff_text, f"{path}: handoff missing {needle!r}", failures)
    for needle in checks.get("rewrite_must_include", []):
        require(needle.lower() in rewrite_text, f"{path}: rewrite missing {needle!r}", failures)
    for needle in checks.get("rewrite_must_not_include", []):
        require(needle.lower() not in rewrite_text, f"{path}: rewrite contains forbidden {needle!r}", failures)
    for needle in checks.get("skill_snapshot_must_include", []):
        require(needle.lower() in skill_snapshot_text, f"{path}: skill snapshot missing {needle!r}", failures)
    for needle in checks.get("prompt_type_must_include", []):
        require(needle.lower() in data["prompt_type"].lower(), f"{path}: prompt_type missing {needle!r}", failures)

    return failures


def fixture_paths(args: argparse.Namespace) -> list[Path]:
    if args.fixtures:
        return [Path(item) for item in args.fixtures]
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
    return sorted(fixtures_dir.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", help="Fixture JSON files. Defaults to all prompt-rewrite fixtures.")
    args = parser.parse_args()

    failures: list[str] = []
    paths = fixture_paths(args)
    if not paths:
        print("No fixtures found")
        return 1

    names: set[str] = set()
    prompt_types: set[str] = set()
    for path in paths:
        path_failures = validate_fixture(path)
        if path_failures:
            failures.extend(path_failures)
        else:
            data = json.loads(path.read_text())
            name = data["name"]
            prompt_type = data["prompt_type"]
            if name in names:
                failures.append(f"{path}: duplicate fixture name {name!r}")
            if prompt_type in prompt_types:
                failures.append(f"{path}: duplicate prompt_type {prompt_type!r}")
            names.add(name)
            prompt_types.add(prompt_type)
            print(f"ok: {path}")

    if failures:
        for failure in failures:
            print(f"error: {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
