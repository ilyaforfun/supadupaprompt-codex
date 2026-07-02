# Skill Routing

Use installed skills as native capabilities when rewriting prompts. The goal is to produce prompts that say "use the right local skill" instead of generic tool instructions.

## Routing Rules

1. Build a skill map from the current context first.
   - Use exact names from the available skills list, including plugin prefixes when present.
   - Include only skills that are relevant to the user's task.
   - Do not expose or summarize the full installed skill inventory unless the user asks.

2. Never invent a skill.
   - If a skill is visible, write the exact invocation: `Use $skill-name ...`.
   - If a capability is likely but not visible, write: `Use the available browser QA skill, if installed`.
   - If the prompt will be used outside the current Codex environment, explain that skill names are environment-specific.

3. Prefer specific skills over broad labels.
   - Browser/live UI: `$gstack`, `$qa`, `$browse`, `$live-workflow-audit`, `$browser:browser`, or similar visible browser skill.
   - Design/UI quality: `$impeccable`, `$critique`, `$polish`, `$arrange`, `$typeset`, `$normalize`, or similar visible design skill.
   - GitHub/PR: `$github:yeet`, `$github:gh-fix-ci`, `$github:gh-address-comments`, or similar visible GitHub skill.
   - Skill work: `$skill-creator`, `$skill-installer`, or similar visible skill tooling.
   - Docs/sheets/slides: visible document, spreadsheet, or presentation skills.
   - Automations/reminders: visible automation tooling or the native Codex automation tool.

4. Keep the invocation contextual.
   - Good: `Use $gstack to test the onboarding flow at 375px and 1440px, then report findings first.`
   - Weak: `Use $gstack.`
   - Good: `Use $github:yeet to publish the scoped branch as a draft PR after validation passes.`
   - Weak: `Use GitHub.`

5. Preserve user intent and scope.
   - Skill references should reduce ambiguity, not expand the job.
   - Do not add multiple skill invocations when one direct skill covers the task.
   - If a skill would trigger extra work the user did not ask for, make it optional or omit it.

## Optional Local Scan

If the current context does not show installed skills and local filesystem access is appropriate, run:

```bash
python3 scripts/list_installed_skills.py --include-plugin-cache --category "browser,github,design,skill" --query "gstack,yeet,browser,github,design,skill"
```

Use the output as a candidate map only. The current Codex session may expose plugin skills that are not present in ordinary skill folders, and local folders may contain skills that are not active in this session.

The scanner ranks exact invocation/name matches above broad description matches and infers plugin prefixes from the plugin cache, such as `$github:yeet` or `$browser:browser`, when possible.

## Example Rewrite

Rough:

```text
check the live ux and make a small pr
```

Improved when `$gstack` and `$github:yeet` are visible:

```text
Use $gstack to inspect the live UX flow at [URL] on mobile and desktop. Lead with concrete findings, reproduction steps, screenshots if useful, and severity. Keep fixes to the smallest PR-worthy slice and do not redesign unrelated surfaces.

If the fixes are implemented and validation passes, use $github:yeet to publish a draft PR with the changed files, verification commands, and remaining risks.
```

Improved when no matching skills are visible:

```text
Inspect the live UX flow at [URL] with the available browser QA tooling, if installed. Lead with concrete findings, reproduction steps, screenshots if useful, and severity. Keep fixes to the smallest PR-worthy slice and do not redesign unrelated surfaces.

If the fixes are implemented and validation passes, publish a draft PR using the available GitHub workflow.
```
