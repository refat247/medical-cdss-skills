# Artifact and Writing Routing

## Purpose

Use this reference when the correct Notion destination is unclear because the item has a recognizable document form such as an audit, SOP, prompt, guide, handoff, manuscript, research report, decision memo, learning note, source artifact, benchmark, or execution report.

This reference refines placement. It does **not** replace NIQS Page Role, domain ownership, canonicality rules, or duplicate control.

## Routing algorithm

Apply this sequence:

**DOMAIN / OWNERSHIP → NIQS PAGE ROLE → ARTIFACT FORM → CANONICAL HOME**

### 1. Domain / ownership
Ask what the content is actually about and which project, programme, or life/work area is responsible for keeping it current.

### 2. NIQS Page Role
Assign the narrowest useful primary NIQS role:

`HUB` / `CURRENT STATE` / `RESEARCH` / `EVIDENCE ARCHIVE` / `SOURCE CARD` / `DECISION` / `EXECUTION` / `BENCHMARK` / `LEARNING` / `REFERENCE` / `ARCHIVE`

Page Role answers **what job the page performs**. It remains authoritative over Artifact Form.

### 3. Artifact Form
Use Artifact Form only when it adds practical routing clarity. Examples include:
- raw capture / inbox item
- research report / synthesis
- raw AI research output
- source evidence / source card
- decision memo
- audit report
- SOP / procedure / how-to
- guide
- prompt
- handoff
- learning / study note
- execution / test report
- benchmark report
- manuscript / book
- stable reference note
- historical / superseded artifact

Do not create a new Notion taxonomy merely to enumerate every possible document genre.

### 4. Canonical Home
Search and fetch the existing canonical parent, project, domain hub, database, or router before creating anything new.

Routing precedence:

**existing canonical parent → domain ownership → NIQS Page Role → artifact form**

If an existing canonical parent already governs the object, keep the artifact there unless a documented architectural rule requires otherwise.

## Existing-router-first rule
Before creating a new routing page, index, database, or top-level control surface:
1. Search for the current canonical routing/control surface.
2. Fetch it.
3. Test whether the missing route can be expressed as a compact section, matrix, linked view, or child reference.
4. Extend the current router when this remains readable and maintainable.
5. Split into a child routing page only when the existing router would become materially overloaded or mix incompatible scopes.
6. Create a peer/top-level router only when neither the current router nor a child reference can serve the need without structural harm.
7. Record uncertainty as `UNRESOLVED` instead of creating a speculative competing surface.

## Default routing matrix

| Artifact Form | Default Page Role | Default routing rule |
|---|---|---|
| Raw capture / brain dump | unclassified until review | Universal Inbox/staging → classify later |
| Research report / synthesis | RESEARCH | Relevant project/domain research hub |
| Raw AI research output | EVIDENCE ARCHIVE | Under the corresponding research/synthesis parent |
| Source evidence | SOURCE CARD | Under the relevant evidence archive |
| Decision memo | DECISION | Relevant project/domain decision surface |
| Execution / test report | EXECUTION | Relevant active project / implementation-validation branch |
| Benchmark report | BENCHMARK | Relevant project benchmark/evaluation branch |
| Audit report | RESEARCH or REFERENCE depending purpose | Nearest governed parent/object being audited; not a universal Audit folder |
| SOP / procedure / how-to | REFERENCE | Domain-specific stays in domain; truly cross-domain reusable method goes to reusable reference/methodology |
| Guide | REFERENCE or LEARNING | Subject guide stays in subject domain; writing-method guide stays in writing methodology |
| Prompt | supporting artifact | Project-specific stays with project; reusable AI prompt goes to AI prompt/system library |
| Handoff | EXECUTION / control support | Inside the project/workstream being handed off |
| Learning / study note | LEARNING | Relevant study/domain area |
| Manuscript / book | project-like artifact | Writing/manuscript programme when manuscript production itself is the active project; otherwise preserve owning subject/project context |
| Stable reusable reference | REFERENCE | Reusable reference layer unless domain-specific ownership is stronger |
| Historical / superseded | ARCHIVE | Archive within owning domain; raw imports remain in designated raw-import archive until promoted |

## KOS-specific guardrails
- `00A — Knowledge OS Routing Map & Move Log` is the primary structural routing/control surface. Extend it before proposing a peer routing index.
- `03 AI Systems & Prompt Library` owns reusable AI prompts/systems and AI-domain research, but project-specific prompts stay with their projects.
- `07 Reference Library` is for reusable cross-domain references, governance, methods, and standards; it is not a dumping ground for every SOP or guide.
- `09. GUIDE WRITING` owns writing methodology and genuine manuscript/publication projects. Finished domain-specific guides remain in their subject domain.
- `99 Google Keep Archive` remains a raw legacy-import archive, not the default destination for newly superseded governed content.
- An audit, SOP, handoff, prompt, or guide should normally stay near the thing it governs.
- **Being prose or “writing” is never sufficient reason by itself to route a page into a writing area.**

## Verification
Before final placement, answer:
1. What domain owns this?
2. What is its primary NIQS Page Role?
3. Does Artifact Form add any routing information?
4. Is there already a canonical parent?
5. Am I creating a new router only because of the artifact's name?
6. Will this placement preserve provenance, discoverability, and maintenance responsibility?
7. After placement, did I re-fetch and verify the route?

If questions 1–4 are unresolved, do not guess. Record the route as `UNRESOLVED` and preserve the artifact until the ambiguity is resolved.
