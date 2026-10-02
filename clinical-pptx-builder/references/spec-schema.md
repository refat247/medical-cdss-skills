# Minimal Slide Specification

```yaml
deck:
  title: ""
  audience: ""
  jurisdiction: "UNKNOWN"
  duration_minutes: null
  typography:
    title_min_pt: 32
    body_min_pt: 24
    citation_min_pt: 9
  requested_closing_slides:
    take_home: false
    q_and_a: false
    thank_you: false
  design_exclusions: []
  coverage_ledger:
    - item: ""
      status: "DONE|PARTIAL|UNRESOLVED|NOT IN SCOPE"
      evidence: ""
  status: "DRAFT"
slides:
  - id: "s01"
    type: "title|objectives|divider|content|algorithm|takeaway|references"
    title: ""
    key_message: ""
    evidence: []
    interpretation: []
    recommendation: []
    risks_or_exceptions: []
    citations: []
    visual: "none|diagram|chart|table|image"
    notes: ""
```

Use `UNKNOWN` rather than guessing jurisdiction, current label status, or evidence certainty.
Use the deck-level typography values as QA thresholds whenever the user provides stricter readability rules. If the slide cannot satisfy them, split or redesign the slide rather than shrinking main audience text.
