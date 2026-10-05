---
description: "Input contract for markdown, Word, and PDF. Read before building a guide from a source file."
connections: [reader-contract]
---

# Input contract

Pipeline: source read, extraction, structure detection, census, quality gate, reader model, render, artifact check. Render success does not mean the source parsed.

## Markdown

`#` book title. `##` section. `###` chapter. Paragraphs, `-` bullets, `1.` lists, pipe tables (including standard alignment separators), and HTTP/HTTPS Markdown links are kept. Unsafe executable link schemes are not activated. A long file with no headings is FILE READ SUCCESS only and is not rendered.

## Word

`.docx` only. Heading 1, Heading 2, and Heading 3 are read from style metadata. Bold or large Normal text is not a heading. Paragraphs, List Bullet, List Number, tables, and ordinary external HTTP/HTTPS hyperlink relationships stay in document order. A chapter or section the source names Guide is valid. A section the parser invents, or a book with no chapter, is FILE READ SUCCESS and is not rendered. Book text before the first section keeps paragraphs, lists, and tables as separate blocks.

## PDF

The strict parser recognizes headings, any case, with optional `: . - —` after the number or letter:

- Chapter 1, Chapter 1: Title, CHAPTER 1 — Title
- Part I, PART I, Part 1, Section 1
- Appendix A, APPENDIX A

Introduction, Background, and Discussion are candidates, not headings. Text before the first Chapter is book front matter; text after a recognized Part/Section but before its first Chapter is section introductory content. Neither creates a phantom chapter. Many gapped lines are a structure review even if Chapter lines were recognized.

When the strict parser finds no chapter, a guarded **layout-aware textbook mode** may activate automatically. It requires all of the following: an extractable multi-page PDF, a large title on page 1, at least five page-1 contents-like entries ending in page numbers, and at least 80% agreement between those contents labels and later display headings. In that mode:

- PyMuPDF layout coordinates are used to read the left column before the right column;
- line-break hyphenation is normalized by the PDF engine;
- page headers, decorative chapter-number stripes, and non-text footers are excluded with explicit provenance;
- the original source contents list is retained as front matter;
- numbered boxed tables are promoted to semantic HTML only when the table geometry is reliable;
- source-authored display headings become reader chapters, while smaller repeats remain local subheadings;
- every original PDF page is embedded as a collapsed JPEG visual-fidelity appendix so figures, complex boxed material, and layouts remain inspectable even when they are not semantically reconstructed;
- the census records `layout_mode`, contents-heading match ratio, semantic table count, source boxed-table count, visual-only table count, and source-page fallback count.

The visual-fidelity appendix is evidence preservation, not semantic extraction. A complex figure or visually structured table may remain visual-only. A scan with almost no extractable text still asks for OCR. If the title/contents/body-heading corroboration gate is not met, the PDF remains FILE READ SUCCESS / structure review; the layout-aware mode does not guess. Generated HTML must keep its structure census; the checker rejects a missing census unless `--legacy-v4` is set.

## Expectation file

`--expect file.json` may set `min_chapters`, `min_sections`, `titles`, and `appendices`. A miss blocks render unless `--override-structure` is set.
