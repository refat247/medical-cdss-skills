# evidence-locked-clinical-pptx-builder v2.4.0: how to commit

Built against `refat247/medical-cdss-skills@main` (v2.3.0, commit `9a16422`).
31 files changed, +1680 / −87. Tests: **110 passed** (89 original + 21 new).
`PACKAGE_MANIFEST.md` regenerated and verified (247 rows).

## Option A: apply the patch (recommended, keeps history clean)

```bash
cd medical-cdss-skills
git checkout -b visual-polish-v2.4.0
git apply --check evidence-locked-clinical-pptx-builder-v2.4.0.patch
git apply evidence-locked-clinical-pptx-builder-v2.4.0.patch
cd evidence-locked-clinical-pptx-builder && python -m pytest -q   # expect 110 passed
cd .. && git add -A evidence-locked-clinical-pptx-builder
git commit -m "evidence-locked-clinical-pptx-builder v2.4.0: content-locked VISUAL_POLISH mode"
git push -u origin visual-polish-v2.4.0
```

## Option B: replace the folder

Unzip `evidence-locked-clinical-pptx-builder-v2.4.0.zip` over the repo's
`evidence-locked-clinical-pptx-builder/` folder, then run the tests and commit as above.

## After committing

Remember to switch the repo back to **private** if you made it public for this.

## Test-run evidence (`test-run/`)

Run on `assets/design_references/DYS_2026_Master_Core_v1.5_VISUAL_REPAIR_PRECANONICAL.pptx`:

| Profile | POLISHED | SKIPPED | SPLIT_REQUIRED | Content lock | Floors & fit | Repo preflight |
|---|---|---|---|---|---|---|
| `dense_case_reveal` (approval recorded as a test) | 189 | 0 | 4 (slides 12, 33, 65, 140) | PASS | PASS | PASS |
| `projector_default` | 145 | 0 | 48 | PASS | PASS | PASS |

- All 193 slides were rendered with LibreOffice 25.2. Contact sheets are in `cs_1..6.png`, and the render manifest has the slide-set SHA-256.
- `visual_review_ledger.csv` is the **blank** per-slide ledger produced by the gate. It has not been filled in, so this test run is
  `RENDER-UNCERTIFIED` / `POWERPOINT-RENDER-PENDING` under SKILL.md section 19. No release status is claimed.
