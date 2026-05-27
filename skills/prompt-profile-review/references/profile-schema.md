# Prompt Profile Schema

Use this schema for the final output. Keep it compact enough to paste into `$prompt-rewrite`.

## 1. Prompting Profile

- **Default intent:** What the user usually wants the agent to do.
- **Preferred autonomy:** When to execute directly, when to plan, when to ask.
- **Evidence standard:** What counts as "checked" or "real" for this user.
- **Scope preference:** How tightly or broadly to interpret requests.
- **Communication style:** Directness, density, tone, update cadence, and final-answer shape.

## 2. Preserve

List behaviors the prompt-rewriter should keep, even if the user's draft is rough:

- Strong verbs and direct goals.
- Real workspace paths, product names, and constraints.
- Explicit requests for subagents, browser checks, current-state verification, PRs, or shipping.
- Informal wording when it carries intent.

## 3. Strengthen

List missing details that should usually be added:

- Target artifact: code change, review, research memo, PR, plan, prompt, doc, spreadsheet, or live QA report.
- Scope boundary: files, repos, surfaces, data sources, or "small PR" limits.
- Verification gate: tests, browser screenshots, live endpoint checks, citations, line references, or before/after examples.
- Stop condition: when the agent should ask before continuing.
- Output contract: findings-first review, copyable prompt, commit/PR summary, or concise recommendation.

## 4. Ask Before Assuming

Name only the decisions that are risky to infer:

- Destructive changes.
- External publication or sharing private chat evidence.
- Live production actions.
- Ambiguous target tool when prompt style depends on the tool.

## 5. Rewrite Defaults

Write 5-10 rules future prompt-rewriters should apply automatically.

Example:

```text
When the user asks for review/audit, rewrite the prompt so findings come first and verification evidence is required.
```

## 6. Example Rewrites

Provide 3-6 anonymized examples:

```text
Rough: "check this flow"
Improved: "Review the live product flow at [URL/path]. Use the browser, trace the main workflow end to end, and report concrete UX or behavior issues first with reproduction steps and evidence. Do not propose new features until current-flow issues are listed."
Why: Adds source, method, output order, and a guard against generic ideation.
```
