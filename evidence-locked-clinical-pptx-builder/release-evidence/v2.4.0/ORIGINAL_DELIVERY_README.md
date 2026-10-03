# Downloads: evidence-locked-clinical-pptx-builder v2.4.0

**Want one file? Download `ALL_DELIVERABLES.zip`** (everything below).

| Folder | File | Use it for |
|---|---|---|
| `1-skill-full/` | `evidence-locked-clinical-pptx-builder-v2.4.0.zip` | **The complete skill.** 248 files; unzip it over the skill folder in your repo. |
| `2-skill-key-files/` | `SKILL.md` | The updated skill instructions (new section 17A: VISUAL_POLISH) |
| | `visual_polish_protocol.md` | Full contract, design system, workflow, limits (lives in `docs/` in the skill) |
| | `scripts/visual_polish/polish.py`, `style.py`, `verify.py` | The polish engine, design tokens, and content-lock gate |
| | `test_v2_4_visual_polish.py` | The 21 new regression tests (lives in `tests/`) |
| | `CHANGELOG.md`, `README.md`, `MIGRATION_NOTES_v2.3.0_to_v2.4.0.md`, `VERSIONING_DECISION_v2.4.0.md` | Release notes |
| `3-github/` | `evidence-locked-clinical-pptx-builder-v2.4.0.patch` | `git apply` onto the repo (recommended) |
| | `changed-files-only-v2.4.0.zip` | Only the 31 added/changed files, in repo paths. Unzip at the repo root. |
| | `CHANGED_FILES.txt` | List of those 31 files |
| | `HOW_TO_COMMIT.md` | Step-by-step commit instructions |
| `4-polished-deck/` | `DYS_2026_Master_Core_v1.5_POLISHED_dense_case_reveal.pptx` | The test output on your deck (193 slides, editable PowerPoint) |
| `5-test-evidence/` | `test-run-evidence.zip` | Polish/verify reports, render manifest, blank per-slide review ledger, contact sheets |

The files in `2-skill-key-files/` are copies for reading. The zip in `1-skill-full/` is the one to install.

**Checked:** 110/110 tests pass; package manifest verified (247 rows); the patch applies cleanly to `main`.
