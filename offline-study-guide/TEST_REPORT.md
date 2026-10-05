# offline-study-guide v1.2.1 verification report

Date: 2026-10-01

## Scope

Governance-only PATCH over the proven v1.2.0 capability release. Runtime/parser/reader behavior is intentionally unchanged. v1.2.1 adds version mirrors, package metadata, root-correct install packaging, and release verification. The functional baseline below remains the v1.2.0 capability evidence and is re-run unchanged for v1.2.1.

## Version-governance verification

- Canonical version: `SKILL.md` → `metadata.version`.
- Mirrors: visible SKILL version, `VERSION`, `README.md`, `agents/openai.yaml`, manual activation, activation smoke test, changelog, and package manifest.
- Release verifier: `python3 scripts/verify_release.py`.
- Functional suite retained unchanged: 59/59 expected.
- Git/Notion/install/runtime states are reported separately and are not inferred from package correctness.

## Automated regression

- Previous v1.1.4 suite retained: 54/54 PASS.
- New layout-aware PDF checks: 5/5 PASS.
- Expanded packaged suite: 59/59 PASS.

New checks cover guarded textbook-mode activation, source-page visual fallback count, duplicate-heading suppression when a smaller local subheading repeats a source-contents label, coordinate-based boxed-table cell reconstruction, and checker acceptance of the final layout-aware artifact.

## External integration test

Test source: `Davidson_25_01_Clinical decision-making.pdf`

Source SHA-256: `8b186f19012cdd03e0141205db099867fabe24ced0b30caabbac9bfcc9526690`

Observed final census:

- status: PARSE SUCCESS
- layout mode: `fitz-column-aware-textbook`
- pages: 12
- sections: 1 renderer container (`Clinical decision-making`)
- navigation chapters: 27
- source contents matches: 25/25 (1.0)
- semantic numbered boxed tables: 6
- source boxed tables: 7
- visual-only boxed tables: 1
- embedded source-page fallbacks: 12
- dropped source blocks: 0
- duplicate navigation chapter titles: 0
- replacement/decorative control glyphs in reader text: 0
- static checker: PASS

The supplied source contents includes the chapter topics from Introduction through Answers to problems, and the later pages include Further information and Multiple Choice Questions; the layout-aware reader preserved these as navigation/content rather than inventing a dummy chapter.

## Source-fidelity strategy

The searchable text layer is a layout-aware extraction. For complex figures, diagrams, and the one boxed table not reconstructed semantically, the embedded original-page appendix is the fidelity boundary. It preserves the source visual but does not claim semantic extraction of the figure/table.

## Known limitations

- The layout-aware mode is intentionally narrow and will not activate without a strongly corroborated title/contents/body-heading pattern.
- Scanned PDFs remain OCR-required.
- Complex diagrams and some visually structured boxes may remain visual-only; source-page fallbacks are embedded rather than guessed.
- The static checker does not launch a browser. In this execution environment Chromium could not start because its GPU process failed; no HTTP/mobile browser claim is made for this run. The reader shell itself was not materially redesigned in v1.2.0, and source-page images are constrained to `max-width:100%`.
