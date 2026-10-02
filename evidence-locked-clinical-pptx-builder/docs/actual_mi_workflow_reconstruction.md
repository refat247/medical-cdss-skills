# Reconstructed MI Workflow — Reference Implementation

This reconstruction is read-only and is based on `MI_Case_Based_Presentation_Project_Handoff_v3.16_FINAL.md` plus the frozen extraction, reconciliation, case-library, architecture, storyboard, build and independent-audit artifacts.

## What actually happened

### Evidence control
- Two-source-only clinical boundary: 2026 Fifth UDMI + 2023 ESC ACS.
- Explicit source roles: 2026 definitions/classification/diagnostic framing; 2023 ACS management/investigation.
- No invention of vignette values or clinical detail.
- 2023 vs 2026 terminology preserved explicitly rather than silently harmonized.
- Local/operational constraints were treated as context, not guideline evidence.

### Source extraction and independent audit
- 2026 UDMI provisional extraction: 161 nodes -> dedicated audit/repair/split/add/merge -> 168 FINAL nodes.
- 2023 ESC provisional extraction: 339 nodes, including 193 recommendation-table rows -> dedicated audit/repair -> 340 FINAL nodes.
- The ESC audit rechecked 17/17 recommendation tables and 193/193 formal rows, corrected PDF artefacts, split an over-compressed pregnancy node, added missed nodes and removed duplicates/placeholders.
- Frozen inventories were hash-protected before reconciliation.

### Reconciliation
- 508 total frozen decision nodes were audited.
- 56 explicit cross-source relationship records and 10 conflict/terminology items were created.
- Source-specific language and the management-vs-final-classification distinction were preserved.

### Case corpus
- 508 source nodes -> 493 provisional candidates; 15 nodes intentionally remained explanatory-only.
- Candidate audit/deduplication -> 481 FINAL distinct cases.
- Coverage re-audit accounted for 168/168 UDMI nodes, 340/340 ESC nodes, 56/56 reconciliation records and 10/10 conflict items.
- Master Case Library, audit report and coverage matrix were frozen.

### Pedagogy / architecture
- 481 cases were re-audited pedagogically: 152 Core GP, 205 Important, 114 Advanced/Consultant, 10 Backup/Optional.
- 16 teaching modules were created.
- A 78-case Core Live anchor path emerged from review rather than a preset target.
- 481/481 cases were routed; 78 anchors became 39 storyboard units using individual, paired, cluster and terminology-checkpoint patterns.
- 137-slide Master/Core specification followed; 10 reusable case-first slide patterns and 41 master / 31 live-route visual requirements were specified.

### Product builds
- 70-slide Live CME built, rendered, audited, independently promoted.
- 137-slide Master Core built, rendered, audited, independently promoted.
- 60-, 45-, and 30-minute derivatives were derived from canonical parents rather than re-researched.
- Advanced/Consultant and Reference/Backup products were separately specified, built, audited and promoted.
- Modular Slide Bank became an index/integration layer rather than a duplicate 475-slide superdeck.

### Repair lessons
- Advanced independent audit found 119 source-label runs below the >=16 pt citation target; repair increased source labels to 16 pt without changing clinical content.
- Reference independent audit found title edge/margin/readability risk; repair adjusted title margins/wording without altering clinical meaning.
- Dense master/reference products kept full provenance in notes while on-screen text was compressed.

### Closure
- Eight presentation products were structurally verified with complete speaker-note coverage.
- Modular index was independently rerendered 35/35 and promoted.
- Canonical clinical slides indexed: 475; case-occurrence rows: 1002; unique case IDs appearing in canonical products: 195.
- Manifest/hash verification passed and the project was closed; future work was maintenance, not a new numbered continuation phase.

## Workflow lesson

The successful pattern was not “write PPTX -> fix formatting.” It was evidence control -> exhaustive corpus -> audited/frozen clinical model -> teaching architecture -> specification -> build -> clinical QA -> render/visual QA -> repair -> independent promotion -> derivatives/index/closure.

## Why an independent second visual review became useful

The MI project demonstrated a concrete separation between build-time audit and independent promotion audit. The Phase-25 Advanced build audit reported no blocking layout problem, yet the Phase-26 independent pass detected 119 source-label runs below the frozen citation floor. Likewise, the Reference build passed its initial audit, but the independent promotion audit detected title-edge/margin readability risk after rendering. These were not clinical errors; they were presentation-engineering defects that survived the first pass. The lesson is to use an independent visual/runtime review as a second set of eyes for high-stakes final decks, while preventing that reviewer from changing clinical evidence.
