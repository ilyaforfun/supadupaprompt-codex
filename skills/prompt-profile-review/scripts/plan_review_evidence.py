#!/usr/bin/env python3
"""Plan a narrow evidence set for prompt-profile-review."""

from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path
from statistics import mean
from typing import Any

import collect_user_prompts


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
INSTRUCTION_FILES = (
    "SKILL.md",
    "references/profile-schema.md",
    "references/source-guide.md",
)
DEFAULT_SOURCE = Path("~/.codex/memories/MEMORY.md")
STOPWORDS = {
    "about",
    "again",
    "before",
    "everything",
    "for",
    "from",
    "have",
    "how",
    "prompt",
    "prompts",
    "review",
    "scan",
    "scanning",
    "that",
    "this",
    "with",
    "work",
}


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def read_text(path: Path) -> str:
    try:
        return path.expanduser().read_text(errors="ignore")
    except OSError:
        return ""


def instruction_text() -> str:
    return "\n\n".join(
        read_text(SKILL_DIR / relative)
        for relative in INSTRUCTION_FILES
        if (SKILL_DIR / relative).exists()
    )


def query_patterns(goal: str, query: str | None) -> list[str]:
    raw = query if query else goal
    parts = [item.strip().lower() for item in raw.split(",") if item.strip()]
    words = re.findall(r"[a-z0-9][a-z0-9-]{2,}", raw.lower())
    parts.extend(word for word in words if word not in STOPWORDS)
    parts.extend(("when the user", "user asks", "user says", "prompting style"))
    deduped: list[str] = []
    for part in parts:
        if part and part not in deduped:
            deduped.append(part)
    return deduped


def contains_term(text: str, term: str) -> bool:
    if len(term) <= 2:
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None
    return term in text


def score_match(match: dict[str, str], terms: list[str]) -> int:
    text = match["text"].lower()
    source = match["source"].lower()
    score = 0
    topical_hit = False
    for term in terms:
        if term in {"when the user", "user asks", "user says"}:
            continue
        if contains_term(text, term):
            score += 8 if " " in term else 4
            topical_hit = True
        if contains_term(source, term):
            score += 2
            topical_hit = True
    if "when the user" in text or "user asks" in text or "user says" in text:
        score += 1
    if "dogfood" in text:
        score += 10
        topical_hit = True
    if "profile review" in text or "prompt-profile-review" in text:
        score += 8
        topical_hit = True
    if contains_term(text, "pr") or "pull request" in text:
        score += 5
        topical_hit = True
    if not topical_hit:
        score -= 12
    return score


