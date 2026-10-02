# Versioning Decision — v2.2.1

Release: `evidence-locked-clinical-pptx-builder v2.2.1`

Immediate predecessor: `2.2.0`

Breaking change: `false`

Rationale: v2.2.1 hardens the implementation of the v2.2 semantic-integrity architecture without changing the public workflow purpose or rebuilding the skill. It repairs fail-open promotion logic, adds the missing source→inventory certification step required by the v2.2 intent, aligns schemas/templates with validators, tightens clinical repair authority, and removes release-cache artifacts. Existing v2.2 project artifacts can migrate forward without changing frozen clinical content.
