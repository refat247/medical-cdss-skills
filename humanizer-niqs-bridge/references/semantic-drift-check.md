# Semantic Drift Check

Run after every Humanizer pass on governed Knowledge OS prose.

## Compare

Check the source and edited versions for changes to:
- facts;
- numbers;
- dates;
- names;
- quotations;
- citations;
- rankings;
- evidence/status labels;
- uncertainty;
- warnings;
- decisions;
- permissions or prohibitions;
- clinical or legal meaning;
- exact technical literals.

## Disposition

- `PASS`: style changed; supported meaning did not.
- `RESTORE`: one or more supported details were altered or dropped; restore them.
- `SKIP`: safe prose cleanup cannot be separated from protected evidence wording.

Do not mark `PASS` merely because the rewritten prose sounds better.