def collect_candidates(
    paths: list[Path],
    patterns: list[str],
    max_chars: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in collect_user_prompts.iter_files(paths):
        for match in collect_user_prompts.scan_file(path, patterns, max_chars):
            score = score_match(match, patterns)
            text = match["text"]
            candidates.append(
                {
                    "source": match["source"],
                    "line": int(match["line"]),
                    "text": text,
                    "score": score,
                    "estimated_tokens": estimate_tokens(text),
                }
            )
    if candidates:
        return sorted(candidates, key=lambda item: (-int(item["score"]), item["source"], int(item["line"])))

    fallback_patterns = ["prompt", "user", "review", "dogfood", "pr"]
    for path in collect_user_prompts.iter_files(paths):
        for match in collect_user_prompts.scan_file(path, fallback_patterns, max_chars):
            score = score_match(match, fallback_patterns)
            text = match["text"]
            candidates.append(
                {
                    "source": match["source"],
                    "line": int(match["line"]),
                    "text": text,
                    "score": score,
                    "estimated_tokens": estimate_tokens(text),
                }
            )
    return sorted(candidates, key=lambda item: (-int(item["score"]), item["source"], int(item["line"])))


def selected_evidence_text(selected: list[dict[str, Any]]) -> str:
    lines = []
    for item in selected:
        lines.append(f"- {item['source']}:{item['line']} - {item['text']}")
    return "\n".join(lines)


def select_candidates(
    candidates: list[dict[str, Any]],
    evidence_budget: int,
    max_snippets: int,
    per_file: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    file_counts: dict[str, int] = {}
    used_tokens = 0
    for candidate in candidates:
        if len(selected) >= max_snippets:
            break
        source = str(candidate["source"])
        if file_counts.get(source, 0) >= per_file:
            continue
        candidate_tokens = int(candidate["estimated_tokens"])
        if selected and used_tokens + candidate_tokens > evidence_budget:
            continue
        selected.append(candidate)
        file_counts[source] = file_counts.get(source, 0) + 1
        used_tokens += candidate_tokens
    if not selected and candidates:
        selected.append(candidates[0])
    return selected


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_commands(args: argparse.Namespace, selected: list[dict[str, Any]]) -> dict[str, str]:
    source_paths = [str(path) for path in args.paths]
    planner_command = [
        "python3",
        "skills/prompt-profile-review/scripts/plan_review_evidence.py",
        "--goal",
        args.goal,
        "--budget",
        str(args.budget),
        *source_paths,
    ]
    if args.query:
        planner_command.extend(["--query", args.query])
    if args.evidence_output:
        planner_command.extend(["--evidence-output", str(args.evidence_output)])

    review_command = (
        "Use $prompt-profile-review to review only the selected evidence for goal: "
        f"{args.goal!r}. Do not broad-scan all memories unless the selected evidence is too thin. "
        "Produce the standard profile plus a compact Prompt-Rewrite Handoff."
    )
    commands = {
        "planner_command": shell_join(planner_command),
        "review_command": review_command,
        "review_prompt": review_command,
    }
    if args.evidence_output:
        commands["estimate_command"] = shell_join(
            [
                "python3",
                "skills/prompt-profile-review/scripts/estimate_review_tokens.py",
                "--evidence-file",
                str(args.evidence_output),
            ]
        )
    elif selected:
        commands["evidence_note"] = "Use the selected evidence block from this report as inline evidence."
    return commands


def write_evidence(path: Path, goal: str, selected: list[dict[str, Any]]) -> None:
    text = f"# Planned Prompt-Review Evidence\n\nGoal: {goal}\n\n{selected_evidence_text(selected)}\n"
    path.expanduser().parent.mkdir(parents=True, exist_ok=True)
    path.expanduser().write_text(text)


def print_markdown(payload: dict[str, Any]) -> None:
    print("# Profile Review Evidence Plan")
    print()
    print(f"- Goal: {payload['goal']}")
    print(f"- Token budget: {payload['budget_tokens']}")
    print(f"- Estimated review tokens: {payload['estimated_review_total_tokens']}")
    print(f"- Instruction tokens: {payload['instruction_tokens']}")
    print(f"- Selected evidence tokens: {payload['selected_evidence_tokens']}")
    print(f"- Candidates considered: {payload['candidate_count']}")
    print(f"- Selected snippets: {payload['selected_snippet_count']}")
    print()
    print("## Selected Evidence")
    for item in payload["selected_evidence"]:
        print(f"- {item['source']}:{item['line']} score={item['score']} tokens={item['estimated_tokens']}")
        print(f"  {item['text']}")
    print()
    print("## Commands")
    for label, command in payload["commands"].items():
        print(f"- {label}: `{command}`")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[DEFAULT_SOURCE], help="Files or directories to rank")
    parser.add_argument("--goal", required=True, help="Review goal, such as 'PR/dogfood prompting style'")
    parser.add_argument("--query", help="Comma-separated search terms. Defaults to terms from --goal")
    parser.add_argument("--budget", type=int, default=5000, help="Target total review token budget")
    parser.add_argument("--max-snippets", type=int, default=12)
    parser.add_argument("--per-file", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=420)
    parser.add_argument("--evidence-output", type=Path, help="Optional file to write selected evidence into")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    patterns = query_patterns(args.goal, args.query)
    candidates = collect_candidates(args.paths, patterns, args.max_chars)
    instruction_tokens = estimate_tokens(instruction_text())
    evidence_budget = max(200, args.budget - instruction_tokens)
    selected = select_candidates(candidates, evidence_budget, args.max_snippets, args.per_file)
    evidence_text = selected_evidence_text(selected)
    selected_tokens = estimate_tokens(evidence_text)
    total_tokens = instruction_tokens + selected_tokens

    if args.evidence_output:
        write_evidence(args.evidence_output, args.goal, selected)

    selected_scores = [int(item["score"]) for item in selected]
    payload: dict[str, Any] = {
        "goal": args.goal,
        "budget_tokens": args.budget,
        "patterns": patterns,
        "source_paths": [str(path) for path in args.paths],
        "candidate_count": len(candidates),
        "selected_snippet_count": len(selected),
        "instruction_tokens": instruction_tokens,
        "evidence_budget_tokens": evidence_budget,
        "selected_evidence_tokens": selected_tokens,
        "estimated_review_total_tokens": total_tokens,
        "selected_score_average": round(mean(selected_scores), 1) if selected_scores else 0,
        "selected_evidence": selected,
        "commands": build_commands(args, selected),
        "note": "Rough estimate for planning, not provider billing.",
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_markdown(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
