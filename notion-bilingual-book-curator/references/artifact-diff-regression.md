# Artifact Diff & Regression Control

Use after a repair whenever both the previous and repaired artifacts are available.

## Purpose

Confirm:
1. the authorized repair occurred;
2. unrelated content did not change;
3. previously passed defects did not regress.

## Comparison dimensions

When tooling supports them, compare:

- page count;
- extracted text by page;
- normalized text hashes;
- rendered-page differences;
- PDF outline/bookmark targets;
- link/annotation counts and targets;
- fonts/glyph rendering where affected.

## Authorized-change map

Before comparing, define the allowed patch scope.

For each changed page/block classify:

AUTHORIZED CHANGE  
EXPECTED REFLOW  
UNRELATED CHANGE — INVESTIGATE  
REGRESSION  
METADATA/NAVIGATION ONLY

A page-number shift caused by a legitimate reflow is not itself semantic drift.

## Regression gate

PREVIOUSLY PASSED ≠ STILL PASSED AFTER A LATER REPAIR.

After every final micro-patch, recheck:
- all newly requested repairs;
- all earlier freeze blockers;
- navigation affected by pagination;
- glossary/control counts affected by reflow;
- SOURCE PARTIAL boundaries;
- evidence/status labels.

## Minimal-repair ratchet

As the artifact matures:
- broad instructions should decrease;
- patch scope should shrink;
- unrelated redesign should be prohibited.

Preferred sequence:

MASTER BUILD
→ TARGETED REPAIR
→ MICRO-PATCH
→ FINAL MICRO-REPAIR
→ FREEZE AUDIT

If a late repair introduces a regression, repair only that regression plus the still-open blocker; do not replay the full master prompt.

## Reporting

When possible state:
- pages changed;
- whether rendered pages changed;
- whether extracted text changed;
- whether bookmark/link metadata changed;
- whether all changes map to the authorized patch.

If a comparison dimension is unavailable, report it as unavailable rather than "unchanged".
