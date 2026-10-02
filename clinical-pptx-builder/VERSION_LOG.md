# Version log

| Version | Date | Commit / baseline | Status | Change | Evidence |
|---|---|---|---|---|---|
| 0.2.1 | 2026-09-08 | `5761e47` | PROVISIONAL / operational | Added user-stated typography gates, coverage ledger, sparse/dense slide repair guidance, and rejected-decoration handling after PUD 2026 repair failure analysis | `quick_validate.py` passed; regression 6/6 passed |
| 0.2.0 | 2026-09-06 | `68fe558` reliability baseline; package finalization in Git history | PROVISIONAL / operational | Added deck specification, six fixtures, regression runner, release docs, icon, and repaired v4 workflow | `quick_validate.py` passed; regression 6/6 passed |
| 0.1.0 | 2026-09-06 | `5bc005c` | PROVISIONAL | Initial clinical PPTX builder package | Initial validation and first regression run |

## Release evidence

- The package keeps its full `.git` history when distributed in the release ZIP.
- The final package commit is the newest commit reported by `git log --oneline` at release time.
- The ZIP is tested with `unzip -t` after creation.
