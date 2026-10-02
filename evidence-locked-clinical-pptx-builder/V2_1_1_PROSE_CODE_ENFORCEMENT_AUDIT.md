# v2.1.1 Prose-vs-Code Enforcement Audit

| Requirement | SKILL/README/template | Code enforcement | Test coverage | Result |
|---|---|---|---|---|
| High-stakes default policy | `required_unless_explicit_user_waiver` | project validator accepts only enum | metadata/policy tests | PASS |
| Explicit waiver is not certification | documented | gate returns `INDEPENDENT_QA_WAIVED`, `NOT_CERTIFIED` | waiver test | PASS |
| Missing report/no waiver fails closed | documented | `INDEPENDENT-QA-UNCERTIFIED` | fail-closed test | PASS |
| JSON only certifies | documented | text/Markdown -> `NON_CERTIFYING_REPORT` | free-text + marker-only tests | PASS |
| One unique row per slide | documented | duplicate/missing/out-of-range rejected | three row-integrity tests | PASS |
| Findings require adjudication | documented | ACCEPT/REJECT/CLINICAL required | warning-without-adjudication test | PASS |
| Clinical adjudication blocks visual certification | documented | gate blocks | clinical-adjudication test | PASS |
| Accepted repair cannot certify original | documented | final hashes/mapping/rerender/post-review required | repair evidence tests | PASS |
| Full post-repair review | documented | 100% row coverage + passlike final status | complete/missing post-review tests | PASS |
| Manifest excludes itself | documented in generated manifest | writer auto-excludes output path | manifest self-reference test | PASS |
| Manifest-listed hashes verify | release requirement | verifier recomputes every listed byte/hash | verifier/tamper tests | PASS |
| Promotion distinguishes certified/waived/uncertified | promotion template + SKILL | gate emits distinct status/certification | policy tests | PASS |

Verdict: **PASS — v2.1.1 prose, templates and deterministic enforcement are aligned for the patched domains.**
