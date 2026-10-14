# Versioning decision

Package version: 1.0.0 on 2026-10-14.

This is the first release of a new skill, so the SemVer baseline is 1.0.0, not a bump from the presentation’s V1–V4 files.

Output versions 1, 2, 3, and 4 are renderer profiles. They stay on `--output-version`. They must not be written into `SKILL.md` metadata.version, `agents/openai.yaml`, the README version line, or the latest changelog heading.

Chosen class: initial release. Not a patch or minor of version-manager. version-manager 1.2.1 was only the rule used to place declarations.
