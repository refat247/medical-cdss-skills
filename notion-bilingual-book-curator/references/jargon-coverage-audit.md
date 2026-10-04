# Jargon Coverage Audit

Use this reference for MODE F or whenever book readability depends on technical vocabulary coverage.

## Goal

Make the book self-contained enough for the intended reader without turning a local appendix into an enterprise-wide dictionary.

## Audit sequence

1. Extract or inventory technical terms/acronyms actually used in the artifact.
2. Read the existing local glossary.
3. If the user requests it and the canonical workspace glossary is available, compare against that glossary.
4. Normalize aliases and case variants.
5. Classify each candidate:

- DEFINED LOCALLY
- READER-CRITICAL MISSING
- EXTERNAL-GLOSSARY ONLY
- NO LOCAL ENTRY NEEDED
- PROPER NAME / MODEL / PRODUCT — NOT A GLOSSARY HEADWORD
- ALIAS / GROUP WITH CANONICAL HEADWORD

## Reader-critical test

A term is a strong candidate for local definition when misunderstanding it could materially impair:
- comprehension of the architecture;
- interpretation of evidence/validation state;
- understanding of benchmark results;
- interpretation of workflow or safety gates;
- ability to follow the book's Reading Routes.

Do not add every provider, model, framework, proper noun, file format, or common computing term merely because it occurs.

## Group aliases

Prefer one grouped headword when concepts are functionally linked in this book.

Examples:
- Candidate k / top-k / candidate depth
- Parent/child retrieval / hierarchical chunking
- Long context / context window / lost-in-the-middle

Do not create multiple near-identical entries unless the distinctions matter to the reader.

## Bilingual glossary entry

Preferred structure:

### Technical term — English
**সহজ অর্থ:** Bengali conceptual explanation.  
**Why it matters:** Bengali reasoning.  
**Project / clinical mapping:** specific application in the book.

Keep established technical terminology, acronyms, model names, metrics, labels and literal identifiers in English.

## Locked glossary patch

Before sending glossary content to an external builder:
- finalize the exact grouped headword set;
- lock the exact insertion text;
- state exact insertion location;
- state expected entry count;
- state expected repeated field counts when useful;
- prohibit the builder from inventing extra entries or paraphrasing locked definitions.

## Post-build verification

Verify the actual exported artifact, not only the builder report.

Check:
- every supplied headword is present;
- no supplied headword is duplicated;
- insertion boundaries are correct;
- expected field counts match;
- existing glossary entries remain intact;
- navigation still targets the glossary correctly;
- Bengali renders cleanly.

A builder statement such as "40/40 inserted" is not a substitute for independent artifact verification.
