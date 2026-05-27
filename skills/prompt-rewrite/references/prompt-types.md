# Prompt Types

Use the relevant section only. Keep the final prompt proportional to the task.

## Code Change

Require:

- Repo/path and feature or bug target.
- Files or modules to inspect first, if known.
- Scope boundary: small PR, no unrelated refactors, no dependency changes unless needed.
- Verification: tests, lint, typecheck, build, browser smoke, or explicit "explain if not run".
- Git/PR expectations if the user asked to ship.

Template:

```text
Work in [repo/path]. Implement [change]. First inspect [files/areas] and follow existing patterns. Keep the change scoped to [boundary]. Do not [forbidden actions]. Verify with [commands/checks], and report changed files plus any tests you could not run.
```

## Bug Investigation

Require:

- Symptom, expected behavior, reproduction clue, logs/errors if available.
- Instruction to find root cause before patching.
- Evidence request: failing test, reproduced behavior, stack trace, or code path.
- Fix boundary and regression check.

## Code Review Or Audit

Require:

- Review target: diff, branch, PR, file, feature, live flow, or repo.
- Findings-first output, ordered by severity.
- Evidence: file/line references, reproduction steps, screenshots, logs, or commands.
- Explicit instruction not to rewrite code unless asked.

Template:

```text
Review [target] for bugs, regressions, security/privacy risk, UX issues, and missing tests. Lead with findings ordered by severity, each with evidence and a concrete fix direction. Keep summary brief and do not make code changes.
```

## Product Or UX Audit

Require:

- Audience and job-to-be-done.
- Real surface to inspect: URL, route, screenshot, branch, local app, or product docs.
- Workflow path to trace end to end.
- Findings-first output with reproduction/evidence.
- Guard against generic feature brainstorming.

## Browser QA

Require:

- URL or local target.
- Viewports, credentials/test login path if relevant.
- Interactions to perform.
- Evidence: screenshots, console errors, network failures, overlap/layout issues.
- Boundary: do not submit forms, spend money, or modify production unless allowed.

## Research

Require:

- Research question and decision the research should support.
- Source types and freshness needs.
- Citation requirements.
- Comparison dimensions.
- Output artifact: memo, table, recommendation, brief, or source list.

## Planning Or Spec

Require:

- Product goal and current reality sources.
- Constraints, non-goals, and staged rollout.
- Deliverable: implementation plan, task breakdown, PR sequence, Linear issues, or Notion doc.
- Ask to map against existing capability before inventing new systems.

## Data, Spreadsheet, Or Document Work

Require:

- Input files/sheets/docs and exact output artifact.
- Column/schema/format expectations.
- Data-cleaning rules.
- Verification: row counts, formulas checked, rendered export, or spot checks.

## Automation Or Reminder

Require:

- Task, cadence/date/time/timezone, destination, and stop condition.
- Whether it should continue this thread or run detached.
- Output expectation for each run.

## Image Or Design Generation

Require:

- Subject, use case, style, composition, aspect ratio, must-include and must-avoid details.
- For edits, specify only the delta and what must remain unchanged.
- Avoid vague mood-only prompts when the user needs a concrete asset.

## Agent Handoff

Require:

- Starting state, exact goal, files/links to inspect, decisions already made, constraints, verification, and final report shape.
- Include "do not restart from scratch" when continuing prior work.

## Skill Creation

Require:

- Skill name or working name.
- Trigger scenarios.
- Concrete examples of user requests.
- Reusable resources: references, scripts, assets.
- Validation command and forward-test prompt.
- Open-source packaging expectations if relevant.
