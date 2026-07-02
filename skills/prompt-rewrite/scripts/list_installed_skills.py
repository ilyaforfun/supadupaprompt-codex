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

PLUGIN_PREFIXES = {
    "browser": "browser",
    "chrome": "chrome",
    "github": "github",
    "gmail": "gmail",
    "google-drive": "google-drive",
    "linear": "linear",
    "notion": "notion",
    "openai-developers": "openai-developers",
    "build-web-apps": "build-web-apps",
    "vercel": "vercel",
}

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


def plugin_prefix_for_path(path: Path) -> str | None:
    parts = path.expanduser().parts
    for index, part in enumerate(parts):
        if part in {"openai-bundled", "openai-curated", "openai-curated-remote"} and index + 1 < len(parts):
            return PLUGIN_PREFIXES.get(parts[index + 1])
    return None


def skill_invocation(name: str, path: Path) -> str:
    prefix = plugin_prefix_for_path(path)
    if prefix:
        return f"{prefix}:{name}"
    return name


def skill_family(name: str, description: str, path: Path) -> str:
    invocation = skill_invocation(name, path).lower()
    skill_name = name.lower()
    invocation_tail = invocation.split(":", 1)[-1]
    slug = path.parent.name.lower()
    parts = {part.lower() for part in path.expanduser().parts}
    desc = description.lower()
    if invocation.startswith("github:") or skill_name in {"github", "yeet"} or skill_name.startswith("gh-"):
        return "github"
    if invocation.startswith(("browser:", "chrome:")):
        return invocation.split(":", 1)[0]
    if "github" in parts:
        return "github"
    if (
        "gstack" in parts
        or "(gstack)" in desc
        or skill_name.startswith("gstack-")
        or invocation_tail.startswith("gstack-")
        or slug.startswith("gstack-")
    ):
        return "gstack"
    if "browser" in parts or skill_name in {"browser", "browse", "control-in-app-browser"}:
        return "browser"
    return "standalone"


def skill_category(name: str, description: str, path: Path) -> str:
    invocation = skill_invocation(name, path).lower()
    skill_name = name.lower()
    text = f"{invocation} {description}".lower()
    if invocation.startswith("github:") or skill_name in {"github", "yeet"} or skill_name.startswith("gh-"):
        return "github"
    if (
        invocation.startswith(("browser:", "chrome:"))
        or skill_name in {"gstack", "browse", "browser", "control-in-app-browser", "open-gstack-browser", "qa", "qa-only"}
        or "gstack" in skill_name
        or "browser" in skill_name
    ):
        return "browser"
    if skill_name in {"skill-creator", "skill-installer"} or skill_name.startswith("skill-"):
        return "skill"
    if any(needle in skill_name for needle in ("design", "critique", "polish", "impeccable", "arrange", "typeset")):
        return "design"
    categories = (
        ("github", ("github", "pull request", " pr ", "issue", "branch", "commit", "yeet")),
        ("design", ("design", "ux", "ui", "visual", "polish", "typography", "layout")),
        ("docs", ("docs", "document", "docx", "slides", "spreadsheet", "pdf", "notion")),
        ("skill", ("skill-creator", "skill-installer", "skillify")),
        ("browser", ("browser", "gstack", "qa", "screenshot", "localhost", "chrome", "workflow")),
        ("research", ("research", "scrape", "web page", "source", "citation")),
        ("automation", ("automation", "cron", "reminder", "monitor", "canary")),
    )
    for category, needles in categories:
        if any(needle in text for needle in needles):
            return category
    return "other"


def skill_intent(name: str, description: str, path: Path) -> str:
    invocation = skill_invocation(name, path).lower()
    skill_name = name.lower()
    invocation_tail = invocation.split(":", 1)[-1]
    slug = path.parent.name.lower()
    exact_names = {skill_name, invocation_tail, slug}

    exact_intents = (
        ("qa-report", ("qa-only", "gstack-qa-only")),
        ("qa-fix", ("qa", "gstack-qa")),
        ("design-review", ("design-review", "gstack-design-review", "critique", "polish")),
        ("debug", ("investigate", "gstack-investigate", "gstack-openclaw-investigate")),
        ("code-review", ("review", "gstack-review")),
        ("publish-pr", ("ship", "gstack-ship", "yeet")),
        ("deploy-canary", ("canary", "gstack-canary", "land-and-deploy", "gstack-land-and-deploy")),
        ("perf", ("benchmark", "gstack-benchmark")),
        ("research", ("scrape", "gstack-scrape")),
        (
            "planning",
            (
                "autoplan",
                "office-hours",
                "plan-ceo-review",
                "plan-design-review",
                "plan-devex-review",
                "plan-eng-review",
            ),
        ),
        ("skill-work", ("skill-creator", "skill-installer", "skillify")),
        ("docs", ("document-generate", "document-release", "make-pdf")),
        (
            "browser-qa",
            (
                "gstack",
                "browse",
                "browser",
                "control-in-app-browser",
                "open-gstack-browser",
                "agent-browser",
                "agent-browser-verify",
                "frontend-testing-debugging",
            ),
        ),
    )
    for intent, names in exact_intents:
        if exact_names.intersection(names):
            return intent

    text = f"{invocation} {description}".lower()
    intent_rules = (
        ("qa-report", ("qa-only", "report-only", "structured report", "never fixes", "without any code changes")),
        ("design-review", ("design-review", "designer", "visual", "spacing", "typography", "layout", "ux")),
        ("debug", ("investigate", "debug", "root cause", "stack trace", "broken behavior")),
        ("code-review", ("pre-landing", "code review", "check my diff", "review this pr")),
        ("deploy-canary", ("canary", "land-and-deploy", "post-deploy", "production health")),
        ("perf", ("benchmark", "performance", "vitals", "latency")),
        ("research", ("scrape", "research", "source", "citation", "web page")),
        ("planning", ("autoplan", "office-hours", "ceo review", "eng review", "plan review")),
        ("skill-work", ("skill-creator", "skill-installer", "skillify")),
        ("docs", ("document", "docs", "slides", "spreadsheet", "pdf", "make-pdf")),
        ("publish-pr", ("ship workflow", "create a pr", "draft pr", "publish local changes")),
        ("qa-fix", ("qa test", "fix bugs", "iteratively fixes", "source code")),
        ("browser-qa", ("browse", "browser", "screenshot", "localhost", "dogfood")),
    )
    for intent, needles in intent_rules:
        if any(needle in text for needle in needles):
            return intent
    return "general"


