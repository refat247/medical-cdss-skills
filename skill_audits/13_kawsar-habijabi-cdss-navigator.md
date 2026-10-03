# 13 · kawsar-habijabi-cdss-navigator (v1.0.0) — Independent Audit

**Tier:** Separate product (bedside heuristics + exam engine) · **Code:** 535 LOC · **Tests: 0** · **README: none · CHANGELOG: none**

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| C | **F** | F | D | D | **F** (do not use for clinical decisions as is) |

Unlike the textbook skills, this one executes clinical logic itself, in code, with no tests and no clinician-review record in the repo.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| H1 | **Critical** | C | **No-match returns a safety clearance.** `run_prescribing_safety` checks **six hand-typed substring rules**; when none match it prints `INTERCEPT STATUS: [PERMITTED_WITH_ROUTINE_MONITORING]` and "No hard-stop contraindications … detected". Any drug, spelling, or phrasing outside six rules is reported as permitted. | Default to `NOT_EVALUATED — this is not a safety clearance` with a non-zero exit; move rules to a data file with source chunk IDs; add synonym/misspelling tests. |
| H2 | **Critical** | C | **`--federated` prints canned text** for Harrison, Hurst and Kumar & Clark, identical for every topic. If no bridge-CSV row matches, it falls back to `bridge_rows[0]` (an unrelated topic). It never calls the real federation. | Delegate to `medical-cdss-unified-orchestrator`; return "no match" instead of row 0; show per-book chunk IDs. |
| H3 | **Critical** | C | **Silent default patient values in calculators.** `anion` defaults to Na 140 / Cl 100 / HCO₃ 15 and `mentzer` to MCV 65 / RBC 5.8 when arguments are omitted, then prints a diagnostic "RESULT" (e.g. "SUGGESTIVE OF THALASSEMIA TRAIT… hold empirical iron therapy") for an imaginary patient. `dengue` defaults to 50 kg. Non-numeric input raises an uncaught `ValueError`. | Require all inputs; reject missing, non-numeric, zero or implausible values; never print an interpretation without real inputs. |
| H4 | High | C | **Dengue fluid calculator discontinuity and scope.** Maintenance is `weight*100` for ≤20 kg but `1500 + 20*(weight−20)` above 20 kg: a 20 kg patient gets 2,000 mL/24 h, a 21 kg patient 1,520 mL (arithmetic from the code). It then fixes a 48-h volume (maintenance×2 + 5% deficit, e.g. ~140 mL/h for 50 kg) as a flat rate. That is not a response-guided regimen, and it sits beside this same script's own warning about dengue fluid overload. (My reading of standard dengue guidance is that fluids are stepwise and adjusted to haematocrit/vitals; needs clinician confirmation.) | Remove or gate behind clinician review; implement Holliday–Segar piecewise correctly (100/50/20 per kg bands); cite the guideline; add unit tests across band edges (9, 10, 11, 19, 20, 21 kg). |
| H5 | High | C | **SBA bank is 4 hard-coded items** (HABIJABI-001/003/005/012), chosen with `random.choice`, although docs say it serves "137 verified records". Citations such as `Davidson 25th Ed, Ch 25` are literal strings, not looked up. | Generate from records with verified rationale chunks, or label as demo items; seedable randomness. |
| H6 | Medium | C | **Anion-gap logic:** labels any gap ≤12 "NORMAL ANION GAP METABOLIC ACIDOSIS" even if bicarbonate is normal; no albumin correction. | Check HCO₃ < 22 before saying "acidosis"; note albumin correction. |
| H7 | Medium | C | Hard-coded `D:\HABIJABI_FULL` (8 code lines) and printed `file:///D:/…` links. | Env-configured root. |
| H8 | Medium | C | Zero tests; no README or CHANGELOG, though `version-manager` lists it as "Consistent" (2 declarations). | Add tests for every calculator and rule; add docs. |
| OK | — | C | Drop-rate formulas are correct: mL/h ÷ 3 for 20 gtt/mL, ÷ 4 for 15 gtt/mL, 1:1 for 60 gtt/mL. | Keep; add tests. |

## Verdict
The most dangerous skill in the repo: it fabricates cross-book "grounding", defaults missing inputs to a fictional patient, and treats "no rule" as "safe". Clinical review of all rules and calculators is needed before any use beyond demonstration.

**Top 3 actions:** (1) flip the no-match default, (2) refuse missing inputs in calculators, (3) delete the canned federation or delegate it.
