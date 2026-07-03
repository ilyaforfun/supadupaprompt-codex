---
name: prompt-profile-review
description: Review prior chats, exported conversations, local Codex memory, or session logs to infer a user's prompting style and produce a reusable prompt profile. Use when the user asks to learn how they prompt, review chat history, improve future prompts from prior behavior, create a prompt profile, tune a prompt-rewriter to their style, or find recurring prompting failure modes.
---

# Supadupaprompt Profile Review

## Overview

Use supadupaprompt-codex to turn prior conversations into a compact private profile that helps future prompt rewrites preserve the user's real intent, working style, and correction patterns.

## Workflow

1. Define the review scope.
   - Prefer sources the user named explicitly: current thread, exported chats, local memory files, session logs, or a supplied folder.
   - When the source set is broad, first plan a narrow evidence set with `scripts/plan_review_evidence.py`.
   - If no source is named, inspect likely local sources only when they are available and clearly relevant, such as `~/.codex/memories/MEMORY.md`, `~/.codex/memories/rollout_summaries/`, or `~/.codex/sessions/`.
   - Broad-scan all memories or sessions only when the user asks for full recalibration, the narrow plan is too thin, or the target pattern is still unclear.
   - Keep the review local. Do not send private chat text to external services.

2. Gather evidence.
   - Start with current conversation and high-signal memory summaries before broad log scans.
   - Track the source set, whether `scripts/plan_review_evidence.py` or a manual equivalent was used, and any broad-vs-narrow token estimates available.
   - Use `scripts/collect_user_prompts.py` for a first pass over local Markdown or JSONL sources when there are many files.
   - Treat script output as candidate evidence. Manually sample sources around important claims before finalizing.
   - Quote minimally. Prefer paraphrase and short snippets.

3. Classify the user's prompting patterns.
   - Goal shape: what outcomes they ask for, and how they frame success.
   - Autonomy: when they expect direct execution, planning, subagents, browser testing, PRs, or verification.
   - Context style: how they supply prior decisions, repo paths, artifacts, examples, or constraints.
   - Correction style: recurring phrases that indicate a boundary, such as "real product", "not random", "small PR", "use subagents", or "check live".
   - Failure modes: what agents tend to overbuild, under-verify, miss, or answer too generically.
   - Prompt opportunities: missing details that would improve first-pass results without slowing the user down.

4. Produce a prompt profile.
   - Use the schema in `references/profile-schema.md`.
   - Include a compact `Evidence Budget` block before the profile whenever the user asks to keep review cheap/focused, avoid scanning everything, or review broad local sources.
   - Separate observations from recommended rewrite rules.
   - Include a short "preserve" section so future prompt-rewriters do not sand away the user's useful directness.
   - Include 3-6 before/after examples based on patterns, not long private transcripts.

5. Hand off to prompt rewriting.
   - When the user wants both review and rewriting, include a compact `Prompt-Rewrite Handoff` block with the 5-8 active rules the rewriter should apply.
   - If the user also wants better prompts, tell them to use `$prompt-rewrite` with this profile.
   - Do not persist the profile to disk unless the user asks for a file or gives an explicit destination.

## Evidence Collection Helper

Plan a narrow evidence set before scanning broad sources:

```bash
python3 scripts/plan_review_evidence.py ~/.codex/memories/MEMORY.md --goal "review how I prompt for PR/dogfood work" --budget 5000
```

Run the helper from this skill directory or pass its absolute path:

```bash
python3 scripts/collect_user_prompts.py ~/.codex/memories/MEMORY.md --query "when the user,prompt,subagents" --limit 40
```

For broader local logs:

```bash
python3 scripts/collect_user_prompts.py ~/.codex/sessions ~/.codex/memories/rollout_summaries --limit 80
```

The helper prints candidate user-prompt evidence with source paths and line numbers. Use it to find patterns quickly, then inspect the strongest sources directly.

## Token Accounting

Estimate review-mode token use before scanning broad sources. Prefer the evidence planner when the source could exceed the useful budget:

```bash
python3 scripts/estimate_review_tokens.py --evidence-file ~/.codex/memories/MEMORY.md
```

Use the estimate and evidence plan to choose narrower sources, lower `--limit`, or summarize evidence before handing it to `$prompt-rewrite`. Treat counts as planning guidance, not billing truth.

When producing the final profile after a focused review, include:

```text
Evidence Budget:
- Source set: [current thread, MEMORY.md, selected rollout summaries, supplied export, etc.]
- Narrowing: [planner command used/recommended, or manual equivalent]
- Token estimate: [broad estimate vs narrow estimate, or "not measured"]
- Scan boundary: [what was intentionally skipped and when to broaden]
```

## Privacy Rules

- Keep raw chat evidence local by default.
- Do not include secrets, account details, personal contact data, or long private excerpts in the final profile.
- If the user wants an open-source example, synthesize anonymized examples instead of publishing their real chats.
- If a source contains sensitive material unrelated to prompting behavior, ignore it.

## References

- Read `references/profile-schema.md` before writing the final profile.
- Read `references/source-guide.md` when deciding where to look or how to use the helper script.
