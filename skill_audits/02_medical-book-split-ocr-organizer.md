# 02 · medical-book-split-ocr-organizer (v1.2.0) — Independent Audit

**Tier:** Critical path (ingest) · **Code:** 568 LOC · **Tests:** 7 pass / 0 fail `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| A- | C | C+ | B | D | **C+** |

## What it does well
- Sensible command set (`init / ingest / auto / status / organize-section / organize-book`), skips existing targets unless `--force` `[C]`.
- Ignores empty `ocr-playground-download*` staging folders instead of ingesting them `[C]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| O1 | High | C | With `--force`, an existing OCR directory is removed with `shutil.rmtree` / `unlink` and then replaced. No dry-run, no backup. OCR output is paid-for, hard-to-recreate data. | Add `--dry-run`; on overwrite, move the old folder to `*.replaced-<timestamp>` rather than deleting; require `--force --yes`. |
| O2 | Medium | I | Matching OCR folders to sections uses `normalize_name` fuzzy name matching. A mis-match would put one chapter's OCR under another with only a printed `[MOVED]` line. Tests are 7, mostly structural. | Print a match table and require confirmation when match confidence is not exact; add tests with near-duplicate chapter names. |
| O3 | Medium | C | Hard-coded Windows defaults: `C:\Users\User\Downloads`, `D:\01_Medical_Study\...` (6 code lines, 9 doc lines); needs `uv run` per docs. | Take paths only from args/env (`CDSS_DOWNLOADS_DIR` already exists in the orchestrator; reuse it). |
| O4 | Low | C | Several `except Exception` blocks (init, ingest cleanup) print or swallow errors; ingest cleanup `pass`es silently. | Collect failures and exit non-zero if any move failed. |
| O5 | Low | C | SKILL.md handover step points to `python -m preready.runner` with a Windows path. | Use relative skill paths. |

## Verdict
Functionally sound for the author's Windows workflow, but its destructive overwrite has no safety net and its folder matching is under-tested.

**Top 3 actions:** (1) replace delete-on-force with rename-aside, (2) match-confidence confirmation, (3) remove hard-coded paths.
