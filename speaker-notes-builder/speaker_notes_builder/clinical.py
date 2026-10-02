from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HIGH_RISK_PATTERNS = {
    "dose": re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|µg|g|ml|units?)\b", re.I),
    "titration": re.compile(r"\b(?:titrate|titration|increase|escalat|start(?:ing)? dose|maintenance dose|missed dose)\b", re.I),
    "approval": re.compile(r"\b(?:approved|licensed|indication|authorized|authorised)\b", re.I),
    "pregnancy": re.compile(r"\b(?:pregnan|contracept|fertility|lactat|breastfeed)\w*\b", re.I),
    "contraindication": re.compile(r"\b(?:contraindicat|boxed warning|black box|MTC|MEN2|hypersensitiv)\w*\b", re.I),
    "paediatric": re.compile(r"\b(?:paediatric|pediatric|age\s+\d+|years? old)\b", re.I),
}

LOCAL_TERMS = re.compile(r"\b(?:Bangladesh|DGDA|local label|locally approved|approved in Bangladesh)\b", re.I)
UNQUALIFIED_LOCAL_APPROVAL = re.compile(r"(?:\b(?:approved|licensed)\s+(?:in|for)\s+Bangladesh\b|\bBangladesh[-\s]+(?:approved|licensed)\b|\b(?:approved|licensed)\s+by\s+DGDA\b|\bDGDA[-\s]+(?:approved|licensed)\b)", re.I)
QUALIFIER_TERMS = re.compile(r"\b(?:verify|not retrieved|uncertain|jurisdiction|according to|product-label evidence|current local label|must be checked|check separately)\b", re.I)


def lint_scripts(project_dir: str | Path) -> dict[str, Any]:
    project = Path(project_dir)
    scripts_path = project / "scripts.json"
    if not scripts_path.exists():
        report = {"status": "UNCERTIFIED", "blockers": ["scripts.json not found"], "warnings": [], "slides": []}
        (project / "clinical_lint.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    data = json.loads(scripts_path.read_text(encoding="utf-8"))
    manifest = {}
    manifest_path = project / "deck_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = manifest.get("profile", "default")
    ledger_path = project / "claim_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"claims": []}
    ledger_by_slide = {}
    for claim in ledger.get("claims", []):
        ledger_by_slide.setdefault(int(claim.get("slide", 0)), []).append(claim)

    blockers = []
    warnings = []
    slide_reports = []
    for rec in data.get("slides", []):
        if not rec.get("included", True):
            continue
        text = " ".join([
            rec.get("main_script", ""),
            rec.get("compressed_script", ""),
            rec.get("optional_expansion", ""),
        ])
        status = rec.get("claim_status", "UNVERIFIED")
        hits = [name for name, pat in HIGH_RISK_PATTERNS.items() if pat.search(text)]
        slide_blockers = []
        slide_warnings = []
        if status == "BLOCKED":
            slide_blockers.append("claim_status is BLOCKED")
        if hits and status == "UNVERIFIED":
            slide_blockers.append(f"high-risk content is UNVERIFIED: {', '.join(hits)}")
        slide_claims = ledger_by_slide.get(int(rec.get("slide", 0)), [])
        if profile == "clinical_cme" and hits and not slide_claims:
            slide_blockers.append("high-risk spoken content has no claim_ledger.json entry for this slide")
        bad_claims = [c for c in slide_claims if c.get("status") in {"UNVERIFIED", "BLOCKED"}]
        if hits and bad_claims:
            slide_blockers.append("claim ledger contains UNVERIFIED/BLOCKED high-risk claim(s)")
        if LOCAL_TERMS.search(text) and UNQUALIFIED_LOCAL_APPROVAL.search(text) and not QUALIFIER_TERMS.search(text):
            slide_blockers.append("local approval wording lacks an explicit verification/jurisdiction qualifier")
        if LOCAL_TERMS.search(text) and status not in {"SUPPORTED", "JURISDICTION_SENSITIVE", "SOURCE_PARTIAL", "SOURCE_CONFLICT"}:
            slide_warnings.append(f"local/jurisdiction wording has status {status}")
        for b in slide_blockers:
            blockers.append(f"Slide {rec.get('slide')}: {b}")
        for w in slide_warnings:
            warnings.append(f"Slide {rec.get('slide')}: {w}")
        slide_reports.append({"slide": rec.get("slide"), "high_risk_hits": hits, "claim_ledger_entries": len(slide_claims), "status": status, "blockers": slide_blockers, "warnings": slide_warnings})

    report = {
        "status": "FAIL" if blockers else ("PASS_WITH_WARNINGS" if warnings else "PASS"),
        "blockers": blockers,
        "warnings": warnings,
        "slides": slide_reports,
    }
    (project / "clinical_lint.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
