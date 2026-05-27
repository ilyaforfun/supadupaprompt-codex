# Quality Rubric

Score each item 0-2. A strong prompt usually scores 10+ without unnecessary length.

| Item | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Goal | Vague action | Broad goal | Specific outcome |
| Context | Missing | Some context | Sources/files/examples included |
| Scope | Open-ended | Partial boundary | Clear touch/do-not-touch rules |
| Method | No execution guidance | Some tool hints | Tool, research, subagent, or verification method specified |
| Output | Undefined | General format | Exact deliverable and ordering |
| Verification | None | Weak "check it" | Concrete tests/evidence/done criteria |

## Common Fixes

- If goal is vague, convert verbs like "fix", "check", "improve", or "make better" into observable outcomes.
- If context is missing, tell the agent what to inspect first.
- If scope is too broad, add "keep this to..." and "do not...".
- If verification is missing, add the cheapest reliable check.
- If the prompt is too long, remove theory and keep only instructions that affect output.

## Red Flags

- The prompt asks for "best" without saying best for whom.
- The agent could satisfy the prompt with a generic answer.
- The prompt invites unrelated refactors or feature expansion.
- The prompt requires current facts but does not require browsing or source citations.
- The prompt asks for review but does not require findings first.
- The prompt asks an agent to act in production without approval gates.
