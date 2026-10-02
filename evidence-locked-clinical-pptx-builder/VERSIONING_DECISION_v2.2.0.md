# Versioning Decision — v2.2.0

Release: `evidence-locked-clinical-pptx-builder v2.2.0`

Reason: the dyslipidemia regression exposed externally observable workflow capabilities that v2.1.1 did not enforce: independent source-inventory completeness, semantic source-boundary QA, footnote binding, source-hierarchy attribution, prompt-leak/coherence QA, repair-fidelity control, normalization policy, semantic defect severity, and promotion blocking. These are backward-compatible additions, so a MINOR release is appropriate. They are not merely internal bug fixes; therefore v2.1.2 would understate the public capability change.
