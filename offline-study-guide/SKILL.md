---
name: offline-study-guide
description: "Build or repair a self-contained offline HTML study guide with chapter navigation, search, section-aware bookmarks, themes, and A4 print. Use when the user wants a mobile study guide, reader HTML, or a successor to the investigation or medicine guides. Not for dashboards, web apps, or clinical rewriting."
type: workflow
lifecycle: active
---

# Offline study guide — standalone HTML reader

Version 1.2.0. Build a single HTML file that opens offline with no build step. Preserve the supplied book. Do not replace it with a dashboard or a summary.

Read `references/input-contract.md` before accepting a markdown, Word, or PDF source. A file that opens is not a parsed book. Render only after the structure census says PARSE SUCCESS.

Reference guides already in this project: `artifacts/BEGINNERS_GUIDE_MOBILE_V4.html` and `artifacts/SELECTION_OF_MEDICINE_MOBILE_V4.html`. Copy their reader shell when repairing those books. Read `references/reader-contract.md` before changing navigation, bookmarks, or print. Read `references/clinical-constraints.md` before touching medical text or the calculator.

## Workflow

1. Keep the supplied file unchanged. Write a versioned successor next to it (`NAME_Vnext.html`).
2. Inventory chapters, sections, tables, formulas, and any calculator. Record counts.
3. Preserve every clinical sentence, number, unit, table cell, and link. Do not dedupe passages or invent figures.
4. Wrap content in the reader shell: skip link, sticky header (tools row + chapter row), native `<dialog>`, progress bar, main landmark.
5. Label every chapter with its section. Bookmark titles and the chapter menu must show `Section — Chapter`, never a serial index alone.
6. Keep wide tables in a scroll container. Do not let them widen the page.
7. Add the V5 print sheet from `assets/print-v5.css`: hide chrome, chapter page-breaks, repeating table headers, orphans and widows, `@page { size: A4; margin: 14mm 12mm }`. Caption Mermaid source; do not leave a bare graph block.
8. Run `python3 scripts/check_guide.py PATH` from this skill directory. Fix failures.
9. Serve over HTTP and check 360×800 and 390×844: `scrollWidth === clientWidth`, `visualViewport.scale === 1`. Do not claim `file://` was tested unless that exact open was logged.
10. If printing is requested, generate an A4 PDF and confirm page size is about 595×842 pt. Do not call the guide clinically validated.

## Reader rules

- Viewport: `width=device-width, initial-scale=1`. Never set `maximum-scale` or `user-scalable=no`.
- Controls use at least 16px text so focus does not force mobile zoom.
- Themes: light, sepia, dark, auto. One preference key. Removing auto must remove the auto class.
- Search results scroll to a stable passage id, not `href="#"`.
- Bookmarks: one versioned schema `{title, anchor, offset, section, chapter, created}`. Migrate older `{title, href}` and `{title, y}` records. Export/import JSON. Storage key stays book-specific (`cgci:reader-v2` for investigation, `som:reader-v2` for medicine).
- Chapter jumps use one navigation path and respect `prefers-reduced-motion`.
- Dialogs use `<dialog>`. Escape closes. Return focus to the opener.
- No remote fonts, CDN scripts, analytics, or login. Embed only fonts the book uses.

## End-to-end workflow

When the user supplies markdown, PDF, or Word and asks for this reader:

1. Do not overwrite the source. Write `NAME_V1.html` beside it.
2. From this skill directory, run:

```bash
python3 scripts/build_guide.py INPUT --title "Book title" --book investigation --out OUTPUT.html
```

`--book medicine` only for a medicine guide. Add `--calculator` only when the source already has the medicine calculator; leave IV iron, low-dose dopamine, norepinephrine, and amino acids disabled in the control, and reject weights outside 0.5–300 kg.
3. Markdown: `#` title, `##` section, `###` chapter. Word: real Heading 1/2/3 styles; tables and lists stay in document order. PDF: only explicit Chapter, Part, and Appendix lines are headings. The builder writes a census and exits 3 when the parse is only a file read. Do not override that gate unless the user accepts the structure.
4. Run `python3 scripts/check_guide.py OUTPUT.html`.
5. Open over HTTP at 360 and 390. Confirm section — chapter labels, no page overflow, and `visualViewport.scale` 1.
6. Compare the shell with `artifacts/BEGINNERS_GUIDE_MOBILE_V4.html`: same header ids, dialog, theme options, bookmark label function, and A4 rule. Content will differ. Do not claim byte-identical output.
7. State file:// limits. Do not call the file clinically validated.

The shell assets in `assets/` are extracted from the V4 investigation reader. Rebuild those assets if the reader shell changes.

| Symptom | Fix |
|---|---|
| Bookmark list is `1 / 54` | Store and display `section — chapter`. Resolve old anchors on open. |
| Chapter select shows only a number | Option text is the label. Put the index in `title`, not at the start. |
| Page pans sideways | Clip the page; scroll tables inside `.table-wrapper`. Do not shrink all text. |
| Print is US Letter | Set `@page { size: A4 }`. |
| Light theme stays dark | Clear `auto-theme` when Light is chosen. |
| `file://` warning | Expected if a local file requests another local file. Do not claim it fixed from an HTTP test. |
