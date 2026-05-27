# supadupaprompt-codex

supadupaprompt-codex is an open-source Codex skill pack for turning rough intent into execution-ready AI prompts.

- `prompt-rewrite`: rewrite a rough ask into a copy-paste prompt for coding agents, research agents, chat models, browser agents, design tools, and handoffs.
- `prompt-profile-review`: review prior chats or local memory to infer a user's prompting style, recurring corrections, and rewrite rules.

supadupaprompt-codex is intentionally lightweight. It does not try to become a full prompt-optimization platform or an always-on hook. You invoke the skills when you want a better prompt or when you want to tune the rewriter to how someone actually works.

`prompt-rewrite` can reference other installed skills natively. It checks the current Codex skill context first, and can optionally scan local skill folders, so rewritten prompts can say things like `Use $gstack for browser QA` or `Use $github:yeet for publishing` only when those skills are available.

## Why This Exists

There are already strong prompt-improvement projects:

- [severity1/claude-code-prompt-improver](https://github.com/severity1/claude-code-prompt-improver) uses a Claude Code hook to evaluate vague prompts and ask clarifying questions.
- [EdwinjJ1/chiron-prompt](https://github.com/EdwinjJ1/chiron-prompt) turns rough terminal requests into repo-aware execution prompts.
- [ckelsoe/prompt-architect](https://github.com/ckelsoe/prompt-architect) applies many prompt-engineering frameworks across prompt intents.
- [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master) focuses on generating optimized prompts for specific AI tools.
- [conversation-analyzer](https://claude-plugins.dev/skills/%40mhattingpete/claude-skills-marketplace/conversation-analyzer) reviews conversation history for usage patterns and workflow improvements.
- [linshenkx/prompt-optimizer](https://github.com/linshenkx/prompt-optimizer) provides a larger app, extension, Docker, and MCP surface for optimizing reusable prompt assets.
- [promptfoo](https://github.com/promptfoo/promptfoo) handles prompt and agent evaluation rather than one-off prompt rewriting.

supadupaprompt-codex focuses on a different wedge: Codex-native prompt rewriting that learns from the user's actual prompting habits, keeps their useful directness, and adds only the missing structure needed for the task type. It is a local, transparent prompt compiler for agent execution, not a generic prompt-prettifier.

## Install

Copy either or both skill folders into your Codex skills directory:

```bash
cp -R skills/prompt-rewrite ~/.codex/skills/
cp -R skills/prompt-profile-review ~/.codex/skills/
```

Then start a fresh Codex session so the skills are discovered.

## Usage

Rewrite a rough prompt:

```text
Use $prompt-rewrite to improve this prompt for Codex:
check if this app is ready and create PR if yes
```

Create a private prompt profile from local history:

```text
Use $prompt-profile-review to review my local Codex memories and summarize how I prompt, what agents often miss, and what future prompt rewrites should preserve.
```

Use both together:

```text
Use $prompt-profile-review on the supplied chat export, then use $prompt-rewrite to rewrite this rough request using that profile.
```

## What Makes A Good Rewrite

A strong rewrite usually adds:

- The exact outcome.
- The context or files/surfaces to inspect first.
- Scope boundaries and approval gates.
- Tool expectations such as browser checks, subagents, citations, tests, or live verification.
- A clear output contract.
- Done criteria.

It should not add ceremony for its own sake. If the rough ask is already clear, the skill should keep it short.

## Privacy

`prompt-profile-review` is designed for local evidence. It should inspect local chat exports, memory summaries, or session logs without publishing raw private transcripts. Open-source examples should be synthetic or anonymized.

## Development

Validate the skills with the system skill validator:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/prompt-rewrite
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/prompt-profile-review
```

Test the profile helper:

```bash
python3 skills/prompt-profile-review/scripts/collect_user_prompts.py ~/.codex/memories/MEMORY.md --query "when the user,prompt,subagents" --limit 10
```

List locally installed skills for routing:

```bash
python3 skills/prompt-rewrite/scripts/list_installed_skills.py --include-plugin-cache --query "browser,github,design,skill"
```

## License

MIT
