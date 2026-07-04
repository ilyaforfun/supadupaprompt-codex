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

Install both skills into your local Codex skills directory:

```bash
python3 scripts/install.py
```

Preview the install first, choose a custom skills directory, or refresh an existing install:

```bash
python3 scripts/install.py --dry-run
python3 scripts/install.py --skills-dir ~/.codex/skills
python3 scripts/install.py --force
```

Then start a fresh Codex session so the skills are discovered.

Manual install still works:

```bash
cp -R skills/prompt-rewrite ~/.codex/skills/
cp -R skills/prompt-profile-review ~/.codex/skills/
```

Check the local install:

```bash
python3 skills/prompt-rewrite/scripts/supaprompt_doctor.py
```

## Quick Demo

Rough ask:

```text
qa the onboarding flow in browser on mobile and desktop, give bugs with proof, don't fix yet
```

Rewritten shape:

```text
You are Codex. QA the onboarding flow in a real browser and produce a report only. Do not make code changes or attempt fixes.

Target:
- App URL: <APP_URL>
- If no URL is available, ask for it before testing instead of inventing one.

Coverage:
- Desktop viewport, around 1440x900.
- Mobile viewport, around 390x844.
- First-run onboarding path, returning-user path if reachable, form validation, navigation/back behavior, loading states, error states, and completion/success state.

For every bug or concern, include severity, reproduction steps, expected vs actual behavior, screenshot or visual proof when possible, console/network evidence when present, and the viewport where it happened.

Output a readiness summary first, then findings ordered by severity, then untested areas. Stop after the QA report.
```

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

Run the local health check:

```bash
python3 skills/prompt-rewrite/scripts/supaprompt_doctor.py
```

Test the profile helper:

```bash
python3 skills/prompt-profile-review/scripts/collect_user_prompts.py ~/.codex/memories/MEMORY.md --query "when the user,prompt,subagents" --limit 10
```

Plan narrow profile-review evidence:

```bash
python3 skills/prompt-profile-review/scripts/plan_review_evidence.py ~/.codex/memories/MEMORY.md --goal "review how I prompt for PR/dogfood work" --budget 5000
```

Estimate token use by mode:

```bash
python3 skills/prompt-profile-review/scripts/estimate_review_tokens.py --evidence-file ~/.codex/memories/MEMORY.md
python3 skills/prompt-rewrite/scripts/estimate_rewrite_tokens.py --fixture skills/prompt-rewrite/fixtures/review_handoff_rewrite.json
```

List locally installed skills for routing:

```bash
python3 skills/prompt-rewrite/scripts/list_installed_skills.py --include-plugin-cache --intent "browser-qa,qa-fix,qa-report,design-review,publish-pr,debug,code-review,deploy-canary" --query "qa,qa-only,design-review,ship,yeet,browser,github,vercel,investigate,review,deploy"
```

Validate dogfood fixtures:

```bash
python3 skills/prompt-rewrite/scripts/check_dogfood_fixtures.py
```

Plan manual forward tests:

```bash
python3 skills/prompt-rewrite/scripts/plan_forward_tests.py
```

Create and score a private forward-test results file:

```bash
python3 skills/prompt-rewrite/scripts/score_forward_tests.py --init-results /tmp/supaprompt-forward-results.json
# Run each agent_prompt in a clean thread, then fill agent_output and rubric scores.
python3 skills/prompt-rewrite/scripts/score_forward_tests.py --results /tmp/supaprompt-forward-results.json
```

Generate a dogfood loop report after a PR:

```bash
python3 skills/prompt-rewrite/scripts/dogfood_report.py --pr 9 --evidence-file ~/.codex/memories/MEMORY.md --scan-skills
```

Include scored forward-test results in the report:

```bash
python3 skills/prompt-rewrite/scripts/dogfood_report.py --forward-test-results /tmp/supaprompt-forward-results.json
```

Fixtures cover paired review-to-rewrite, code change, PR review, browser QA, research, design audit, profile-review narrowing, dogfood loops, and rewrite-only/no-execution prompts.

## License

MIT
