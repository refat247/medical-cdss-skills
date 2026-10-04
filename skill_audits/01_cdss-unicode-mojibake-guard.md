# 01 · cdss-unicode-mojibake-guard (v1.5.2) — Independent Audit

**Tier:** Critical path (pre-flight) · **Code:** 521 LOC · **Tests:** 22 pass / 0 fail `[M]` (394 test LOC)

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A | B | A- | C | B | **B+** |

## What it does well
- Separates **source repair** from **generated-output rewriting**: ISMP rewrites (`5.0 mg`→`5 mg`, `QD`→`once daily`, `µg`→`mcg`) are applied only by `sanitize`/`cleanroom-docx`, never to source text; in source, ISMP issues are *advisories* only `[C]`.
- `fix` skips directories holding `*_CHECKPOINT.json` or trust markers, so it cannot mutate a trusted RAG output `[C]`.
- Tested: superscripts/subscripts and fractions (`10⁹/L`, `10⁶ IU`, `m²`, `CO₂`, `½`) survive both source repair and sanitize unchanged `[M]`. This matters because a naive NFKC pass would turn `10⁶` into `106`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| G1 | Medium | C | `fix_directory` overwrites files in place (`write_text`) with **no `--dry-run` and no backup**. Protection exists only for checkpoint/trust directories; any other corpus `.md/.json/.csv` is rewritten. | Add `--dry-run` (default for first run), write `.orig` or a SHA-256 manifest before rewrite, print a per-file diff summary. |
| G2 | Medium | C | **Docs contradict behaviour.** SKILL.md says repair maps `Âµg → mcg` and `≥ → >=`; code restores the original (`Âµg → µg`) and leaves ISMP to output. SKILL.md also says "6-Layer" but lists 7 layers, and Layer 3 (NFKC) is not observable on the glyphs tested. A user following the doc would expect source rewriting. | Rewrite the layer table with two columns: *source repair* vs *output sanitize*. Fix the layer count. State exactly which Unicode forms NFKC changes. |
| G3 | Low | C | `except Exception: continue` in `fix_directory` silently skips unreadable files, and the count is not reported. | Count and print skipped files; exit non-zero in `gate` mode if any were skipped. |
| G4 | Low | C | `sanitize_for_llm` also rewrites spacing (`<60` → `< 60`). Harmless but changes verbatim text. | Document as output-only normalisation; keep out of source repair (already true). |
| G5 | Low | C | SKILL.md examples are hard-coded `C:\Users\User\.gemini\...` paths (4). | Use `$CDSS_SKILLS_ROOT` placeholders. |

## Verdict
Best-engineered pre-flight skill and safe on the clinically dangerous glyph cases I tested. Fix the doc/behaviour mismatch (G2) and add a dry-run (G1) before trusting it on corpora outside the protected directories.

**Top 3 actions:** (1) `--dry-run` + backup manifest, (2) correct SKILL.md layer table, (3) report skipped files.
