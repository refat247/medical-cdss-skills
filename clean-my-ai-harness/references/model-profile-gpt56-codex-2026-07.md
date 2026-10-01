# Dated profile: GPT-5.6 family in Codex

Research cutoff: 2026-07-14

Use this profile only for a GPT-5.6-family model running in Codex. ChatGPT Work and API products need separate surface notes.

## What the evidence supports

Codex documents a bounded initial skill-discovery surface. Nate's 66 skill descriptions totaled 27,197 characters, and a native proof run displayed a warning that descriptions were shortened to fit the available skills budget. That proves discovery pressure existed on that surface. It does not prove a routing miss or a universal GPT-5.6 productivity advantage after cleanup.

On 2026-07-14, Codex CLI 0.144.2 identified the authenticated account's default model as `gpt-5.6-sol`. Forcing the generic ID `gpt-5.6` returned a product-level error saying that model ID was not supported with the ChatGPT account. Record the exact model ID the runtime exposes. Do not tell a reader to force the generic ID just because the family is called GPT-5.6.

## Recommendations to test on the user's setup

- Keep skill names and discovery descriptions concise, distinct, and about selection: what problem the skill solves and when to use it.
- Load the full procedure only after the skill is selected.
- Give one job one clear route and keep shared policy in one owned source.
- Record the exact model, reasoning effort, tool route, sandbox, approvals, fallback, loaded skill, checks, and output files.
- Use schemas, tool restrictions, permissions, validators, tests, and file receipts for binary requirements when the runtime supports them.
- Keep private context, product truth, source priority, authority, and acceptance criteria even when simplifying the route.

Label these as dated Codex recommendations, not GPT personality. Recheck after a major model, skill-loader, or Codex runtime change.
