#!/usr/bin/env python3
"""Estimate prompt-rewrite token use from a prompt, profile, skill map, or fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


INSTRUCTION_FILES = (
    "SKILL.md",
    "references/prompt-types.md",
    "references/quality-rubric.md",
    "references/personalization.md",
    "references/skill-routing.md",
)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def read_path(path: Path) -> str:
    try:
        return path.expanduser().read_text(errors="ignore")
    except OSError as exc:
        raise SystemExit(f"Could not read {path}: {exc}") from exc


def add_component(rows: list[dict[str, int | str]], name: str, text: str) -> None:
    rows.append(
        {
            "component": name,
            "chars": len(text),
            "estimated_tokens": estimate_tokens(text),
        }
    )


def fixture_text(data: dict[str, Any], *keys: str) -> str:
    parts: list[str] = []
    for key in keys:
        value = data.get(key)
        if not value:
            continue
        if isinstance(value, str):
            parts.append(value)
        else:
            parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return "\n\n".join(parts)


def print_markdown(mode: str, rows: list[dict[str, int | str]]) -> None:
    total_chars = sum(int(row["chars"]) for row in rows)
    total_tokens = sum(int(row["estimated_tokens"]) for row in rows)
    print(f"Mode: {mode}")
    print()
    print("| Component | Chars | Estimated tokens |")
    print("| --- | ---: | ---: |")
    for row in rows:
        print(f"| {row['component']} | {row['chars']} | {row['estimated_tokens']} |")
    print(f"| **Total** | **{total_chars}** | **{total_tokens}** |")
    print()
    print("Token counts are rough estimates for planning, not provider billing records.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--prompt-text", action="append", default=[], help="Inline rough prompt text")
    parser.add_argument("--prompt-file", action="append", type=Path, default=[], help="File containing the rough prompt")
    parser.add_argument("--profile-file", action="append", type=Path, default=[], help="Prompt profile or handoff file")
    parser.add_argument("--skill-map-file", action="append", type=Path, default=[], help="Installed-skill map file")
    parser.add_argument("--fixture", type=Path, help="Dogfood fixture JSON to estimate")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    rows: list[dict[str, int | str]] = []
    instructions = "\n\n".join(
        read_path(args.skill_dir / relative)
        for relative in INSTRUCTION_FILES
        if (args.skill_dir / relative).exists()
    )
    add_component(rows, "rewrite instructions", instructions)

    prompt_parts = [read_path(path) for path in args.prompt_file]
    prompt_parts.extend(args.prompt_text)
    profile_parts = [read_path(path) for path in args.profile_file]
    skill_map_parts = [read_path(path) for path in args.skill_map_file]

    if args.fixture:
        data = json.loads(read_path(args.fixture))
        prompt_parts.append(fixture_text(data, "rough_prompt"))
        profile_parts.append(fixture_text(data, "golden_profile", "golden_handoff"))
        skill_map_parts.append(fixture_text(data, "installed_skill_snapshot"))

    add_component(rows, "rough prompt", "\n\n".join(prompt_parts))
    add_component(rows, "profile or handoff", "\n\n".join(profile_parts))
    add_component(rows, "installed skill map", "\n\n".join(skill_map_parts))

    if args.format == "json":
        total_chars = sum(int(row["chars"]) for row in rows)
        total_tokens = sum(int(row["estimated_tokens"]) for row in rows)
        print(
            json.dumps(
                {
                    "mode": "rewrite",
                    "components": rows,
                    "total_chars": total_chars,
                    "estimated_total_tokens": total_tokens,
                    "note": "Rough estimate for planning, not provider billing.",
                },
                indent=2,
            )
        )
    else:
        print_markdown("rewrite", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
