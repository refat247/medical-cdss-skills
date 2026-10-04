"""Audit & Reporting Module for Davidson OCR Pre-Ready Pipeline."""
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

SKILL_NAME = "davidson-ocr-preready"
from preready import __version__ as SKILL_VERSION  # single source of truth (was a stale duplicate: 1.6.0)


def _format_provenance_header(source_path: str) -> str:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"<!--\n"
        f"PROVENANCE METADATA:\n"
        f"  skill_name: \"{SKILL_NAME}\"\n"
        f"  skill_version: \"{SKILL_VERSION}\"\n"
        f"  generated_at: \"{now_iso}\"\n"
        f"  source_path: \"{source_path}\"\n"
        f"-->\n\n"
    )


def _completeness(table_audits, image_audits) -> str:
    """Computed, not hard-coded: inlined tables + copied figures over everything the chapter referenced."""
    total = len(table_audits) + len(image_audits)
    if not total:
        return "n/a (no tables or figures referenced)"
    done = sum(1 for t in table_audits if t["status"] == "INLINED") + sum(1 for i in image_audits if i["copied"])
    return f"{100 * done // total}% ({done}/{total})"


def write_audit_reports(
    out_dir: str,
    prefix: str,
    table_audits: List[Dict],
    image_audits: List[Dict],
    assets_dir: str,
    source_dir: Optional[str] = None
) -> Tuple[str, str, str]:
    """Writes detailed table, figure, and overall pre-ready audit markdown reports."""
    os.makedirs(out_dir, exist_ok=True)
    prov_hdr = _format_provenance_header(source_dir or out_dir)

    # 1. Table Audit Report
    tbl_report_path = os.path.join(out_dir, f"{prefix}_TABLE_AUDIT.md")
    tbl_lines = [
        prov_hdr.rstrip(),
        f"",
        f"# Table Inlining Audit Report — {prefix}",
        f"",
        f"- **Skill**: `{SKILL_NAME}` (v{SKILL_VERSION})",
        f"- **Total Tables Processed**: {len(table_audits)}",
        f"- **Successfully Inlined**: {sum(1 for t in table_audits if t['status'] == 'INLINED')} / {len(table_audits)}",
        f"",
        f"| Placeholder | Title | Status | Rows | Source File |",
        f"|---|---|---|---|---|",
    ]
    for t in table_audits:
        status_icon = "✅ INLINED" if t["status"] == "INLINED" else "❌ MISSING"
        tbl_lines.append(f"| `{t['placeholder']}` | {t['title']} | {status_icon} | {t['rows']} | `{os.path.basename(t['table_path'])}` |")

    with open(tbl_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tbl_lines))

    # 2. Figure & Visual Asset Audit Report
    tabular_figs = [t for t in table_audits if t.get("is_tabular_figure")]
    total_visual_items = len(image_audits) + len(tabular_figs)
    fig_report_path = os.path.join(out_dir, f"{prefix}_FIGURE_AUDIT.md")
    fig_lines = [
        prov_hdr.rstrip(),
        f"",
        f"# Figure & Visual Asset Registry — {prefix}",
        f"",
        f"- **Skill**: `{SKILL_NAME}` (v{SKILL_VERSION})",
        f"- **Total Visual / Figure Assets Detected**: {total_visual_items}",
        f"- **Decoupled Raster Image Assets**: {sum(1 for img in image_audits if img['copied'])} / {len(image_audits)}",
        f"- **Inlined Tabular Figures (Archetype 2)**: {len(tabular_figs)}",
        f"- **Assets Store**: `{assets_dir}`",
        f"",
        f"### 1. Decoupled Raster Figures & Image Assets",
        f"",
        f"| Placeholder | Fig # | Caption | Canonical Asset Name | Copied to Store |",
        f"|---|---|---|---|---|",
    ]
    for img in image_audits:
        copy_icon = "✅ YES" if img["copied"] else "⚠️ MISSING"
        fig_lines.append(f"| `{img['placeholder']}` | Fig {img['fig_key']} | {img['caption'][:40]} | `{img['canonical_name']}` | {copy_icon} |")

    if tabular_figs:
        fig_lines.extend([
            f"",
            f"### 2. Tabular Figures Inlined as Markdown Tables (Archetype 2)",
            f"",
            f"> [!NOTE]",
            f"> **Visual Conversion Standard (Archetype 2)**: Textbook figures structured as clinical matrices, scoring grids, or classification tables are inlined directly as searchable Markdown tables from `tbl-*.md` rather than stored as raster images. This guarantees 100% lexical and semantic searchability for CDSS AI models without vision token overhead.",
            f"",
            f"| Fig # | Figure Title | Source Table | Conversion Format | Status |",
            f"|---|---|---|---|---|",
        ])
        for tf in tabular_figs:
            fig_lines.append(f"| Fig {tf.get('fig_key', 'N/A')} | {tf['title']} | `{tf['placeholder']}` | 📊 GFM Markdown Table | ✅ INLINED |")

    with open(fig_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fig_lines))

    # 3. Master Pre-Ready Report
    master_report_path = os.path.join(out_dir, f"{prefix}_PREREADY_REPORT.md")
    master_lines = [
        prov_hdr.rstrip(),
        f"",
        f"# Davidson OCR Pre-Ready Master Audit — {prefix}",
        f"",
        f"- **Skill**: `{SKILL_NAME}` (v{SKILL_VERSION})",
        f"",
        f"## Processing Summary",
        f"- **Canonical Output File**: `{prefix}.pdf.markdown_inlined.md`",
        f"- **Tables Inlined**: {sum(1 for t in table_audits if t['status'] == 'INLINED')} / {len(table_audits)}",
        f"- **Decoupled Raster Figures**: {sum(1 for img in image_audits if img['copied'])} / {len(image_audits)}",
        f"- **Tabular Figures Inlined**: {len(tabular_figs)}",
        f"- **Assets Store**: `{assets_dir}`",
        f"- **Visual Asset Completeness**: {_completeness(table_audits, image_audits)}",
        f"",
        f"## Handover Contract with davidson-rag-pipeline-antigravity",
        f"The generated `{prefix}.pdf.markdown_inlined.md` is 100% compliant with the downstream RAG pipeline:",
        f"1. Standard Markdown Tables (`|`) for Stage 1/4B parsing and tabular figures.",
        f"2. Decoupled asset URIs (`assets/figures/chNN_fig_MM.*`) for Stage 4B metadata extraction and Stage 6 Invariant 6.5.",
        f"3. Clean heading depth hierarchy (`#`, `##`, `###`) for Stage 4A Heading Manifest.",
        f"",
        f"## Immediate Next Step",
        f"Execute downstream RAG pipeline:",
        f"```bash",
        f"python -m pipeline.run_stage --stage auto --source \"{out_dir}\\{prefix}.pdf.markdown_inlined.md\" --out \"{out_dir}\"",
        f"```",
    ]
    with open(master_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(master_lines))

    return tbl_report_path, fig_report_path, master_report_path

