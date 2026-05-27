# Source Guide

Use the smallest source set that can answer the question.

## Preferred Source Order

1. Current conversation.
2. User-supplied chat exports or paths.
3. High-signal local memory summaries, especially `~/.codex/memories/MEMORY.md`.
4. Specific rollout summaries named by `MEMORY.md`.
5. Broader session logs only when the previous sources are too thin.

## Local Codex Sources

- `~/.codex/memories/MEMORY.md`: concise summaries of repeated user preferences and prior task lessons.
- `~/.codex/memories/rollout_summaries/`: per-session summaries with evidence snippets.
- `~/.codex/sessions/`: JSONL session logs. These can be large and private; sample narrowly.

## Helper Usage

Collect candidate evidence from Markdown:

```bash
python3 scripts/collect_user_prompts.py ~/.codex/memories/MEMORY.md --query "when the user,prompt,review,subagents" --limit 50
```

Collect from multiple paths:

```bash
python3 scripts/collect_user_prompts.py path/to/export.jsonl path/to/chat.md --limit 30 --max-chars 360
```

The helper supports directories and scans `.md`, `.txt`, and `.jsonl` files. It sorts directory files by modified time, newest first.

## Evidence Standards

- Prefer recurring patterns over one-off wording.
- For each rule, try to identify at least two supporting examples or one strong explicit correction.
- If evidence is thin, label the result as a hypothesis.
- Distinguish "the user often wants this" from "this particular task needs this".

## Privacy Handling

- Do not publish raw examples from private chats.
- Redact personal names, emails, URLs, tokens, and customer data unless the user explicitly wants them included.
- Keep examples short and synthetic when producing open-source documentation.
