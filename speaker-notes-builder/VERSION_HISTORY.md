# Version History

## v1.0.0 — 2026-09-07

**State:** ENGINEERING RELEASE PASS  
**Primary validated profile:** `clinical_cme`  
**Regression source:** Tirzepatide CME PDF (31 source pages; terminal duplicate explicitly excluded for 30 presenter pages)

### Release capabilities
- deck-first PPTX/PDF inspection and rendering;
- semantic-density-aware timing allocation;
- structured deck analysis, slide briefs, and clinical high-risk claim ledger;
- three-layer scripts: main, compressed, optional expansion;
- rehearsal and live presenter DOCX outputs;
- optional clean PowerPoint Notes injection;
- deterministic clinical/regulatory lint;
- render/reopen artifact verification;
- explicit PASS / PASS_WITH_WARNINGS / FAIL / UNCERTIFIED reporting.

### Known scope limits
- exact Work Mode manual ZIP-import behavior was not executable in the validation environment;
- exact original Tirzepatide PPTX injection was not run because the regression attachment available for this release was PDF;
- clinical correctness remains dependent on authoritative, current source material and human clinical review.
