# 03 · davidson-ocr-preready (v1.7.5) — Independent Audit

**Tier:** Critical path (normalise) · **Code:** 804 LOC · **Tests:** 19 pass / 0 fail `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A- | B+ | B+ | C | C | **B** |

## What it does well
- Narrow, safe write scope: output chapter dir and `assets/figures/` only; writes via a temp file `[C]`.
- Normalises to NFC, strips running headers, inlines tables and decouples figures; explicit handover contract to the RAG pipeline (`references/ocr_handover_contract.md`).

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| P1 | High | M,C | **Provenance stamp is wrong.** `preready/auditor.py` has `SKILL_VERSION = "1.6.0"` and writes it into every output header and audit report; the skill is 1.7.5. `runner.py` docstring says v1.7.0. `version-manager --verify` reports "0 drift" because it does not scan `SKILL_VERSION`. | `from preready import __version__` in `auditor.py`; delete the duplicate; extend the version scanner (see 19). Add a test that the stamp equals SKILL.md. |
| P2 | Medium | C | `detect_document_archetype` classifies by **substring of the folder name** (`"ada_"`, `"esc_"`, `"nice_"`, `"who_"`). `canada_…`, `venice_…` or similar names would be marked GUIDELINE; everything else defaults to TEXTBOOK. | Match on whole tokens (`re.split(r"[_\- ]")`) or take an explicit `--archetype`; fail loudly if ambiguous. |
| P3 | Medium | I | Table inlining has no integrity check that inlined row/cell counts equal the source `tbl-*.md` (not seen in code). A dropped row would not be detected here. | Count rows/cells before and after and record them in the audit report; fail on mismatch. |
| P4 | Low | C | Named "davidson-" but used for Harrison, Hurst, guidelines. | Rename or document as generic; update triggers. |
| P5 | Low | C | `except Exception as e` in `runner.py` around per-asset work reports and continues. | Roll failures into an exit code. |

## Verdict
Reliable normaliser with a good safety scope. The wrong version stamp (P1) is a real provenance defect that the repo's own checker failed to catch.

**Top 3 actions:** (1) fix `SKILL_VERSION` import, (2) token-based archetype detection, (3) table row-count check.
