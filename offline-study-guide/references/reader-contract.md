---
description: "Reader shell contract: navigation, bookmarks, search, themes, print, and viewport rules for offline study guides."
connections: [clinical-constraints]
---

# Reader contract

Use this when adding or repairing the reader around an existing book.

## Chrome

- Header is sticky and two rows on a phone: tool buttons, then previous / chapter select / next / theme.
- Touch targets at least 44px. Labels stay readable at 360px.
- Hide the brand line under 480px if it causes a third row.
- `scroll-margin-top` on headings is at least the header height.

## Chapter model

For a guide with `<section class="doc-section">` and `<article class="chapter">`:

- Section name comes from the section `h2`, with a leading `Section` badge removed.
- Chapter name comes from `.chapter-title`.
- Display label is `Section — Chapter title`.
- Contents groups by section. The filter matches section and chapter.
- Medicine-style books keyed by `h1[id^="chapter-"]` use the heading text. Subtype rows stay associated with their chapter and page.

## Bookmarks

Save:

```json
{"title":"Hematology — Chapter 01: CBC","section":"Hematology","chapter":"Chapter 01: CBC","anchor":"chapter-01-cbc","offset":0,"created":0}
```

On open, if `anchor` resolves, show the current section and chapter even when the stored title is numeric. Keep legacy `y` only when no anchor resolves.

## Print

Use `assets/print-v5.css`. Hide `.reader-header`, `.reader-dialog`, `.reader-status`, `.chapter-nav`, sidebars, and floating buttons. Each chapter title starts a page except the first. Tables repeat `thead`. Paragraphs keep orphans and widows of 3. Body text prints black on white. Tables may shrink but must not clip off the page without a scroll fallback in screen CSS. All chapters remain in the document; do not print a filtered view.

## Diagrams

Wrap Mermaid source in `figure.diagram-source` with the caption `Diagram source (Mermaid) — not rendered offline`. Do not invent a graphic.

## Checks

Run `scripts/check_guide.py`. HTTP viewport checks are still required; the script does not open a browser.
