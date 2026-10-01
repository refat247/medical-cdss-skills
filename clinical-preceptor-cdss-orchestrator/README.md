# Clinical Preceptor CDSS Orchestrator (v1.2.0)

Universal Clinical Preceptor & Bedside Case CDSS Orchestrator for physician-authored clinical series, medical vignettes, and preceptor corpora.

Installed (v1.2.0)

## Quick Start

### Pre-scaffold a New Workspace
```powershell
python scripts/orchestrator.py --workspace "D:\NEW_CASES" --init-workspace --clinician-name "Dr. Jane Doe"
```

### Run Autonomous Manufacturing Pipeline
```powershell
python scripts/orchestrator.py --workspace "D:\HABIJABI_FULL" --pipeline auto
```

### Run Runtime Modalities
```powershell
# Socratic Preceptor
python scripts/orchestrator.py --workspace "D:\HABIJABI_FULL" --preceptor "Young male with severe HTN and hypokalemia"

# Visual OSCE Spotter
python scripts/orchestrator.py --workspace "D:\HABIJABI_FULL" --visual-spotter "HABIJABI-001"

# Toxic Drug Never-Events
python scripts/orchestrator.py --workspace "D:\HABIJABI_FULL" --never-events "Linezolid"
```

## Documentation
See [SKILL.md](file:///C:/Users/User/.gemini/config/skills/clinical-preceptor-cdss-orchestrator/SKILL.md) for full 13-modality documentation and [CHANGELOG.md](file:///C:/Users/User/.gemini/config/skills/clinical-preceptor-cdss-orchestrator/CHANGELOG.md) for release notes.
