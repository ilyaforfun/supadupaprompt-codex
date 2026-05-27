#!/usr/bin/env python3
"""Collect candidate user-prompt evidence from local Markdown or JSONL logs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PATTERNS = (
    "when the user",
    "user asked",
    "user asks",
    "user says",
    "user said",
    "prompt",
)


def iter_files(paths: list[Path]) -> Iterable[Path]:
    for path in paths:
        path = path.expanduser()
        if path.is_file():
            yield path
            continue
        if not path.is_dir():
            continue
        candidates = [
            item
            for item in path.rglob("*")
            if item.is_file() and item.suffix.lower() in {".md", ".txt", ".jsonl"}
        ]
        yield from sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)


def compact(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def strings_from_content(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(strings_from_content(item))
        return out
    if isinstance(value, dict):
        out = []
        for key in ("text", "content", "message", "input"):
            if key in value:
                out.extend(strings_from_content(value[key]))
        return out
    return []


def user_texts_from_json(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        role = str(value.get("role") or value.get("author") or "").lower()
        kind = str(value.get("type") or "").lower()
        if role == "user" or kind in {"user_message", "user"}:
            found.extend(strings_from_content(value))
        for child in value.values():
            found.extend(user_texts_from_json(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(user_texts_from_json(child))
    return found


def matches(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def scan_markdown(path: Path, patterns: list[str], max_chars: int) -> Iterable[dict[str, str]]:
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except OSError:
        return
    for number, line in enumerate(lines, start=1):
        if matches(line, patterns):
            yield {
                "source": str(path),
                "line": str(number),
                "text": compact(line, max_chars),
            }


def scan_jsonl(path: Path, patterns: list[str], max_chars: int) -> Iterable[dict[str, str]]:
    try:
        handle = path.open(errors="ignore")
    except OSError:
        return
    with handle:
        for number, line in enumerate(handle, start=1):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            for text in user_texts_from_json(payload):
                if not patterns or matches(text, patterns):
                    yield {
                        "source": str(path),
                        "line": str(number),
                        "text": compact(text, max_chars),
                    }


def scan_file(path: Path, patterns: list[str], max_chars: int) -> Iterable[dict[str, str]]:
    if path.suffix.lower() == ".jsonl":
        yield from scan_jsonl(path, patterns, max_chars)
    else:
        yield from scan_markdown(path, patterns, max_chars)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to scan")
    parser.add_argument("--query", help="Comma-separated case-insensitive filters")
    parser.add_argument("--limit", type=int, default=80, help="Maximum matches to print")
    parser.add_argument("--max-chars", type=int, default=500, help="Maximum characters per match")
    parser.add_argument("--format", choices=("markdown", "jsonl"), default="markdown")
    args = parser.parse_args()

    patterns = [item.strip().lower() for item in (args.query or "").split(",") if item.strip()]
    if not patterns:
        patterns = list(DEFAULT_PATTERNS)

    count = 0
    for path in iter_files(args.paths):
        for match in scan_file(path, patterns, args.max_chars):
            if args.format == "jsonl":
                print(json.dumps(match, ensure_ascii=False))
            else:
                print(f"- {match['source']}:{match['line']} - {match['text']}")
            count += 1
            if count >= args.limit:
                return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
