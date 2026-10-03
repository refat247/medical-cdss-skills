# Release Evidence Policy

Preserve reproducibility and audit evidence separately from canonical runtime source.

1. Runtime instructions/code/tests/templates stay in canonical source.
2. Versioned release evidence may preserve original packages, patches, changed-file ledgers, test evidence, reference outputs, delivery bundles, provenance and hashes.
3. Never route runtime execution through `release-evidence/`.
4. Never overwrite a released version directory.
5. Record SHA-256 for preserved artifacts.
6. Preserve certification/uncertainty state exactly; archival presence is not certification.
7. Reassess storage strategy before future very-large binaries; migrate to GitHub Releases or Git LFS when supported.
