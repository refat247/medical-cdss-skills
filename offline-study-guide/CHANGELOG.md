# Changelog
## 1.2.0 — 2026-10-02
- V5 reader contract: A4 chapter page-breaks, repeating table headers, orphans and widows.
- Mermaid source must be captioned as an offline diagram. Bare graph blocks fail the checker.
- Medicine calculator disables IV iron, low-dose dopamine, norepinephrine, and amino acids in the control, and rejects weights outside 0.5–300 kg. The script gate remains.
- Medicine chapter menus must include the chapter title. A reader chrome presence check is no longer enough.
- Repaired guides still use `--legacy-v4` for the missing census. Print and calculator checks apply to them too.
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
