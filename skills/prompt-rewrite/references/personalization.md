# Personalization

Apply a prompt profile only when it is available in the current conversation or a user-approved local file.

## How To Use A Profile

1. Extract 3-7 active rewrite rules from the profile.
2. If the profile includes a `Prompt-Rewrite Handoff` block, treat it as the active rule set and avoid re-summarizing the whole profile.
3. Apply rules that fit the current prompt type.
4. Keep the final prompt in the user's working style.
5. Do not mention private profile details unless relevant.

## Useful Defaults For Direct, Execution-Oriented Users

- Preserve informal directness.
- Add current-state inspection instead of abstract planning.
- Add verification gates by default.
- Specify whether to implement, review, research, or only propose.
- Include subagents only when the user asks for them or the task clearly benefits and the environment supports them.
- Prevent overbuilding with explicit scope boundaries.
- For repo work, require repo-root verification before editing.
- For live-product work, require browser or live-surface evidence.

## Example Profile Rule Application

Profile rule:

```text
When the user asks whether something is ready, require real verification before answering.
```

Rough prompt:

```text
is this ready to ship
```

Improved prompt:

```text
Check whether this is ready to ship from the current checkout. Verify repo status, run the relevant tests/build, inspect any changed user-facing flow if applicable, and report blockers first. Do not say it is ready unless the verification actually passed; list any checks you could not run.
```
