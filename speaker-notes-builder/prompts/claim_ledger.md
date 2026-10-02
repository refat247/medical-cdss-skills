# Clinical claim ledger prompt contract

Required for `clinical_cme` projects.

Create `claim_ledger.json` using `schemas/claim_ledger.schema.json` after the slide briefs and before final script certification.

Record every high-risk medical/regulatory claim that enters or may enter the spoken script, including dose, titration, indication, age cut-off, contraindication, boxed warning, pregnancy/lactation, paediatric use, comparative efficacy, MACE/mortality, procedure/anaesthesia advice, and local regulatory approval.

For each claim:
- preserve the exact proposition;
- classify its category and status;
- list the exact approved source reference(s) or source anchor(s);
- preserve jurisdiction and checked date when relevant;
- store the final safe spoken wording if the literal source wording needs qualification.

`UNVERIFIED` and `BLOCKED` high-risk claims may remain in the ledger for audit history, but must not enter the final spoken script without repair.
