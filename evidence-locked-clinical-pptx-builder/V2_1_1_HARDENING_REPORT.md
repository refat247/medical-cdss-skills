# v2.1.1 Hardening Report

Baseline: `evidence-locked-clinical-pptx-builder v2.1.0`

Verified baseline ZIP SHA-256 supplied by the user/audit: `75e7b5c6ce723399548ecd24dd6367a7c5d9205ff6cce647d88338a6ce48666b`.

This release is intentionally limited to package-integrity and independent-QA policy enforcement. It does not restart MI workflow reconstruction and does not modify frozen MI clinical artifacts.

## Fixed
- manifest self-hash defect;
- wrong immediate predecessor / breaking-change metadata;
- ambiguous independent-QA template defaults;
- permissive independent-review certification;
- insufficient repair/post-repair evidence validation;
- ambiguous canonical promotion terminology.

## Not changed
- evidence/case corpus architecture;
- derivative workflow architecture;
- clinical source boundaries;
- frozen MI cases, recommendations, thresholds, doses, Class/LoE, terminology or provenance.
