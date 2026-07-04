#!/usr/bin/env python3
"""Install supadupaprompt-codex skills into a local Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILLS_DIR = REPO_ROOT / "skills"
DEFAULT_SKILLS = ("prompt-rewrite", "prompt-profile-review")


def default_codex_skills_dir() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "skills"


def ignore_generated(_dir: str, names: list[str]) -> set[str]:
    ignored = {"__pycache__", ".DS_Store"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def install_skill(skill: str, target_root: Path, *, force: bool, dry_run: bool) -> str:
    source = SOURCE_SKILLS_DIR / skill
    target = target_root / skill
    if not source.is_dir():
        raise SystemExit(f"missing bundled skill: {source}")

    if target.exists() and not force:
        action = "would skip" if dry_run else "skip"
        return f"{action}: {skill} already exists at {target} (use --force to replace)"

    if dry_run:
        action = "replace" if target.exists() else "install"
        return f"would {action}: {skill} -> {target}"

    target_root.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_dir():
            raise SystemExit(f"refusing to replace non-directory target: {target}")
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=ignore_generated)
    return f"installed: {skill} -> {target}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=default_codex_skills_dir(),
        help="Target Codex skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--skill",
        action="append",
        choices=DEFAULT_SKILLS,
        help="Install one skill. Repeat to install multiple. Defaults to both skills.",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing installed skill directories.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change without copying files.")
    parser.add_argument("--list", action="store_true", help="List bundled skills and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills = tuple(args.skill) if args.skill else DEFAULT_SKILLS

    if args.list:
        for skill in DEFAULT_SKILLS:
            print(skill)
        return 0

    target_root = args.skills_dir.expanduser()
    print(f"Target skills directory: {target_root}")
    for skill in skills:
        print(f"- {install_skill(skill, target_root, force=args.force, dry_run=args.dry_run)}")

    if not args.dry_run:
        print()
        print("Restart Codex so newly installed skills are discovered.")
        print("Then run: python3 skills/prompt-rewrite/scripts/supaprompt_doctor.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
