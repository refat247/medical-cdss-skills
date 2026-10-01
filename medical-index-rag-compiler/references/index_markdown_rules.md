# Index Markdown Formatting Rules

Requirements for input index markdown files processed by `medical-index-rag-compiler`.

---

## 1. Primary Entries vs Sub-facets
- **Primary Concepts**: Lines starting with a capital letter (e.g., `Aortic stenosis`, `Cardiogenic shock`).
- **Sub-facets**: Indented lines or lines starting with lowercase letters/prepositions:
  - Starting with: `in `, `of `, `for `, `with `, `as `, `and `, `vs. `
  - Or lines where `line[0].islower()` is true.

---

## 2. Acronyms & Abbreviations
- Format: `Full Medical Term (ACRONYM)`
- Example: `Accelerated idioventricular rhythm (AIVR)`
- Acronyms must be at least 2 characters and contain uppercase letters or numbers.

---

## 3. Typographical Locators
- Table citations: Postfixed with `t` (e.g., `1842t`)
- Figure citations: Postfixed with `f` (e.g., `1205f`)
- Color plate citations: Postfixed with `c` (e.g., `840c`)
- Comprehensive ranges: Hyphenated or en-dashed page numbers (e.g., `60–64` or `112-118`)

---

## 4. Cross-References
- Use explicit editorial syntax:
  - `See [Target Term]`
  - `See also [Target Term]`
