#!/usr/bin/env python3
"""Estimate prompt-profile-review token use from local files or text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


INSTRUCTION_FILES = (
    "SKILL.md",
    "references/profile-schema.md",
    "references/source-guide.md",
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
    parser.add_argument("--evidence-file", action="append", type=Path, default=[], help="Local evidence file to include")
    parser.add_argument("--evidence-text", action="append", default=[], help="Inline evidence text to include")
    parser.add_argument("--profile-output-file", type=Path, help="Optional drafted profile output")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    rows: list[dict[str, int | str]] = []
    instructions = "\n\n".join(
        read_path(args.skill_dir / relative)
        for relative in INSTRUCTION_FILES
        if (args.skill_dir / relative).exists()
    )
    add_component(rows, "review instructions", instructions)

    evidence_parts = [read_path(path) for path in args.evidence_file]
    evidence_parts.extend(args.evidence_text)
    add_component(rows, "source evidence", "\n\n".join(evidence_parts))

    if args.profile_output_file:
        add_component(rows, "drafted profile output", read_path(args.profile_output_file))

    if args.format == "json":
        total_chars = sum(int(row["chars"]) for row in rows)
        total_tokens = sum(int(row["estimated_tokens"]) for row in rows)
        print(
            json.dumps(
                {
                    "mode": "review",
                    "components": rows,
                    "total_chars": total_chars,
                    "estimated_total_tokens": total_tokens,
                    "note": "Rough estimate for planning, not provider billing.",
                },
                indent=2,
            )
        )
    else:
        print_markdown("review", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
