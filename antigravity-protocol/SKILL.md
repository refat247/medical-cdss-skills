---
name: antigravity-protocol
version: 1.0.0
description: Use this skill when the user wants efficient, low-token execution of a software task (write code, fix bugs, plan features) or low token usage, or mentions "antigravity", "planning mode", "fast path", or complains about too many tokens or excessive thinking. Not a default for every coding request: it applies only when efficiency is asked for.
---

# Antigravity Protocol: High-Efficiency Coding

> [!IMPORTANT]
> **Mutual Exclusion**: This skill is **incompatible** with `ultimate-protocol`. If the user has activated ultimate mode (JSON-only output), do NOT follow this skill's formatting rules — defer entirely to `ultimate-protocol`. Both skills must never be active simultaneously.

Adopt a strict, structured approach to software development. Prioritize exact edits and planning over exploratory guessing and conversational filler.

## 1. Core Directives (Always Follow)

1. **Prefer targeted inspection over broad terminal sweeps**:
   - Use `find_by_name` (with patterns/extensions) and `grep_search` (with `Includes`, `MatchPerLine: true`) for targeted discovery instead of running recursive terminal sweeps.
   - Use `view_file` with precise `StartLine` and `EndLine` slices instead of viewing whole files.
2. **Chunk-based editing ONLY**:
   - Never rewrite entire files. Modify existing code using `replace_file_content` targeting single contiguous replacement chunks with minimal surrounding context.
   - Use `write_to_file` ONLY when creating brand-new files or Markdown artifacts.
3. **Stop guessing**:
   - If requirements or intentions are ambiguous, do NOT write exploratory test scripts to "figure it out". Stop and ask the user a specific clarifying question or use `ask_question`.
4. **No chat clutter (use artifacts)**:
   - Do not dump long code blocks, logs, or multi-page plans into the conversation text. Write structured documents as artifacts in `<appDataDir>\brain\<conversation-id>/` (`implementation_plan.md`, `walkthrough.md`) and provide clean clickable links (`[filename](file:///path)`).
5. **Acknowledge and act**:
   - No unnecessary preambles ("I understand you want me to...").
   - No redundant postambles ("In summary, I have modified..."). Make the necessary tool calls, then provide a concise, high-signal response.
6. **Minimize tool-call count**:
   - Batch independent reads/searches; never re-read a file already inspected in the same session unless it has changed.

---

## 2. Process Intent (Classify Every Request into a Mode)

### Mode A — Investigatory (Information & Research Requests)
- **Trigger:** "How does X work?", "Where is Y defined?", "Find where Z happens.", architecture questions.
- **Action:**
  1. Search silently using `grep_search` and `find_by_name`.
  2. Inspect definitions with targeted `view_file` line slices.
  3. Output ONLY the direct answer accompanied by clickable file links (`[filename:L10-25](file:///path/to/file#L10-L25)`). No plan required.

### Mode B — Fast Path (Small Targeted Changes)
- **Trigger:** "Fix this typo", "Change this parameter", "Rename this variable", one-off bug fixes.
- **Action:**
  1. Read only the relevant line range of the target file using `view_file`.
  2. Execute a single, exact `replace_file_content` edit.
  3. Close with a concise confirmation. No plan required.

### Mode C — Strict Planning (Complex & Multi-File Tasks)
- **Trigger:** "Add a new feature", "Implement auth", "Refactor module X", any architectural change.
- **Action flow:**
  1. **Silent Research:** Trace dependencies and inspect interfaces using read-only tools (`grep_search`, `find_by_name`, `view_file`). Do NOT modify source code.
  2. **Implementation Plan Artifact:** Create or update `implementation_plan.md` in `<appDataDir>\brain\<conversation-id>/` with exact files (`[NEW]`, `[MODIFY]`, `[DELETE]`), user review items, and automated verification commands. Set `RequestFeedback: true` in `ArtifactMetadata`.
  3. **Halt for Approval:** STOP and wait for explicit user approval before executing any file modifications.
  4. **Execute Checklist:** Once approved, make code modifications strictly adhering to the plan using `replace_file_content` and `write_to_file`.
  5. **Verification:** Run the automated build/test/lint commands (e.g. `pytest`, `npm test`, `cargo check`) via `run_command` and report results.
  6. **Walkthrough:** Create or update `walkthrough.md` summarizing changes and validation outcomes.

---

## 3. Tool Hierarchy (Strict Priority Order)

1. **Discovery & Inspection (Lowest Token Cost):**
   - `grep_search` (exact pattern / regex across files)
   - `find_by_name` (file and directory search)
   - `list_dir` (directory listing)
   - `view_file` (targeted line slices with `StartLine`/`EndLine`)
2. **Precision Code Editing:**
   - `replace_file_content` (targeted search-and-replace chunk edits)
3. **File Creation:**
   - `write_to_file` (brand-new source files, scratch scripts, and markdown artifacts)
4. **Terminal Execution:**
   - `run_command` (PowerShell on Windows: builds, tests, linting, package management). Never use terminal commands to read files or perform edits.

---

## 4. Output Discipline

- Default response shape: direct answer / actionable result → clickable file paths → concise next step.
- Never repeat user instructions back. Never narrate obvious intermediate actions.
- Maintain code comments and documentation integrity; preserve existing comments unless explicitly instructed otherwise.
