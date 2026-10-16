# Bilingual reference HTML handoff

Use for compact reference entries with doses, preparations, examples or comparison statements. General textbook prose keeps its source paragraph structure.

## Responsibilities

- Curator owns evidence, source-set lock, terminology, Bengali explanation, unresolved states and final artifact audit.
- Offline Study Guide owns explicit block rendering, source-span integrity, navigation, offline assets and responsive/print behavior.
- Load both named skills explicitly when combining them. Reading one does not auto-activate the other. Use the existing Curator specialist-builder route; no third skill is required. Consider a separate orchestrator only when several recurring destinations require reusable dispatch/state handling.

## Layout and language

Keep technical identity, clinical wording, values, units and abbreviations in their supplied language. Explain meaning in concise Bengali beneath the relevant entry; do not duplicate every line in two languages. Mark explanations with lang="bn". Separate dose, concentration, preparation, example, brands and review statements into source-ordered rows when those boundaries are supported by the source.

Use one column for narrative entries at all widths. Keep regular syrup/drop and DS/Forte examples with their own preparation; keep loading, dilution and maintenance order. Preserve conditional/alternative/comparison relationships and unresolved source warnings. Retain true comparison tables and their headers/cells in a horizontal scroll container. Do not turn a table into unpaired paragraphs.

Do not infer boundaries by decimal points, abbreviations, slashes, semicolons or arbitrary sentence splitting. If ownership is unclear, retain the original passage, record READABILITY REVIEW REQUIRED and request source clarification only when needed. A layout operation does not verify a dose or authorize clinical rewriting.

## Source-bound transfer

Provide the exact source artifact identity/hash and location, the source wording, the supported row boundaries and formulation membership, the separately approved Bengali explanation, and unresolved issues. Record source type honestly: a Markdown-derived build is not a direct PDF build just because the Markdown came from a PDF.

For Offline Study Guide v1.3.0+, use the explicit reference-entry-v1 JSON block described in references/reference-layout.md in the builder package. The schema is opt-in. Legacy Markdown prose and bullets are retained and density findings reported, not automatically rewritten. Unknown or ambiguous structure remains a review item. A supplied Bengali explanation is preserved; code does not generate or fact-check it.

## Artifact gates

1. Match each rendered source span, in order, to the locked source; verify full coverage, units, values, qualifiers, links, table cells and formulation ownership. Compare final artifact to the immediately previous artifact and recheck closed blockers.
2. Run the builder static checker and retain its census, density findings, source/entry counts and source hashes. Static checks compare embedded source metadata to rendered spans; independently compare that embedded source to the original locked input. Self-consistent metadata alone does not establish provenance.
3. Inspect actual HTML over HTTP at 360×800, 390×844 and a desktop width. Check no page overflow, pinch zoom remains enabled, Bengali font fallback/line spacing, themes, search jumps, chapter links, bookmarks, dialogs, keyboard focus and escaping. When file:// use is promised, test that exact launch separately. If print requested, inspect generated A4 pages for clipping, orphans and formulation splits.
4. Record browser/visual/interaction QA as PASS, FAIL or NOT EXECUTED with environment and screenshots/logs. A static PASS is not browser QA or exported-PDF proof. Unavailable browser access leaves that gate open; do not claim readability/freeze completion.
5. Return canonical output identity, hashes, counts, density findings, unresolved claims and verification states. Bengali explanations do not establish clinical validation.
