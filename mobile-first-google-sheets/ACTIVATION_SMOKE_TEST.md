# Runtime Activation Smoke Test

Run in a fresh chat after installation.

```text
@mobile-first-google-sheets fresh runtime activation test.

Read-only only. Do not modify anything.

Do NOT inspect:
- filesystem skill directories
- SKILL.md
- agents/openai.yaml
- README
- CHANGELOG
- ZIP files
- Git
- Notion
- previous chats
- installed-package discovery

Use ONLY instructions already injected into this fresh conversation by the selected Skill/runtime.

If loaded, report:
- internal skill name
- loaded version
- exact loaded title/header
- first operational heading after the title
- the exact workflow-order mnemonic

Expected:
- internal name: mobile-first-google-sheets
- version: 1.2.1
- title/header: Mobile-First Google Sheets
- first operational heading: 1. Operating Contract
- workflow-order mnemonic: ACT → ORIENT → CHECK → NAVIGATE → ANALYZE → ADMINISTER

Final verdict exactly one of:
PASS — mobile-first-google-sheets v1.2.1 activated
FAIL — mobile-first-google-sheets runtime did not activate as declared
```

Installation/discoverability is not activation.