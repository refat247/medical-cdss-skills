# Figure Naming Standards & Asset Management

## Canonical Figure Naming Convention

All figure assets extracted from Davidson 25th Edition must strictly follow the format:
```
ch{NN}_fig_{MM:02d}.{ext}
```
* `{NN}`: Two-digit chapter number (e.g. `01`, `02`, `18`).
* `{MM}`: Two-digit figure number matching the textbook caption (e.g. `01` for Fig. 1.1, `12` for Fig. 1.12).
* `{ext}`: Preserved original image extension (`.jpeg`, `.png`, `.webp`).

### Examples:
- `Fig. 1.1` $\to$ `ch01_fig_01.jpeg`
- `Fig. 18.4` $\to$ `ch18_fig_04.png`
- `Fig. 21.12` $\to$ `ch21_fig_12.png`

### Multi-Panel / Sub-Figure Numbering:
When multiple images share a single textbook figure citation (e.g. Panel A, Panel B):
- Primary image: `ch01_fig_01.jpeg`
- Subsequent images: `ch01_fig_01_sub01.jpeg`, `ch01_fig_01_sub02.jpeg`

---

## Tabular Figures (Archetype 2) in Figure Asset Registry

When a textbook figure (e.g. `Fig. 1.6`, `Fig. 3.8`, `Fig. 6.3`) is structured as a clinical matrix, scoring grid, or data table:
1. It is extracted by OCR as a structured table (`tbl-*.md`).
2. It is inlined directly as a native GFM Markdown table (`| ... | ... |`) to guarantee 100% lexical and semantic searchability for CDSS AI models.
3. It is explicitly recorded in `{PREFIX}_FIGURE_AUDIT.md` under **Tabular Figures Inlined as Markdown Tables (Archetype 2)** with its corresponding `Fig. X.Y` key, title, and source table placeholder.

---

## Distributed Per-Chapter Directory Layout

The canonical assets directory layout is generated directly within each chapter directory:
```
<CHAPTER_DIR>/
├── markdown.md                            <-- Raw OCR Input
├── pages/                                 <-- Page directories (tbl-*.md, img-*.jpeg)
├── {PREFIX}.pdf.markdown_inlined.md       <-- Primary Pipeline Input (Inlined Canonical)
├── assets/figures/                        <-- Per-Chapter Decoupled Asset Store
│   ├── ch01_fig_01.jpeg
│   └── ch01_fig_02.jpeg ...
├── {PREFIX}_TABLE_AUDIT.md                <-- Inlined Table Verification
├── {PREFIX}_FIGURE_AUDIT.md               <-- Decoupled Figure & Visual Asset Registry
└── {PREFIX}_PREREADY_REPORT.md            <-- Master Scorecard
```

When deploying downstream to CDSS production, the `*/assets/figures/` tree is mirrored to your CDN or Object Storage (S3 / Cloudflare R2 / GCS) without altering chunk frontmatter relative paths (`assets/figures/chNN_fig_MM.ext`).
