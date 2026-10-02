---
description: "Input contract for markdown, Word, and PDF. Read before building a guide from a source file."
connections: [reader-contract]
---

# Input contract

Pipeline: source read, extraction, structure detection, census, quality gate, reader model, render, artifact check. Render success does not mean the source parsed.

## Markdown

`#` book title. `##` section. `###` chapter. Paragraphs, `-` bullets, `1.` lists, and pipe tables are kept. A long file with no headings is FILE READ SUCCESS only and is not rendered.

## Word

`.docx` only. Heading 1, Heading 2, and Heading 3 are read from style metadata. Bold or large Normal text is not a heading. Paragraphs, List Bullet, List Number, and tables stay in document order. A chapter or section the source names Guide is valid. A section the parser invents, or a book with no chapter, is FILE READ SUCCESS and is not rendered. Book text before the first section keeps paragraphs, lists, and tables as separate blocks.

## PDF

Recognized headings, any case, with optional `: . - —` after the number or letter:

- Chapter 1, Chapter 1: Title, CHAPTER 1 — Title
- Part I, PART I, Part 1, Section 1
- Appendix A, APPENDIX A

Introduction, Background, and Discussion are candidates, not headings. Many gapped lines are a structure review even if Chapter lines were recognized. A scan with almost no extractable text asks for OCR. Generated HTML must keep its structure census; the checker rejects a missing census unless `--legacy-v4` is set.

## Expectation file

`--expect file.json` may set `min_chapters`, `min_sections`, `titles`, and `appendices`. A miss blocks render unless `--override-structure` is set.
