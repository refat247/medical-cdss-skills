# Unembedded Large Artifacts — v2.4.0

Audit date: 2026-10-03

The following two aggregate ZIP files were reconstructed from the preserved Library fallback and verified byte-for-byte by SHA-256, but could not be uploaded through the currently available GitHub connector because it supports Git blob creation from inline content only and exposes no create-release/upload-release-asset or local-file upload action.

| Intended path | Size | SHA-256 | State |
|---|---:|---|---|
| `delivery/ALL_DELIVERABLES.zip` | 12,238,082 bytes | `97c95cf7f9389a39a43b031b251347ac62581cb2de9cde34349658c40a6b4da9` | reconstructed + verified; not embedded |
| `test-evidence/test-run-evidence.zip` | 10,281,210 bytes | `0d63d5b5bda046e76d5e8780d27efccfcf592cf1621f8870b12c74d32d8a3ace` | reconstructed + verified; not embedded |

The test-evidence ZIP contains six PNG contact sheets plus the JSON/CSV evidence files. The JSON/CSV evidence files are embedded separately in this archive. The source package, delta ZIP, patch, polished reference deck, commit handoff, changed-file ledger, and hash ledger are also embedded separately.

This file is intentionally explicit so the repository never claims archival completeness that the GitHub connector did not actually achieve.
