# Skill Routing

Reference installed skills natively when they reduce ambiguity. Keep routing narrow: one primary skill, at most one follow-up for a distinct phase.

## Rules

1. Use current context first.
   - Prefer exact visible invocations, including plugin prefixes such as `$github:yeet`.
   - Include only task-relevant skills; never summarize the full inventory unless asked.

2. Never invent a skill.
   - Visible skill: `Use $skill-name ...`.
   - Likely but not visible: `Use the available browser QA skill, if installed`.
   - External prompt target: mention that skill names are environment-specific.

3. Pick the narrowest capability.
   - Browser/live UI: visible browser QA skill such as `$gstack`, `$qa`, `$browse`, or `$browser:control-in-app-browser`.
   - Design/UI quality: visible design skill such as `$design-review`, `$critique`, `$polish`, `$arrange`, or `$typeset`.
   - GitHub/PR: visible GitHub skill such as `$github:yeet`, `$github:gh-fix-ci`, `$github:gh-address-comments`, or `$ship`.
   - Skill work, docs, sheets, slides, automations: use the matching visible specialist skill.

4. Preserve scope.
   - Skill references should reduce ambiguity, not expand work.
   - Omit a skill if it would trigger extra work the user did not ask for.
   - Write contextual invocations: `Use $qa to test onboarding at 375px and 1440px, then report findings first.`

## Families

Treat a family as skills sharing a plugin namespace, nested pack path, related name pattern, or explicit metadata marker. Do not collapse to the root when a child skill matches better.

- Prefer the narrowest child skill for the outcome.
- Use the root skill only for generic family work.
- Preserve namespace prefixes exactly.
- Add a second child skill only for a distinct phase, such as QA then shipping.
- If several children are plausible, write a decision rule instead of a menu.

## Local Scan

If the current context does not expose installed skills and local filesystem access is appropriate, run:

```bash
python3 scripts/list_installed_skills.py --include-plugin-cache --intent "browser-qa,qa-fix,qa-report,design-review,publish-pr,debug,code-review,deploy-canary" --query "qa,qa-only,design-review,ship,yeet,browser,github,vercel,investigate,review,deploy"
```

Use the output as a candidate map only. The scanner caches snapshots at `~/.cache/supadupaprompt-codex/installed-skills.json`; use `--refresh-cache` after installing/removing skills and `--no-cache` when debugging scanner behavior.

Read `skill-routing-examples.md` only when routing behavior is ambiguous, examples are requested, or fixture output fails.
