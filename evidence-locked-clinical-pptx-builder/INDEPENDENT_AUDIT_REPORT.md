# Independent Adversarial Audit — v2 Candidate

Questions tested before release:

- Can completeness be falsely claimed without section/table coverage evidence?
- Can a decision node be missed or over-compressed?
- Can cases duplicate or inflate cosmetically?
- Can provenance drift between source, case, slide and notes?
- Can a derivative mutate canonical clinical content?
- Can model knowledge leak into notes or local operational constraints become guideline evidence?
- Can an erratum be over-applied beyond its explicit scope?
- Can source terminology be silently harmonized?
- Can a contact sheet be mistaken for full visual certification?
- Can the deck look acceptable on a laptop but fail projector rules?
- Can an external visual reviewer introduce clinical content?

Initial candidate findings and repairs are documented in `docs/repair_report.md`.
