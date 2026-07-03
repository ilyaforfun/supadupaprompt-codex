# Skill Routing Examples

Use this reference only when examples are needed. Keep normal rewrites on `skill-routing.md`.

## Family Choices

- Use `$gstack` or `$browse` for generic browser QA, site dogfooding, screenshots, and live UI checks.
- Use `$qa` when the user wants systematic QA and fixes in the codebase.
- Use `$qa-only` when the user wants a report and no code changes.
- Use `$design-review`, `$critique`, `$polish`, or similar visible design skills for visual UX, spacing, hierarchy, and AI-slop review.
- Use `$investigate` for debugging and root-cause work.
- Use `$review` for pre-landing code review.
- Use `$ship` for full gstack shipping when the user says ship, create PR, push, or publish and the skill is visible.
- Use `$github:yeet` when the task is only to publish already-scoped local changes through GitHub.
- Use `$github:gh-fix-ci` for GitHub Actions failures.
- Use `$canary` or `$land-and-deploy` for post-deploy monitoring or landing/deploying an existing PR.

## Example Rewrite

Rough:

```text
check the live ux and make a small pr
```

Improved when `$qa`, `$design-review`, and `$ship` are visible:

```text
Use $qa to inspect the live UX flow at [URL] on mobile and desktop, report concrete findings, and implement only the smallest PR-worthy fixes. If visual hierarchy, spacing, or UI polish is the main concern and `$design-review` is visible, use `$design-review` instead.

After validation passes, use $ship to publish the branch with changed files, verification commands, screenshots/evidence, and remaining risks.
```

Improved when no matching skills are visible:

```text
Inspect the live UX flow at [URL] with the available browser QA tooling, if installed. Lead with concrete findings, reproduction steps, screenshots if useful, and severity. Keep fixes to the smallest PR-worthy slice and do not redesign unrelated surfaces.

If fixes are implemented and validation passes, publish a draft PR using the available GitHub workflow.
```
