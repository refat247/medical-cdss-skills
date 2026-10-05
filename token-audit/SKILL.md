---
name: token-audit
version: 1.0.0
description: Audit the Antigravity/Codex workspace setup for token waste, context bloat, oversized rules/transcripts, tool schemas, and prompt caching efficiency. Read-only, changes nothing. Trigger when the user asks for a token audit, context analysis, token cost check, or optimization review. Token cost only; to map overlapping rules, skills or permissions use clean-my-ai-harness instead.
---

# Token & Context Audit Protocol

Audit this Antigravity / Codex setup for token waste, prompt caching efficiency, and context bloat. Do not fix anything. Report only.

Use your tools (`grep_search`, `find_by_name`, `list_dir`, `view_file`, `run_command`) to measure each item directly. Measure real numbers; do not guess. Change no file and no setting.

## 1. MEMORY & RULES (Instruction Bloat)
- Find every rule and instruction file in scope:
  - Project rules: `GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md`, `.agent/`
  - Global configs: `~/.gemini/config/`, `~/.codex/AGENTS.md`
- Report each file's size in bytes and estimated tokens (`bytes / 4`).
- Flag any single file over 20KB and any total combined rules over 40KB.
- List all installed skills in `~/.gemini/config/skills/` and `~/.gemini/antigravity/builtin/skills/` with their description lengths and total disk footprint.

## 2. TOOLS & MCP OVERHEAD
- Inspect active MCP servers and plugins:
  - Antigravity plugins in `~/.gemini/config/plugins/`
  - Active tool count and parameter schemas injected into the system prompt.
- Every registered tool adds its parameter JSON schema to every conversation turn. Report total tool count and estimated schema token footprint.
- Note any custom base URLs or third-party gateways that might bypass prompt caching.

## 3. MODEL & REASONING PROFILE
- Identify current active model (e.g., Gemini 2.5 Flash, Claude 3.5 Sonnet, GPT-5).
- Report reasoning effort / thinking budget if applicable.
- Flag frequent model switching within the same session, which invalidates the prompt cache key and re-bills the full conversation history.

## 4. OUTPUT & LOGGING DISCIPLINE
- Check tool output limits (e.g. `view_file` byte limits, command pagination).
- Check for rules that filter command output (build/test verbosity).
- Unfiltered test/build output in conversation history is re-sent in every subsequent turn.

## 5. SUBAGENTS & WORKSPACES
- List configured subagents and sidecars in `~/.gemini/antigravity/` and project configs.
- Check whether subagents inherit models or declare specific lightweight tiers (e.g. `flash_lite`, `flash`, `pro`).

## 6. BACKGROUND WORK & TASK SCHEDULING
- Check active background tasks and schedules via `schedule` / `manage_task`.
- On Windows, check scheduled tasks: `Get-ScheduledTask | Where-Object {$_.TaskName -match 'gemini|antigravity|codex|claude'}`.
- Compare trigger intervals against the 1-hour prompt cache lifetime window. Flag any recurring task >1hr that forces full cold-cache reprocessing.

## 7. TRANSCRIPT & SESSION USAGE
- Check active conversation logs under `<appDataDir>\brain\<conversation-id>\.system_generated\logs\transcript.jsonl`.
- Report:
  - Total conversation steps and turns
  - Cumulative tool calls made
  - Size of `transcript.jsonl` and `transcript_full.jsonl`
  - Longest single tool output in the session.

---

## Output Format

Output one clean table, sorted by token cost impact (highest first):

| FINDING | SEVERITY | EVIDENCE | WHAT IT IS COSTING ME |
|---|---|---|---|

- **Severity:** `RED` (Critical waste), `AMBER` (Moderate inefficiency), or `GREEN` (Optimal).
- **Evidence:** Exact numbers, byte counts, or file paths — never vague descriptions.

Then output one final concluding line:
**Highest-leverage recommendation:** The single highest-impact action the user should take.
