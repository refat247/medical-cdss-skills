# Repository Architecture and Extraction Policy

## Decision

`medical-cdss-skills` remains the canonical monorepo for the coupled medical-CDSS skill ecosystem. A skill is not moved to an independent repository merely because it has its own `SKILL.md`, tests, changelog, or version.

The default is **monorepo + independently versioned skill package**. Extraction is an explicit promotion step. An extracted package has exactly one writable canonical repository; the monorepo retains only a migration pointer where compatibility/discovery requires it.

## Why

The CDSS/RAG subsystem has real cross-skill orchestration and handover contracts. Keeping it together preserves atomic changes, integration testing, shared governance, and simple local installation. General-purpose skills can still be independently packaged and released from their top-level directories when independent lifecycle value exceeds distributed-repository overhead.

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
- `notion-bilingual-book-curator`
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

### C — Extracted standalone canonical repository

- `evidence-locked-clinical-pptx-builder`
  - Canonical repository: `https://github.com/refat247/evidence-locked-clinical-pptx-builder`
  - Frozen monorepo source commit: `39ff2fa03aede6b0c39988e900e63d3bc70b1342`
  - Frozen source subtree tree: `0cca38776383597314b6a8789014e7e76fa66cf6`
  - Verified standalone import commit: `f368c801bffd3e86ea705322143ce37766ebe301`
  - Imported release: `v2.4.0`
  - Integrity gate: byte-for-byte directory comparison plus SHA-256 verification of every `PACKAGE_MANIFEST.md` entry
  - Monorepo state after cutover: migration pointer only; no second runtime/release-evidence copy

This was the first package promoted under this extraction policy because it has an independent product identity, substantial runtime source/tests/templates, immutable release evidence, migration/versioning material, reference outputs, integrity ledgers, and an independent release lifecycle.

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
4. Preserve relevant Git history where practical and record exact source provenance.
5. Create the independent repository and import the verified package.
6. Re-run package integrity and test gates in the new repository.
7. Replace the old monorepo directory with a migration pointer or other deliberate compatibility mechanism; do not maintain two canonical copies.
8. Update catalogs/orchestrators only after the new repository passes verification.
9. Establish independent CI/release governance in the new repository.
10. Re-audit both repositories for broken links, duplicate canonical sources and dependency drift.

## Portability rule

Repository documentation must use repository-relative Markdown links for files stored in this repository. Machine-specific absolute paths may appear only as clearly labeled local CLI examples where the local installation path itself is the subject; they must not be used as documentation hyperlinks or package identity/dependency contracts.

## Canonical-source invariant

After extraction cutover:

- the standalone repository is the only writable canonical source;
- the monorepo must not retain executable source, tests, templates, or release evidence for that extracted package;
- historical monorepo commits remain valid provenance and are never rewritten merely to hide the old package;
- any compatibility directory in the monorepo must clearly identify itself as a pointer and link to the canonical repository.
