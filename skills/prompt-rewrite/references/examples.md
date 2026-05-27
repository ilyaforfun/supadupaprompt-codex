# Examples

Use these as patterns, not fixed templates.

## Readiness And PR

Rough:

```text
check if this app is ready and create pr if yes
```

Improved:

```text
Work in the current app repository. Determine whether the current changes are ready for a pull request.

First confirm the repo root, current branch, git status, intended base branch, and available verification commands from the project docs or package scripts. Inspect the actual changed files and the relevant app surface before deciding.

Verify readiness with the repo's standard checks, including lint, typecheck, tests, build, and a quick local browser smoke test of the core user flow if this is a web app. Check for console errors, broken routes, layout issues, and obvious regressions. Do not make unrelated refactors or expand the scope.

If the app is ready, create a clean branch if needed, commit only the intended changes, push the branch, and create a pull request with a concise summary and the verification performed.

If the app is not ready, do not create a PR. Report blocking issues first with file/line references, failed command output, or reproduction steps, then list the smallest fixes needed to make it ready.
```

Why it works: turns readiness into evidence, defines the PR gate, and prevents shipping when verification fails.

## Real Product Mapping

Rough:

```text
analyze those tasks against the real product, not random
```

Improved:

```text
Inspect the current product before proposing work. Review the relevant routes, components, docs, and data flows, then map each proposed task to existing product capability.

For each task, report:
- What already exists and where.
- The actual gap.
- The smallest useful implementation.
- What should not be built because it duplicates or bypasses current behavior.

Do not invent a parallel workflow unless the existing product cannot support the goal. Lead with concrete findings, not generic brainstorming.
```

Why it works: forces current-state inspection and converts a broad correction into a product-mapping workflow.

## Privacy Or Storage Copy

Rough:

```text
check the wording, we don't store scoring, just summary/contact/quotes
```

Improved:

```text
Audit both the user-facing copy and the actual persistence path. Verify the relevant UI text, API route, storage helper, database schema, and tests before changing wording.

If the backend stores fields the copy says it does not store, fix the behavior or flag the contract mismatch; do not only edit copy. Report the verified stored data categories and update the wording so it matches the real backend contract.
```

Why it works: protects trust-boundary work from becoming cosmetic.

## Live UX Review

Rough:

```text
check this flow
```

Improved:

```text
Review the live product flow at [URL or local route]. Use the browser to trace the main user workflow end to end at desktop and mobile widths. Report concrete UX or behavior issues first with reproduction steps, screenshots if useful, console/network errors, and severity.

Do not propose new features until current-flow issues are listed. Include a short summary only after the findings.
```

Why it works: defines the surface, method, evidence, and output order.
