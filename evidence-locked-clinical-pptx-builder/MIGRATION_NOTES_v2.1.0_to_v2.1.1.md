# Migration Notes — v2.1.0 -> v2.1.1

This patch does not alter clinical artifacts.

For project-state files, replace:

```yaml
independent_visual_qa: preferred
independent_visual_qa_waivable: true
```

with:

```yaml
independent_visual_qa_policy: required_unless_explicit_user_waiver
```

Independent-review certification now requires normalized JSON. Existing Markdown review reports remain valid narrative records but are `NON_CERTIFYING_REPORT`.
