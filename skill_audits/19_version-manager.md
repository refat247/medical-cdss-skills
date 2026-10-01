# 19 · version-manager (v1.1.1) — Independent Audit

**Tier:** Platform (but used by the pipeline) · **Code:** 548 LOC · **Tests:** 8 pass / 0 fail `[M]`

| Goal fit | Safety | Tests | Docs accuracy | Portability | **Overall** |
|:-:|:-:|:-:|:-:|:-:|:-:|
| B | C+ | B | B | B | **B-** |

## What it does well
- Scans many declaration kinds (SKILL.md frontmatter and heading, `__init__.__version__`, `pyproject.toml`, `package.json`, test assertions, README), `--inspect`, `--verify`, `--bump`, and a `--suite` mode across skills `[C]`. Keep-a-Changelog and SemVer reference docs included.
- Suite verification runs cleanly here: "19/19 skills, 0 drift" `[M]`.

## Findings
| ID | Sev | Ev | Finding | Fix |
|---|---|---|---|---|
| V1 | **High** | M,C | **Misses version constants it does not name.** The Python-constant scanner matches only `PIPELINE_VERSION | VERSION | APP_VERSION`. `SKILL_VERSION = "1.6.0"` in `davidson-ocr-preready/preready/auditor.py` (skill is 1.7.5) is invisible to it, so "0 drift" is false assurance. It also does not catch `skill_name`/provenance strings. | Match any `*_VERSION` and `skill_version:`; add a repo-wide grep for the old version string after a bump. |
| V2 | **High** | C | **Intra-skill only.** There is no notion of "A requires B ≥ x". `--suite --verify` cannot detect cross-skill incompatibility. | Add `requires:` frontmatter and a compatibility check (see master report F5). |
| V3 | Medium | C | **Broad rewrite regexes:** in `__init__.py` it rewrites every `(vX.Y.Z)` and in README every `` `vX.Y.Z` `` and `# … (vX.Y.Z)` heading, so unrelated historical references (e.g. "fixed in `v2.6.3`") can be silently changed to the new version. | Restrict to the declared declaration lines; show a diff and require `--yes`. |
| V4 | Medium | C | **No `--dry-run` and no atomicity.** Files are rewritten one at a time; a failure halfway leaves a partially bumped skill with no rollback. | Compute all new contents first, write via temp files, then rename; add `--dry-run`. |
| V5 | Low | I | Does not create a git tag/commit and does not verify CHANGELOG has an entry for the new version (not seen in code). | Optional `--tag` and a changelog check in `--verify`. |

## Verdict
Useful and tested, but its "19/19 consistent" output should not be read as release-readiness. V1 and V2 are why the repo's version story is weaker than it looks.

**Top 3 actions:** (1) scan `*_VERSION` and `skill_version`, (2) cross-skill `requires:`, (3) dry-run + atomic write.
