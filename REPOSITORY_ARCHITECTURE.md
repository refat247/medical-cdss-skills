# Repository Architecture and Extraction Policy

## Decision

`medical-cdss-skills` remains the canonical monorepo for the skill ecosystem. A skill is not moved to an independent repository merely because it has its own `SKILL.md`, tests, changelog, or version.

The default is **monorepo + independently versioned skill package**. Extraction is an explicit promotion step.

## Why

The CDSS/RAG subsystem has real cross-skill orchestration and handover contracts. Keeping it together preserves atomic changes, integration testing, shared governance, and simple local installation. General-purpose skills can still be independently packaged and released from their top-level directories.

## Current classification

### A — Keep in this monorepo: coupled CDSS/RAG subsystem

- `medical-cdss-unified-orchestrator`
- `clinical-preceptor-cdss-orchestrator`
- `harrison-cdss-navigator`
- `hurst-cdss-navigator`
- `kumar-cdss-navigator`
- `kawsar-habijabi-cdss-navigator`
- `cdss-retrieval-packager`
- `davidson-rag-pipeline-antigravity`
- `davidson-ocr-preready`
- `medical-book-split-ocr-organizer`
- `medical-index-rag-compiler`
- `medical-rag-orchestrator`
- `cdss-bridge-note-publisher`
- `cdss-unicode-mojibake-guard`

These packages participate in corpus manufacturing, retrieval, packaging, navigation, publishing, or orchestration contracts. Splitting them would introduce cross-repository dependency/version coordination without a demonstrated benefit.

### B — Keep for now; independently releasable and eligible for later extraction

- `notion-workspace-curator`
- `notion-content-auditor`
- `research-method-curator`
- `humanizer-niqs-bridge`
- `humanizer`
- `mobile-first-google-sheets`
- `speaker-notes-builder`
- `offline-study-guide`
- `version-manager`
- `antigravity-protocol`
- `ultimate-protocol`
- `token-audit`
- `clean-my-ai-harness`
- `clinical-pptx-builder`

These have useful standalone identities, but separate repositories are not required until independent consumers or release operations justify the extra governance.

### C — First extraction candidate

- `evidence-locked-clinical-pptx-builder`

It has the strongest independent-product characteristics: substantial runtime source, tests, templates, release evidence, migration/versioning material, reference outputs, integrity ledgers, and a release lifecycle that is meaningful outside the CDSS/RAG manufacturing chain.

**Status: candidate, not yet extracted.** Extraction should preserve history/evidence and must not create two writable canonical sources.

## Extraction gate

A package SHOULD move to an independent repository only when all of the following are true:

1. **Independent purpose** — useful without the medical-CDSS monorepo.
2. **Independent release lifecycle** — changes/releases need not be synchronized with sibling skills.
3. **Independent consumers** — installation or reuse outside this repository is real or imminent.
4. **Low runtime coupling** — no undeclared sibling-directory assumptions; cross-package dependencies are explicit.
5. **Portable paths** — no machine-specific `file://` or absolute installation links in package documentation/runtime contracts.
6. **Self-contained QA** — tests and release verification can run from the extracted repository.
7. **Self-contained governance** — README, license/notices, changelog/version source, contribution/release policy are sufficient.
8. **Canonical-source plan** — migration defines exactly one writable canonical source after extraction.
9. **History/evidence preservation** — release evidence, provenance and hashes remain recoverable.
10. **Migration benefit exceeds overhead** — separate Issues, Actions, security, releases, dependency updates and PR coordination provide concrete value.

If any gate fails, keep the package in the monorepo.

## Extraction procedure

1. Freeze the source package at a verified commit.
2. Audit and remove machine-specific/cross-monorepo path assumptions.
3. Define explicit dependencies and supported installation modes.
4. Preserve relevant Git history where practical.
5. Create the independent repository and import the verified package.
6. Re-run its full test/release-evidence gates in the new repository.
7. Replace the old monorepo directory with either a migration pointer or other deliberate compatibility mechanism; do not maintain two canonical copies.
8. Update orchestrators/catalog links only after the new repository passes verification.
9. Tag the first independent release.
10. Re-audit both repositories for broken links, duplicate canonical sources and dependency drift.

## Portability rule

Repository documentation must use repository-relative Markdown links for files stored in this repository. Machine-specific absolute paths may appear only as clearly labeled local CLI examples where the local installation path itself is the subject; they must not be used as documentation hyperlinks or package identity/dependency contracts.
