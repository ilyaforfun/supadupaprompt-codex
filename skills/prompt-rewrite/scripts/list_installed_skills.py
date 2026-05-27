#!/usr/bin/env python3
"""List local Codex/agent skills from common skill roots."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_ROOTS = (
    "~/.codex/skills",
    "~/.agents/skills",
    ".codex/skills",
    ".agents/skills",
    "skills",
)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
    if not match:
        return {}
    frontmatter = match.group(1)
    parsed: dict[str, str] = {}
    lines = frontmatter.splitlines()
    for index, line in enumerate(lines):
        inline = re.match(r"^(name|description):\s*(.*)$", line)
        if not inline:
            continue
        key, value = inline.groups()
        value = value.strip()
        if value in {"|", ">"}:
            block: list[str] = []
            for following in lines[index + 1 :]:
                if re.match(r"^[A-Za-z0-9_-]+:\s*", following):
                    break
                block.append(following.strip())
            parsed[key] = " ".join(item for item in block if item).strip()
        else:
            parsed[key] = value.strip("\"'")
    return parsed


def iter_skill_files(roots: list[Path], include_plugin_cache: bool) -> list[Path]:
    expanded: list[Path] = []
    for root in roots:
        path = root.expanduser()
        if path.is_dir():
            expanded.append(path)
    if include_plugin_cache:
        cache_root = Path("~/.codex/plugins/cache").expanduser()
        if cache_root.is_dir():
            expanded.append(cache_root)

    seen: set[Path] = set()
    files: list[Path] = []
    for root in expanded:
        for skill_md in root.rglob("SKILL.md"):
            if skill_md in seen:
                continue
            seen.add(skill_md)
            files.append(skill_md)
    return sorted(files)


def matches_query(name: str, description: str, queries: list[str]) -> bool:
    if not queries:
        return True
    haystack = f"{name} {description}".lower()
    return any(query in haystack for query in queries)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS, help="Skill roots to scan")
    parser.add_argument("--query", help="Comma-separated filters for name or description")
    parser.add_argument("--include-plugin-cache", action="store_true", help="Also scan ~/.codex/plugins/cache")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--limit", type=int, default=120)
    args = parser.parse_args()

    queries = [item.strip().lower() for item in (args.query or "").split(",") if item.strip()]
    roots = [Path(item) for item in args.roots]

    skills: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for skill_md in iter_skill_files(roots, args.include_plugin_cache):
        metadata = parse_frontmatter(skill_md.read_text(errors="ignore"))
        name = metadata.get("name") or skill_md.parent.name
        description = metadata.get("description", "")
        if name in seen_names:
            continue
        if not matches_query(name, description, queries):
            continue
        seen_names.add(name)
        skills.append(
            {
                "name": name,
                "description": description,
                "path": str(skill_md),
            }
        )
        if len(skills) >= args.limit:
            break

    if args.format == "json":
        print(json.dumps(skills, indent=2, ensure_ascii=False))
    else:
        for skill in skills:
            desc = re.sub(r"\s+", " ", skill["description"]).strip()
            if len(desc) > 180:
                desc = desc[:177].rstrip() + "..."
            print(f"- ${skill['name']} - {desc} ({skill['path']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
