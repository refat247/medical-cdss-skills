# Context handoff: medical-cdss-skills second-sweep fixes

Self-contained summary for onboarding another person or LLM. Source of truth for live status is `FIX_STATUS.md`.

## Repo and PR
- **Repo:** `refat247/medical-cdss-skills`, a suite of 19 "skills" (Python tools plus `SKILL.md` descriptions) for a medical clinical-decision-support (CDSS) pipeline. It covers Unicode/OCR cleaning, a Davidson textbook RAG pipeline, index compilers, retrieval packagers, a bridge-note publisher, navigators for Harrison, Hurst, Kumar & Clark and the Kawsar/Habijabi series, orchestrators, and version and QA tooling.
- **Branch:** `claude/exciting-cannon-0dqntt`, about 64 commits ahead of `main`. It includes earlier sessions' first-pass and verification-review fixes.
- **PR:** https://github.com/refat247/medical-cdss-skills/pull/1, titled "Second-sweep fixes: compiler, bridge, preready, Davidson, Kumar, trigger scoping". Open, not merged, mergeable, CI (`qa` workflow) green, no review threads. The repo has no PR template.
- **Source documents:** `skill_audits/SECOND_SWEEP.md` (defect list), `skill_audits/FIX_STATUS.md` (Open and Fixed status, behaviour changes, test evidence, environment note), per-skill audits `01_…` to `19_…`.

## Working rules the user set
- Work only the "Open" list of `FIX_STATUS.md`, one small commit plus one regression test per fix.
- Run `python qa/check_all.py`, the skill's own tests, then `python version-manager/scripts/bump_version.py --suite . --verify` before pushing.
- Do not change clinical content. Do not spawn reviewer subagents unless asked.
- Keep output terse and end each task with a ready-to-paste next-prompt suggestion.

## What was fixed (each with a regression test that fails on the old code)
**medical-index-rag-compiler**
- M22: duplicate acronyms keep every expansion.
- M21: the page-anchor regex ignores digits inside terms like `HbA1c`.
- M20: lowercase-initial acronyms like `eGFR` are primary index entries.
- M25: BM25 weights skip stop words and discount common words.
- M26: the chunk path filter matches whole folder tokens, not substrings.

**cdss-bridge-note-publisher** (M30 and M31 also applied to the byte-identical `enhance_figures.py` in cdss-retrieval-packager)
- M28: literal asterisks are not parsed as italic, and `<br>` becomes a line break.
- M29: each separate numbered list restarts at 1.
- M30: 16-bit greyscale figures are scaled, not whitened.
- M31: the enhanced figure is refreshed when its source changes.
- M32: the chapter regex is token-anchored, and an ambiguous book name resolves to none.

**davidson-ocr-preready**
- M17: empty header cells keep a full GFM delimiter.
- M19: report completeness is computed; unresolved tables or figures give status `PARTIAL` with exit code 3.

**davidson-rag-pipeline-antigravity**
- 1.20/F10: protection-marker hashes are re-compared when building trust records; a chapter edited after finalize is downgraded to `CORPUS_REVIEW_PENDING`.
- 1.24: figure tags are never inserted mid-table; LaTeX captions no longer crash.
- 1.26: the Ch05 adjudication script is limited to the five documented chunks; gate evidence is read from the existing gate, not hard-coded; it gained `--out-dir`; backups can't overwrite.
- 1.27: Stage 4.7 completeness uses whole-word keywords and scores the body, not the frontmatter; clusters under 3 chunks are reported as `low_evidence` (verdict unchanged).
- 1.28: the LLM verifier batches requests, rejects `max_tokens`-truncated replies, tolerates dict or garbage replies; `CDSS_VERIFIER_MODEL` overrides the model id.
- 1.30 mechanical items: a Stage 4 re-run no longer duplicates `AUDIT_REPORT` sections; the trust record follows the newest checkpoint; Stage 3 no longer false-blocks short documents (under 50 non-empty lines, scored by characters); the Ch05 backup name can't collide. The auto-chain CLI test now asserts exit 3.
- Direct tests added for Stage 4.5b and Stage 7.

**kumar-cdss-navigator**
- D-26: partial drug matching is whole-word and lists candidates when ambiguous.

**Trigger collisions (3.17)**
- Overlapping skill descriptions now say which skill to use instead (antigravity-protocol, kawsar, preceptor, unified, rag-orchestrator, token-audit, clean-my-ai-harness, version-manager). `qa/test_trigger_scope.py` guards this; `check_all.py` does not run it.

## Behaviour changes to expect
- Preready and the auto-chain CLI exit **3** when a chapter finishes but is not complete or trusted; wrappers expecting 0 need updating.
- Stage 4.7 scores shift; re-run 4.7 before trusting old completeness results.
- Earlier changes: stricter Davidson gates (4.5 and 6), the compiler exits 1 on a benchmark miss unless `--allow-benchmark-fail`, and the prescribing-screen exit code changed.

## Still open (not fixable mechanically)
- **Needs a decision or input:**
  - preready M18, cross-run figure overwrite in a shared `--out-dir` (refuse or version?)
  - edge over-inclusion not flagged
  - retrieval "accuracy" is self-retrieval
  - bridge enhanced figure looked up by basename, and the canned fallback
  - 1.24 PDF image numbering mis-naming (unconfirmed)
  - the `claude-sonnet-5` default verifier model id is unverified
  - Davidson F18/F22/F25/F29 and reviewer F13/F14/F20/F21 have no individual definitions in the repo
  - 30 Davidson tests skip because they need the author's `D:\` corpus
- **Needs a clinician** (all clinical content; nothing here has been clinician-reviewed):
  - dengue-shock SBA
  - MR mutation rationale
  - gout hard stop
  - SSRI washout
  - thalassaemia leaflet
  - dengue calculator adult weight cap
  - Ch05 `false_positive` adjudication calls

## Test evidence at last push
- `qa/check_all.py` green.
- Davidson 618 passed / 30 skipped; bridge 35; compiler 25; packager 23; preready 52; Kumar 13 (7 skipped).
- Version check: 19/19 skills, 0 drift.

## Environment gotchas
- Pillow, python-docx and pytest must be installed for `check_all` and the tests.
- On a fresh clone, two Davidson Ch05 fixture tests fail because `.gitattributes` pins the fixtures to CRLF but git checked them out as LF. Fix, with no tracked change: `rm -rf davidson-rag-pipeline-antigravity/tests/fixtures && git checkout -- davidson-rag-pipeline-antigravity/tests/fixtures`.

## Process state
- The Claude session is subscribed to PR #1 activity, with a safety-net check-in scheduled for about 06:13 UTC on 2026-10-02.
- If CI goes red or a review comment arrives: root-cause, fix with a test, re-run the checks, push.
- Nothing is pending on code; the PR waits for a reviewer or the owner to merge.
