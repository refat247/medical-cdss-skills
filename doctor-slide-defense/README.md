# Doctor slide defense

**Version:** 1.0.0

Build a doctor-panel defense from one claim ledger. Switch the reading shape without rewriting the sources.

Output versions are not the package version:

- `--output-version 1` citation map
- `--output-version 2` one-argument prose
- `--output-version 3` rehearsal
- `--output-version 4` labeled claims (default for a panel)

```bash
python scripts/render_defense.py fixtures/angina_trimetazidine_ledger.json --output-version 4 --out defense-v4.md
```

HTML, only after that markdown exists:

```bash
set DOCTOR_SLIDE_DEFENSE_HTML_BUILDER=path\to\offline-study-guide\scripts\build_guide.py
python scripts/render_defense.py fixtures/angina_trimetazidine_ledger.json --output-version 3 --out defense-v3.md --html defense-v3.html
```

This package does not search the textbooks. The agent fills the ledger from chunk and PDF retrieval, then the script renders. A render is not clinical validation.
