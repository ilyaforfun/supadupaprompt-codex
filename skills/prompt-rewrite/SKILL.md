---
name: prompt-rewrite
description: Rewrite rough, vague, or under-specified user requests into stronger copy-paste prompts for coding agents, research agents, chat models, browser agents, design tools, or other AI systems. Use when the user asks to improve a prompt, make a better prompt, prepare a prompt for another tool, convert notes into an agent-ready request, add missing context/constraints/verification, or adapt prompts by type such as coding, review, research, UX audit, browser QA, data work, image generation, automation, or handoff.
---

# Supadupaprompt Rewrite

## Overview

Use supadupaprompt-codex to transform a rough ask into a prompt that gives an AI system a clear goal, useful context, scope boundaries, verification gates, and an output contract.

## Core Workflow

1. Preserve the user's intent.
   - Keep the actual goal, product names, repo paths, constraints, tone, and urgency.
   - Do not turn a small ask into a large project.
   - Do not solve the underlying task unless the user explicitly asks for execution.

2. Identify the target executor.
   - Use the named tool or model when provided: Codex, Claude Code, ChatGPT, Cursor, Replit, v0, browser agent, image model, research agent, etc.
   - If no target is named, default to the current agent/chat context.
   - Ask at most one target-tool question only when the rewrite would materially differ by tool.

3. Classify the prompt type.
   - Use `references/prompt-types.md` when the prompt needs type-specific structure.
   - Common types: code change, bug investigation, code review, product/UX audit, browser QA, research, planning, data/document work, automation, image/design generation, handoff, or skill creation.

4. Build an available skill map.
   - Check the current session's available skills list before suggesting skill invocations.
   - Mention exact `$skill-name` invocations only when that skill is installed or visible in the current context.
   - Prefer task-relevant skills over generic wording: browser QA, GitHub PRs, design review, docs, sheets, automations, research, or repo-specific workflows.
   - If the current context does not expose the installed skill list and local filesystem access is appropriate, use `scripts/list_installed_skills.py` to scan likely local skill roots.
   - Read `references/skill-routing.md` for routing rules and examples.

5. Add missing structure.
   - Goal: the exact outcome.
   - Context: sources, files, product surface, prior decisions, or examples the agent should inspect.
   - Scope: what to touch and what to leave alone.
   - Method: whether to use tools, installed skills, subagents, browser checks, citations, tests, or live verification.
   - Constraints: privacy, safety, no destructive actions, no overbuilding, no unrelated refactors.
   - Output contract: findings first, copyable artifact, PR summary, table, checklist, or concise answer.
   - Done criteria: how the agent knows it is finished.

6. Personalize when a profile exists.
   - If a `$prompt-profile-review` output or local prompt profile is available, apply it.
   - Preserve useful directness and autonomy preferences instead of making every prompt formal.
   - Read `references/personalization.md` for profile application rules.

7. Decide whether to ask or assume.
   - Ask up to 3 concise questions only when missing information could cause destructive work, wrong-tool output, privacy exposure, production impact, or a large wrong turn.
   - Otherwise, write the prompt with explicit assumptions.

## Output Format

Default response:

````markdown
**Improved Prompt**

```text
[copyable prompt]
```

**What Changed**
- [short reason]
- [short reason]

**Assumptions**
- [only if relevant]
````

When the user asks for "just the prompt" or "copy-paste only", output only one fenced prompt block and put nothing after it.

## Quality Bar

Before finalizing, score the rewrite against `references/quality-rubric.md`.

The prompt is ready when it:

- Names the intended outcome and executor.
- Gives the agent enough context to start correctly.
- Defines scope and stop conditions.
- States how to verify success.
- Protects against the most likely failure mode for that prompt type.
- Stays no longer than needed.

## Token Accounting And Dogfood Fixtures

Estimate rewrite-mode token use when the prompt includes a profile, handoff, or installed-skill map:

```bash
python3 scripts/estimate_rewrite_tokens.py --prompt-text "check this app" --profile-file profile.md
```

Validate bundled dogfood fixtures after changing review, handoff, personalization, or skill routing behavior:

```bash
python3 scripts/check_dogfood_fixtures.py
```

Use fixture failures as regression signals, then inspect the fixture before changing expected behavior. The fixture suite covers paired review-to-rewrite, code change, PR review, browser QA, research, design audit, profile-review narrowing, dogfood loops, and rewrite-only/no-execution prompts.

For iterative PR-to-dogfood-to-next-build loops on supadupaprompt itself, read `references/dogfood-loop.md` and start with:

```bash
python3 scripts/dogfood_report.py --pr <number> --evidence-file ~/.codex/memories/MEMORY.md --scan-skills
```

## References

- `references/prompt-types.md`: type-specific fields and examples.
- `references/quality-rubric.md`: final checklist for prompt quality.
- `references/personalization.md`: how to apply a user prompt profile.
- `references/skill-routing.md`: how to reference installed skills natively.
- `references/skill-routing-examples.md`: routing examples; read only when routing behavior is ambiguous, examples are requested, or fixture output fails.
- `references/dogfood-loop.md`: iterative PR-to-dogfood-to-next-build workflow for improving this skill pack.
- `references/examples.md`: compact before/after examples for common rewrites.
