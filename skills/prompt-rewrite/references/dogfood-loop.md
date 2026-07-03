# Dogfood Loop

Use this when improving supadupaprompt-codex itself after a PR, when a user asks to dogfood the skills, or when the next build should be chosen from real usage.

## Loop Shape

1. Start from the real repository state.
   - Fetch `origin/main`.
   - Confirm whether the previous PR is merged, open, blocked, or failing checks.
   - If it is not resolved, finish that PR before choosing a new feature.

2. Run the dogfood report.

```bash
python3 skills/prompt-rewrite/scripts/dogfood_report.py --pr <number> --evidence-file ~/.codex/memories/MEMORY.md --scan-skills
```

Use a narrower evidence file when possible. Broad profile review over all memories is a calibration pass, not something to run every lap.

3. Interpret the result.
   - Fixture failure beats all new work.
   - PR/check/auth problems beat new behavior.
   - Token spikes suggest review-scope or cache work.
   - Missing coverage for the latest user prompt suggests a new fixture.
   - Installed-skill routing misses suggest scanner or routing-reference work.

4. Pick one next build.
   - Keep each lap to one coherent PR.
   - Add or update a fixture before behavior changes when the behavior can regress.
   - Prefer scripts for repeated measurement and references for loop rules.

5. Implement, validate, publish, and stop.
   - Run the fixture checker and relevant syntax checks.
   - Commit, push, and open the PR.
   - Rerun the dogfood report after merge before starting the next lap.

## Boundaries

- Do not auto-merge PRs unless the user explicitly asks.
- Do not run an unbounded infinite loop. Each lap ends with a report and a PR or a clear reason to stop.
- Do not perform broad local chat review every lap. Use recent, task-relevant evidence unless recalibration is requested.
- Do not turn dogfood into unrelated product expansion. The next build should come from a concrete failure, repeated friction, missing fixture type, or user correction.

## Rewrite Template

```text
Run one supadupaprompt dogfood lap in the current repo. First fetch and inspect the previous PR state. Then run the dogfood report, including fixture validation, rewrite token estimates, optional profile-review estimate over the narrowest useful evidence, and installed-skill routing scan. If anything fails, fix that before adding behavior. If the suite passes, choose exactly one small next improvement from the latest dogfood friction, add fixture coverage when relevant, implement it, validate, commit, push, and open a PR. Stop after the PR/report summary; do not auto-merge or start another lap without an explicit follow-up.
```
