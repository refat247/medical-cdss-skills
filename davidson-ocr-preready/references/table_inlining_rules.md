# Table Inlining & Box Heading Rules

## 1. Table Placement Protocol

When raw OCR produces detached table files (`pages/page-*/tbl-*.md`), they must be inlined into the primary markdown document at the exact point of the original citation.

---

## 2. Heading Formatting

Every inlined table must be preceded by an explicit Level 3 header (`###`) containing the table or box number:

```markdown
### 1.1 Root causes of diagnostic error in studies

| Error category | Examples |
| --- | --- |
| No fault | Unusual presentation of a disease |
| System error | Inadequate diagnostic support |
| Human cognitive error | Inadequate data-gathering |
```

### Why `###` is required:
* The Davidson RAG parser indexes `###` and `Box X.Y` as discrete clinical containers or micro-chunk headings.
* Plain text titles without markdown header syntax risk merging into adjacent paragraphs.

---

## 3. Footnotes and Attributions

Footnotes (e.g. *Adapted from Graber et al.*) should be included as the last row of the table or as an italicized line directly below the table block.
