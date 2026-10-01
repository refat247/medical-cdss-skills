# Independent Per-Skill Audits — Index

One report per skill, each scored on the same five dimensions and listing findings with severity, evidence tag and a fix. Companion to `../GOAL_ALIGNMENT_REPORT.md` (cross-skill view).

**Evidence tags:** `[M]` measured by running something here · `[C]` read in code · `[I]` inferred, not verified.
**Grades (my judgement, A–F):** *Goal fit* = does it advance "textbook → verified CDSS"; *Safety* = can it mislead or destroy data; *Tests* = coverage and hermeticity; *Docs accuracy* = does SKILL.md match the code; *Portability* = runs off the author's `D:\` disk. Overall is not an average: a Critical safety finding caps it.

| # | Skill | Tier | Overall | Crit | High | Med | Low | Tests pass/fail (this machine) |
|--:|---|---|:-:|:-:|:-:|:-:|:-:|---|
| 01 | [cdss-unicode-mojibake-guard](01_cdss-unicode-mojibake-guard.md) | Critical path | **B+** | 0 | 0 | 2 | 3 | 22/0 |
| 02 | [medical-book-split-ocr-organizer](02_medical-book-split-ocr-organizer.md) | Critical path | **C+** | 0 | 1 | 2 | 2 | 7/0 |
| 03 | [davidson-ocr-preready](03_davidson-ocr-preready.md) | Critical path | **B** | 0 | 1 | 2 | 2 | 19/0 |
| 04 | [davidson-rag-pipeline-antigravity](04_davidson-rag-pipeline-antigravity.md) | Critical path | **B+** | 0 | 2 | 3 | 2 | 463/3 (30 skip) |
| 05 | [medical-index-rag-compiler](05_medical-index-rag-compiler.md) | Critical path | **D** | 2 | 1 | 2 | 1 | 11/0 |
| 06 | [cdss-retrieval-packager](06_cdss-retrieval-packager.md) | Critical path | **B-** | 0 | 1 | 3 | 2 | 9/0* |
| 07 | [cdss-bridge-note-publisher](07_cdss-bridge-note-publisher.md) | Goal-adjacent | **B+** | 0 | 1 | 3 | 1 | 17/0 (1 skip)* |
| 08 | [medical-rag-orchestrator](08_medical-rag-orchestrator.md) | Critical path | **B+** | 0 | 2 | 2 | 2 | 11/0 |
| 09 | [medical-cdss-unified-orchestrator](09_medical-cdss-unified-orchestrator.md) | Critical path | **C+** | 1 | 2 | 3 | 1 | 13/0 |
| 10 | [harrison-cdss-navigator](10_harrison-cdss-navigator.md) | Critical path | **C** | 0 | 0 | 4 | 2 | 6/1 |
| 11 | [hurst-cdss-navigator](11_hurst-cdss-navigator.md) | Critical path | **C+** | 0 | 0 | 3 | 3 | 6/0 (3 skip) |
| 12 | [kumar-cdss-navigator](12_kumar-cdss-navigator.md) | Critical path | **C** | 0 | 0 | 4 | 2 | 5/7 |
| 13 | [kawsar-habijabi-cdss-navigator](13_kawsar-habijabi-cdss-navigator.md) | Separate product | **F** | 3 | 2 | 3 | 0 | none |
| 14 | [clinical-preceptor-cdss-orchestrator](14_clinical-preceptor-cdss-orchestrator.md) | Separate product | **D+** | 0 | 3 | 4 | 0 | 1/0 (version only) |
| 15 | [antigravity-protocol](15_antigravity-protocol.md) | Platform | **B-** | 0 | 0 | 3 | 2 | n/a |
| 16 | [ultimate-protocol](16_ultimate-protocol.md) | Platform | **C+** | 0 | 1 | 2 | 1 | n/a |
| 17 | [clean-my-ai-harness](17_clean-my-ai-harness.md) | Platform | **B-** | 0 | 1 | 2 | 2 | none |
| 18 | [token-audit](18_token-audit.md) | Platform | **B-** | 0 | 0 | 2 | 3 | n/a |
| 19 | [version-manager](19_version-manager.md) | Platform (used by pipeline) | **B-** | 0 | 2 | 2 | 1 | 8/0 |

\* Passing only after `pip install pillow`; without it, the packager suite errors at collection and one bridge-publisher test fails.

## Read in this order (highest risk first)
1. **13 kawsar-habijabi** (F): clinical logic in code, no tests; no-match = "permitted"; calculators invent a patient from defaults; canned "federation".
2. **05 index-compiler** (D): hard-coded benchmark scorecard; stub router; "co-occurrence" is alphabetical neighbours.
3. **09 unified-orchestrator** (C+): "verification" is concatenation; partial results exit 0.
4. **14 clinical-preceptor** (D+): hard-coded clinical literals, untested, inherits file 13's defects.
5. **07 bridge-note-publisher** (B+): good gate, but it checks citation existence, not claim support.
6. **19 version-manager** and **03 ocr-preready**: the missed `SKILL_VERSION` is a real provenance defect.
7. **04 davidson pipeline**: strongest skill; fix CRLF fixture hashes and log the Stage 4.6 LLM verifier.

## Patterns that repeat across skills
- **Claims exceed checks** (05, 06, 07, 09, 10–12, 13): "zero-hallucination", "sub-millisecond", "turnkey", "verified" appear in descriptions where the code does something narrower.
- **Destructive operations with no dry-run** (01 fix, 02 force overwrite, 06 prune, 19 bump).
- **Silent degradation**: ignored decode errors (10–12), swallowed ImportError (09), skipped stages (14), partial results exit 0 (09).
- **Windows-only paths** in every runtime skill; the only portable tests are the ones that never touch the corpus.
- **Hard-coded clinical content** outside the corpus (13, 14) with no reviewer record.
- **Version/provenance drift**: wrong stamp (03), legacy names inside outputs (04), no cross-skill constraints (19).

## What I did not verify
- Anything that needs the real corpora (`D:\01_Medical_Study\…`, `D:\HABIJABI_FULL`): retrieval accuracy, latency, hallucination rate, whether packaged routers behave as the navigators assume.
- Clinical correctness of Kawsar's rules, the Habijabi bridge CSV, the never-events matrix and the Bengali leaflets (needs clinician review). Where I comment on dengue fluids, it is from reading the arithmetic and my general understanding of stepwise guidance, not a guideline check.
- The 18 internal stages of the Davidson pipeline beyond its tests, orchestration use and the Stage 4.6 module layout; the reasons for its 30 skipped tests.
