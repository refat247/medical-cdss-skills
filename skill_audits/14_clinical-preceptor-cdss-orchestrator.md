# 14 · clinical-preceptor-cdss-orchestrator (v1.1.0) — Independent Audit

**Tier:** Separate product (educational/bedside) · **Code:** 1,450 LOC (orchestrator 554 + 894-line modality generator) · **Tests:** 1 pass (version consistency only; 35 test LOC) `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| C | C- | F | C | D | **D+** |

## What it does well
- Good scaffolding: workspace init, staged pipeline (`prune-comments → english-synthesis → claims → bridge → extended-modalities → audits`) and a pre-prune backup policy with SHA-256 manifest described in SKILL.md.
- Modality 13 (never-events) reads a CSV matrix rather than inline rules.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| C1 | High | C | **Half the "13 modalities" are a pass-through.** Modalities 1–6 (Socratic, SBA, prescribing safety, 4-book federation, tropical calculators, search) are forwarded by `subprocess` to the Kawsar script, so every defect in file 13 (H1–H6) is inherited. | Choose one owner; move shared logic into one module with tests; the other becomes configuration. |
| C2 | High | C | **Clinical content is hard-coded in the generator, not derived from the corpus:** the never-events toxic-drug matrix rows, Bengali patient leaflets (~97 lines of Bengali text), SBAR high-acuity cases, causal-graph "hardcoded_triplets", and Anki "high_yield_specifics" are literals in `generate_extended_modalities.py`. They are exported into the same folders as corpus-derived assets and look equally authoritative. | Move to reviewed data files with source citations and reviewer sign-off; tag exports with `origin: curated` vs `origin: derived`. |
| C3 | High | C | **OSCE Visual Spotter has no real answer key.** The image type is guessed from the file name/domain (`ecg`, `xray`, `pbf`…), and the "finding" is the template string `Visual evidence associated with {condition} ({title})`. Missing records default to "General Medicine / Clinical Pathology". | Require a verified caption/finding per image from the source record; skip images without one. |
| C4 | Medium | C | Test coverage: one version test for 1,450 LOC; no test of any modality, the backup/prune path, or the Kawsar hand-off. | Smoke test for each of the 13 modalities on a fixture workspace; test backup+manifest. |
| C5 | Medium | C | Forwarding looks for `C:\Users\User\.gemini\config\skills\kawsar-…` first, then a workspace copy; both Windows-specific; default workspace `D:\HABIJABI_FULL` (10 code lines, 24 doc lines). | Resolve via `CDSS_SKILLS_ROOT`; fail with a clear error. |
| C6 | Medium | C | Two overlapping SKILL descriptions (this and Kawsar) both claim SBA and prescribing safety, so routing is ambiguous. | Routing note: textbook → unified; Habijabi bedside → preceptor. |
| C7 | Medium | C | `run_pipeline_stage` runs each stage via `runpy` **only `if script.exists()`** under `workspace/tools/` (seen for `prune-comments`; same pattern appears for the other stages). A missing stage script is skipped without failing, so `--pipeline auto` can finish with stages not run. | Fail (or print a stage-by-stage status table) when a required stage script is absent. |

## Verdict
Valuable teaching scaffold, but its clinical content is unreviewed literals and its testing is effectively absent.

**Top 3 actions:** (1) externalise and review hard-coded clinical content, (2) modality smoke tests, (3) resolve ownership vs Kawsar.
