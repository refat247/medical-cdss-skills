# Changelog
## [1.3.0] - 2026-10-09

### Added
- Add opt-in source-span reference layout, density reporting, formulation fidelity checks and bilingual handoff.

## 1.2.1 — 2026-10-01
- Governance-only PATCH release; reader/parser behavior is unchanged from v1.2.0.
- Adds `README.md`, `MANUAL_ACTIVATION.md`, `ACTIVATION_SMOKE_TEST.md`, `agents/openai.yaml`, `VERSIONING_DECISION.md`, `RELEASE_AUDIT.md`, and a machine-verifiable package manifest.
- Adds `scripts/verify_release.py` to enforce version agreement across the canonical `SKILL.md` metadata, visible skill version, `VERSION`, README, OpenAI agent metadata, activation files, changelog, and package manifest.
- Standardizes the install archive with `SKILL.md` at the ZIP root and checks for nested/duplicate package roots, empty required files, compiled Python residue, and archive/file drift.
- Preserves the v1.2.0 functional code and all 59 regression checks unchanged; governance release verification re-runs the suite from the final extracted ZIP.
## 1.2.0 — 2026-10-01
- Adds a guarded layout-aware parser for extractable multi-column textbook PDFs that lack explicit `Chapter N` markers. Activation requires a large title page, at least five page-numbered source-contents entries, and at least 80% agreement with later display headings.
- Uses PyMuPDF layout coordinates and dehyphenation to read left-column then right-column text without weakening the existing hostile-layout gate for ordinary PDFs.
- Preserves page-1 authors/source contents as front matter, prevents smaller repeated headings inside worked examples from becoming duplicate navigation chapters, and filters decorative chapter stripes/footer glyphs.
- Reconstructs numbered boxed-table columns from source coordinates when PyMuPDF merges cells; records semantic versus visual-only table counts.
- Embeds every original page as a compressed, collapsed visual-fidelity appendix in layout-aware mode so figures and complex page layouts remain inspectable offline without pretending they were semantically extracted.
- Checker now verifies the embedded source-page fallback count and the contents-heading trust threshold.
- Regression matrix expanded from 54 to 59 checks. External integration test used the supplied 12-page Davidson clinical decision-making chapter and reached PARSE SUCCESS with 27 navigation chapters, 25/25 source-contents matches, six semantic boxed tables, one visual-only boxed table, and 12 embedded source-page fallbacks.
## 1.1.4 — 2026-10-01
- Final parser-contract hardening for PDF ownership, census table accounting, Markdown aligned pipe tables, and hyperlink preservation.
- PDF prose before the first Chapter is book front matter; prose after a recognized Part/Section and before its first Chapter is section intro. No phantom chapter is created.
- Census table totals now include book front matter, section intros, and chapter content, with component counts.
- Markdown table alignment rows (`---`, `:---`, `---:`, `:---:`) are structural separators, not data.
- Markdown and DOCX HTTP/HTTPS hyperlinks are preserved through controlled inline rendering; unsafe executable schemes remain non-active and raw source HTML stays escaped.
- Regression matrix expanded from 39 to 54 checks; runner exits explicitly after flushing results for deterministic automation.
## 1.1.3 — 2026-10-01
- Latent structural-quality defects found after the 1.1.2 source-preservation repair.
- A source-authored chapter or section named Guide is valid. Fallback is recorded only when the parser creates it.
- A book with no chapter is FILE READ SUCCESS and is not rendered. The census is not marked PARSE SUCCESS before that failure.
- A chapter before a section is an inferred section and is blocked.
- Book front matter keeps paragraphs, lists, and tables as separate ordered blocks.
## 1.1.2 — 2026-10-01
- Correction of a latent source-preservation defect present since the builder, not introduced by 1.1.1.
- Content between a section heading and its first chapter stays on that section, including paragraphs, lists, and tables.
- Book preface before the first section remains global front matter.
- Markdown census uses Markdown parser metadata. Dropped blocks block PARSE SUCCESS.
- `--override-structure` may render, but the census stays FILE READ SUCCESS and the normal checker still rejects it.
## 1.1.1 — 2026-10-01
- Correction: the pre-v1.1.0 package advertised DOCX support and called parse_docx(), but an independent run reproduced NameError because def parse_docx() was absent. v1.1.0 restored the parser. The later workspace zip that already contained def parse_docx() was not that broken package.
- Word List Bullet and List Number styles render as ul/ol, not paragraphs.
- A short dummy Guide chapter is blocked. Fallback chapter creation is tracked separately from later real headings.
- Preface text before the first chapter is front matter, not a hidden Guide chapter.
- Hostile column/table extraction blocks render even when Chapter headings were recognized.
- Checker fails a generated artifact with no structure census unless --legacy-v4 is set.
## 1.1.0 — 2026-10-01
- Previous packaged zip was unversioned (treated as 1.0.0).
- Word lists are preserved. Legacy .doc is rejected instead of parsed.
- PDF headings accept Chapter, CHAPTER, Part, PART, Appendix, and APPENDIX variants with colon, dash, or em dash.
- Plain prose headings such as Introduction are not promoted. A dummy Guide chapter no longer renders as success.
- Structure census and quality gate run before render. Optional `--expect` blocks a mismatch unless `--override-structure` is set.
- Checker fails a census whose status is not PARSE SUCCESS.
- Regression matrix: scripts/run_regression.py.
## 1.0.0 — 2026-10-01
- Initial skill from the investigation and medicine V4 reader repairs.
- End-to-end builder for markdown, Word, and PDF using the V4 reader shell.
- Checker covers viewport, zoom lock, reader chrome, A4 rule, CDN ban, and section-chapter labels.
- Word tables stay tables. Medicine calculator template is included only with `--book medicine --calculator`; four audited entries stay disabled.
- Section-badge spacing, book-specific bookmark keys, and repeated section/chapter labels.
