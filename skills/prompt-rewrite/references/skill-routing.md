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

## Skill Families

Some installed skills are packs with many subskills. Treat a family as any group that shares a plugin namespace, nested pack path, related name pattern, or explicit family marker in the skill metadata. Do not collapse a family to its root skill when a visible subskill matches better.

For any skill family:

- Prefer the narrowest visible child skill that matches the outcome.
- Use the root skill only for generic work covered by the whole family.
- Mention a second child skill only for a distinct phase, such as QA first and shipping after validation.
- Preserve namespace prefixes exactly, such as `$github:yeet`, `$vercel:nextjs`, or `$browser:control-in-app-browser`.
- Default to one primary skill invocation. Add at most one follow-up skill unless the user explicitly asks for a multi-stage workflow.
- If several child skills are plausible, write a decision rule instead of a menu, such as `Start with $vercel:investigation-mode; switch to $vercel:deployments-cicd only if the evidence is deployment configuration rather than app code`.

Examples:

- Use `$gstack` or `$browse` for generic browser QA, site dogfooding, screenshots, and live UI checks.
- Use `$qa` when the user wants systematic QA and fixes in the codebase.
- Use `$qa-only` when the user wants a report and no code changes.
- Use `$design-review`, `$critique`, `$polish`, or similar visible design skills for visual UX, spacing, hierarchy, and AI-slop review.
- Use `$investigate` for debugging and root-cause work.
- Use `$review` for pre-landing code review.
- Use `$ship` for the full ship workflow when the user says ship, create PR, push, or publish and the gstack ship skill is visible.
- Use `$github:yeet` when the task is only to publish already-scoped local changes through GitHub.
- Use `$github:gh-fix-ci` for GitHub Actions failures instead of the broader GitHub publishing skill.
- Use `$canary` or `$land-and-deploy` for post-deploy monitoring or landing/deploying an existing PR.

## Optional Local Scan

If the current context does not show installed skills and local filesystem access is appropriate, run:

```bash
python3 scripts/list_installed_skills.py --include-plugin-cache --intent "browser-qa,qa-fix,qa-report,design-review,publish-pr,debug,code-review,deploy-canary" --query "qa,qa-only,design-review,ship,yeet,browser,github,vercel,investigate,review,deploy"
```

Use the output as a candidate map only. The current Codex session may expose plugin skills that are not present in ordinary skill folders, and local folders may contain skills that are not active in this session.

The scanner ranks exact invocation/name matches above broad description matches, infers plugin prefixes from the plugin cache, and labels likely skill families and intents. Family labels come from plugin namespaces, nested pack paths, related name patterns, and trailing metadata markers such as `(gstack)`.

## Example Rewrite

Rough:

```text
check the live ux and make a small pr
```

Improved when `$gstack` and `$github:yeet` are visible:

```text
Use $qa to inspect the live UX flow at [URL] on mobile and desktop, report concrete findings, and implement only the smallest PR-worthy fixes. If visual hierarchy, spacing, or UI polish is the main concern and `$design-review` is visible, use `$design-review` instead.

After validation passes, use $ship if the full gstack ship workflow is visible. Otherwise use $github:yeet to publish a draft PR with the changed files, verification commands, screenshots/evidence, and remaining risks.
```

Improved when no matching skills are visible:

```text
Inspect the live UX flow at [URL] with the available browser QA tooling, if installed. Lead with concrete findings, reproduction steps, screenshots if useful, and severity. Keep fixes to the smallest PR-worthy slice and do not redesign unrelated surfaces.

If the fixes are implemented and validation passes, publish a draft PR using the available GitHub workflow.
```