def score_skill(
    name: str,
    description: str,
    path: Path,
    queries: list[str],
    categories: list[str],
    families: list[str],
    intents: list[str],
) -> int:
    invocation = skill_invocation(name, path).lower()
    skill_name = name.lower()
    desc = description.lower()
    path_text = str(path).lower()
    category = skill_category(name, description, path)
    family = skill_family(name, description, path)
    intent = skill_intent(name, description, path)

    if categories and category not in categories:
        return 0
    if families and family not in families:
        return 0
    if intents and intent not in intents:
        return 0
    if not queries:
        return 100

    best_score = 0
    for query in queries:
        query = query.lower()
        if query in {invocation, f"${invocation}", skill_name, f"${skill_name}"}:
            best_score = max(best_score, 1000)
        elif invocation.endswith(f":{query}") or skill_name == query:
            best_score = max(best_score, 850)
        elif query in invocation.split(":") or query in re.split(r"[-_:/]+", skill_name):
            best_score = max(best_score, 650)
        elif query in invocation:
            best_score = max(best_score, 450)
        elif query in path_text:
            best_score = max(best_score, 200)
        elif query in desc:
            best_score = max(best_score, 50)

    score = best_score
    if category in queries:
        score += 150
    if family in queries:
        score += 120
    if intent in queries:
        score += 180
    return score


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS, help="Skill roots to scan")
    parser.add_argument("--query", help="Comma-separated filters for name or description")
    parser.add_argument("--category", help="Comma-separated categories: browser,github,design,docs,skill,research,automation")
    parser.add_argument("--family", help="Comma-separated skill families, for example: gstack,github,browser")
    parser.add_argument("--intent", help="Comma-separated intents, for example: qa-fix,qa-report,design-review,publish-pr")
    parser.add_argument("--include-plugin-cache", action="store_true", help="Also scan ~/.codex/plugins/cache")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--limit", type=int, default=120)
    args = parser.parse_args()

    queries = [item.strip().lower() for item in (args.query or "").split(",") if item.strip()]
    categories = [item.strip().lower() for item in (args.category or "").split(",") if item.strip()]
    families = [item.strip().lower() for item in (args.family or "").split(",") if item.strip()]
    intents = [item.strip().lower() for item in (args.intent or "").split(",") if item.strip()]
    roots = [Path(item) for item in args.roots]

    skills: list[dict[str, str]] = []
    seen_invocations: set[str] = set()
    for skill_md in iter_skill_files(roots, args.include_plugin_cache):
        metadata = parse_frontmatter(skill_md.read_text(errors="ignore"))
        name = metadata.get("name") or skill_md.parent.name
        description = metadata.get("description", "")
        invocation = skill_invocation(name, skill_md)
        if invocation in seen_invocations:
            continue
        score = score_skill(name, description, skill_md, queries, categories, families, intents)
        if score <= 0:
            continue
        seen_invocations.add(invocation)
        skills.append(
            {
                "name": name,
                "invocation": invocation,
                "category": skill_category(name, description, skill_md),
                "family": skill_family(name, description, skill_md),
                "intent": skill_intent(name, description, skill_md),
                "description": description,
                "path": str(skill_md),
                "score": str(score),
            }
        )

    skills = sorted(
        skills,
        key=lambda skill: (
            -int(skill["score"]),
            skill["family"],
            skill["intent"],
            skill["category"],
            skill["invocation"],
            skill["path"],
        ),
    )[: args.limit]

    if args.format == "json":
        print(json.dumps(skills, indent=2, ensure_ascii=False))
    else:
        for skill in skills:
            desc = re.sub(r"\s+", " ", skill["description"]).strip()
            if len(desc) > 180:
                desc = desc[:177].rstrip() + "..."
            print(
                f"- ${skill['invocation']} "
                f"[family={skill['family']} intent={skill['intent']} category={skill['category']}] "
                f"- {desc} ({skill['path']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
