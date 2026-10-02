# Deck analysis prompt contract

Analyze the entire rendered deck before drafting any per-slide script.

Return only structured content compatible with `schemas/deck_analysis.schema.json`.

Determine:
- presentation purpose and intended audience;
- source mode and evidence boundary;
- narrative arc and section structure;
- which slides are title/divider/evidence/mechanism/safety/dosing/counselling/case/takeaway/reference;
- duplicated or redundant pages;
- high-risk claims and jurisdiction-sensitive claims;
- missing evidence, conflicting evidence, or claims the deck itself says are not verified.

Do not repair source gaps silently. Put them in `known_gaps` or `known_conflicts`.
