# Work Mode quick start

This ZIP is designed so `SKILL.md` is at the package root.

## Manual use

1. Upload `speaker-notes-builder-v1.0.0.zip` to a Work Mode task/session together with the presentation you want to process.
2. Tell Work Mode to **extract the ZIP and follow `SKILL.md` as the governing workflow**.
3. State the audience, total talk time, Q&A reserve, and whether external research is allowed.
4. For medical/CME decks, explicitly request `profile=clinical_cme` unless Work Mode has already inferred the medical profile from the deck.
5. Ask for the complete cycle through artifact build and verification, not only script drafting.

Suggested instruction:

```text
Use the attached speaker-notes-builder skill package. Extract it and follow SKILL.md.
Process the attached presentation with profile=clinical_cme and source_mode=strict.
Audience: physicians.
Total session: 15 minutes, reserve 2 minutes for Q&A.
Create both rehearsal.docx and live-presenter.docx. If the source is PPTX, also create a new PPTX with only the final main script in the Notes pane. Never overwrite the source.
Run the validation, clinical lint, render/reopen verification, and final QA gates. Report exact PASS / PASS_WITH_WARNINGS / FAIL / UNCERTIFIED state and unresolved items.
```

## Important

The package has been engineering-tested in this environment, but the exact manual ZIP-import behavior of every Work Mode client/UI is not part of the package's verified scope. If your client does not expose a dedicated skill-import control, attach the ZIP as a file and instruct Work Mode to extract/read `SKILL.md`.
