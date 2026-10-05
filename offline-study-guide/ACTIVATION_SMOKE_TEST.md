# Activation smoke test — offline-study-guide v1.2.1

## Native runtime read-only test

After selecting `@offline-study-guide`, use this prompt without reading package files manually:

> NATIVE ACTIVATION TEST — READ ONLY. Use only instructions already injected by the selected skill. Do not inspect files, ZIPs, Git, Notion, or prior chats. If the skill instructions are injected, report: exact skill name, exact version, lifecycle/status, exact title/header, the first operational paragraph after the title, and whether the workflow distinguishes FILE READ SUCCESS from PARSE SUCCESS. If the instructions are not injected, reply exactly `OFFLINE_STUDY_GUIDE_NOT_INJECTED`.

Expected release identity when native injection is actually present:

- skill: `offline-study-guide`
- version: `1.2.1`
- status: `stable`

## Package smoke test

From the extracted package root:

```bash
python3 scripts/verify_release.py
python3 scripts/run_regression.py
```

For the final ZIP:

```bash
python3 scripts/verify_release.py --archive /path/to/offline-study-guide-skill-v1.2.1.zip
```

Package smoke-test success does not establish native runtime activation.
