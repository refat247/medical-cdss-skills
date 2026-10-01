#!/usr/bin/env python3
"""Render a normalized visible-harness map as accessible HTML and Markdown."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


RUN_STAGES = (
    "Available",
    "Eligible",
    "Shown",
    "Consulted",
    "Acted through",
    "Checked",
    "Accepted",
)
SETUP_STATIONS = (
    ("already-there", "Already there", "Standing instructions and remembered context visible before this job begins."),
    ("chooses-help", "How it chooses help", "Skills and routes that may make specialist help eligible."),
    ("joins-job", "What joins this job", "Prompts, references, and task context that may join a particular run."),
    ("can-do", "What it can do", "Tools, settings, permissions, and action boundaries."),
    ("proves-done", "What proves it is done", "Checks, validators, and evidence that can test the finish line."),
)
DECISION_LABELS = {
    "KEEP": "Keep it",
    "ONE_HOME": "Give it one home",
    "LOAD_LATER": "Load it later",
    "MAKE_A_CHECK": "Turn it into a check",
    "PROBATION": "Put it on probation",
    "RETIRE": "Retire it safely",
}


class RenderError(ValueError):
    """Raised for malformed or unsafe renderer inputs."""


def as_text(value: object, fallback: str = "UNKNOWN") -> str:
    if value is None:
        return fallback
    if isinstance(value, (str, int, float, bool)):
        rendered = str(value).strip()
        return rendered or fallback
    return fallback


def html_text(value: object, fallback: str = "UNKNOWN") -> str:
    return html.escape(as_text(value, fallback), quote=True)


def markdown_text(value: object, fallback: str = "UNKNOWN") -> str:
    # Numeric entities keep audited filenames and labels visible without letting
    # them become Markdown links, images, headings, emphasis, or code fences.
    entities = {
        "\\": "&#92;",
        "`": "&#96;",
        "*": "&#42;",
        "_": "&#95;",
        "[": "&#91;",
        "]": "&#93;",
        "(": "&#40;",
        ")": "&#41;",
        "#": "&#35;",
        "+": "&#43;",
        "-": "&#45;",
        "!": "&#33;",
        "|": "&#124;",
        ">": "&#62;",
        ":": "&#58;",
    }
    rendered: list[str] = []
    for character in as_text(value, fallback).replace("\r", " "):
        if character == "\n":
            rendered.append("<br>")
        elif character in entities:
            rendered.append(entities[character])
        else:
            rendered.append(html.escape(character, quote=False))
    return "".join(rendered)


def load_map(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RenderError(f"Map file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RenderError(f"Map file is not valid JSON: {exc}") from exc
    except OSError as exc:
        raise RenderError(f"Map file could not be read ({exc.__class__.__name__})") from exc
    if not isinstance(payload, dict):
        raise RenderError("Map JSON must contain an object at the top level")
    setup = payload.get("setup_map")
    if not isinstance(setup, dict) or not isinstance(setup.get("controls"), list):
        raise RenderError("Map JSON must contain setup_map.controls as a list")
    for key in ("coverage", "blind_spots", "decisions"):
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise RenderError(f"Map JSON field {key} must be a list when present")
    return payload


def normalize_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    reported = payload.get("reported_runtime")
    if not isinstance(reported, dict):
        reported = {}

    def field(name: str) -> tuple[str, str]:
        value = reported.get(name)
        if isinstance(value, dict):
            return as_text(value.get("value")), as_text(value.get("evidence_state"), "UNKNOWN")
        return as_text(value), "UNKNOWN"

    surface, surface_evidence = field("surface")
    model, model_evidence = field("model")
    return {
        "surface": surface,
        "surface_evidence": surface_evidence,
        "model": model,
        "model_evidence": model_evidence,
    }


def normalize_run_map(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("run_trace")
    if not isinstance(source, dict):
        source = payload.get("run_map")
    if not isinstance(source, dict):
        source = {}

    trace_status = as_text(source.get("trace_status", source.get("status")), "NOT_EXPOSED")
    trace_note = as_text(
        source.get("trace_note", source.get("note")),
        "No run trace was supplied. Actual loading and use are not exposed.",
    )
    supplied_funnel = source.get("funnel")
    supplied_by_stage: dict[str, dict[str, Any]] = {}
    if isinstance(supplied_funnel, list):
        for item in supplied_funnel:
            if isinstance(item, dict):
                stage = as_text(item.get("stage"), "")
                if stage:
                    supplied_by_stage[stage.casefold()] = item
    elif isinstance(supplied_funnel, dict):
        for stage, item in supplied_funnel.items():
            if isinstance(item, dict):
                supplied_by_stage[as_text(stage).casefold()] = {"stage": stage, **item}

    stages = []
    for stage in RUN_STAGES:
        item = supplied_by_stage.get(stage.casefold())
        if item is None:
            stages.append({
                "stage": stage,
                "status": "UNKNOWN" if trace_status not in {"NOT_EXPOSED", "NOT EXPOSED"} else "NOT_EXPOSED",
                "count": None,
                "detail": "No trace evidence was supplied for this stage.",
            })
            continue
        raw_count = item.get("count")
        count = raw_count if isinstance(raw_count, int) and raw_count >= 0 else None
        stages.append({
            "stage": stage,
            "status": as_text(item.get("status"), "UNKNOWN"),
            "count": count,
            "detail": as_text(item.get("detail"), "No detail supplied."),
        })
    return {"trace_status": trace_status, "trace_note": trace_note, "funnel": stages}


def evidence_states(control: dict[str, Any]) -> str:
    evidence = control.get("evidence")
    if not isinstance(evidence, list):
        return "UNKNOWN"
    states = []
    for item in evidence:
        if isinstance(item, dict):
            state = as_text(item.get("state"), "")
            if state and state not in states:
                states.append(state)
    return ", ".join(states) or "UNKNOWN"


def control_field(control: dict[str, Any], name: str, fallback: str = "UNKNOWN") -> str:
    value = control.get(name)
    if isinstance(value, dict):
        return as_text(value.get("value"), fallback)
    return as_text(value, fallback)


def control_decision(control: dict[str, Any]) -> tuple[str, str]:
    decision = control.get("decision")
    if not isinstance(decision, dict):
        return "UNDECIDED", "No decision supplied."
    return (
        as_text(decision.get("status", decision.get("decision")), "UNDECIDED"),
        as_text(decision.get("reason"), "No reason supplied."),
    )


def decision_display(code: object) -> str:
    normalized = as_text(code, "UNDECIDED")
    if normalized == "UNDECIDED":
        return "Not decided"
    return f"{DECISION_LABELS.get(normalized, normalized)} ({normalized})"


def collect_decisions(payload: dict[str, Any]) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []
    decisions = payload.get("decisions", [])
    if isinstance(decisions, list):
        for item in decisions:
            if not isinstance(item, dict):
                continue
            decision = as_text(item.get("decision", item.get("status")), "UNDECIDED")
            if decision not in DECISION_LABELS:
                raise RenderError(f"Unsupported cleanup decision: {decision}")
            collected.append({
                "control": as_text(item.get("control", item.get("control_id"))),
                "decision": decision,
                "reason": as_text(item.get("reason"), "No reason supplied."),
                "evidence_state": as_text(item.get("evidence_state"), "UNKNOWN"),
            })
    if collected:
        return collected

    controls = payload.get("setup_map", {}).get("controls", [])
    for control in controls:
        if not isinstance(control, dict):
            continue
        status, reason = control_decision(control)
        if status != "UNDECIDED":
            collected.append({
                "control": as_text(control.get("path", control.get("id"))),
                "decision": status,
                "reason": reason,
                "evidence_state": evidence_states(control),
            })
    return collected


def station_for_control(control: dict[str, Any]) -> str:
    kind = as_text(control.get("kind"), "instruction-or-reference").casefold()
    path = as_text(control.get("path"), "").casefold()
    tokens = set(path.replace("\\", "/").replace("-", "_").replace(".", "_").split("_"))
    if kind == "deterministic-control" or any(
        marker in path for marker in ("validator", "guardrail", "hook", "receipt", "test", "check")
    ):
        return "proves-done"
    if kind in {"authority-config", "tool-or-action-config"} or any(
        marker in path for marker in ("permission", "approval", "tool", "mcp", "sandbox", "authority")
    ):
        return "can-do"
    if kind == "skill-or-reference":
        if path.endswith("skill.md") or "catalog" in path or "router" in path or "trigger" in path:
            return "chooses-help"
        return "joins-job"
    if kind == "configuration":
        return "chooses-help"
    if kind in {"prompt", "instruction-or-reference"}:
        return "joins-job"
    if kind in {"project-instructions", "memory-or-standing-context"} or tokens & {"agents", "claude", "memory"}:
        return "already-there"
    return "already-there"


def group_setup_stations(controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = {
        station_id: {"id": station_id, "title": title, "description": description, "controls": []}
        for station_id, title, description in SETUP_STATIONS
    }
    for control in controls:
        groups[station_for_control(control)]["controls"].append(control)
    return [groups[station_id] for station_id, _, _ in SETUP_STATIONS]


def blind_spot_detail(item: dict[str, Any]) -> str:
    detail = as_text(item.get("detail"), "No detail supplied.")
    counts = item.get("counts")
    if isinstance(counts, dict) and counts:
        rendered = ", ".join(f"{as_text(key)}: {as_text(value)}" for key, value in sorted(counts.items()))
        detail = f"{detail} Counts: {rendered}."
    return detail


def render_markdown(payload: dict[str, Any]) -> str:
    runtime = normalize_runtime(payload)
    setup = payload["setup_map"]
    controls = [item for item in setup.get("controls", []) if isinstance(item, dict)]
    summary = setup.get("summary") if isinstance(setup.get("summary"), dict) else {}
    run_map = normalize_run_map(payload)
    blind_spots = [item for item in payload.get("blind_spots", []) if isinstance(item, dict)]
    coverage = [item for item in payload.get("coverage", []) if isinstance(item, dict)]
    decisions = collect_decisions(payload)
    stations = group_setup_stations(controls)

    lines = [
        "# What shapes your AI before you type",
        "",
        "*Your AI Setup Map*",
        "",
        "> This report separates the **setup map** (controls the scanner could see) from the **run map** (controls proven to have shaped one job). Static presence is not proof of runtime use.",
        "",
        "## Reported runtime",
        "",
        "| Field | Value | Evidence |",
        "|---|---|---|",
        f"| Surface | {markdown_text(runtime['surface'])} | {markdown_text(runtime['surface_evidence'])} |",
        f"| Model or router | {markdown_text(runtime['model'])} | {markdown_text(runtime['model_evidence'])} |",
        "",
        "## Blind spots",
        "",
    ]
    if blind_spots:
        lines.extend(["| Area | Evidence | What remains unknown |", "|---|---|---|"])
        for item in blind_spots:
            lines.append(
                f"| {markdown_text(item.get('id'))} | {markdown_text(item.get('evidence_state'))} | "
                f"{markdown_text(blind_spot_detail(item))} |"
            )
    else:
        lines.append("No blind spots were declared. That absence is not proof of complete coverage.")

    lines.extend([
        "",
        "## Setup map: what is visible or declared",
        "",
        f"Visible controls: **{markdown_text(summary.get('visible_controls'), str(len(controls)))}**  ",
        f"Inspected bytes: **{markdown_text(summary.get('inspected_bytes'), 'UNKNOWN')}**  ",
        f"Controls without a cleanup decision: **{markdown_text(summary.get('undecided_controls'), 'UNKNOWN')}**",
        "",
    ])
    lines.extend(["### Five stations in the setup", ""])
    for index, station in enumerate(stations, start=1):
        station_controls = station["controls"]
        lines.append(f"{index}. **{markdown_text(station['title'])} — {len(station_controls)} visible**  ")
        lines.append(f"   {markdown_text(station['description'])}  ")
        if station_controls:
            samples = ", ".join(f"`{markdown_text(item.get('path'))}`" for item in station_controls[:3])
            lines.append(f"   Examples: {samples}")
        else:
            lines.append("   No control was visible here. Hidden or unexported controls may still exist.")
    lines.extend([
        "",
        "### Visible-control drill-down",
        "",
        "| Target-relative control | Job | Owner | Load timing | Control type | Evidence | Decision |",
        "|---|---|---|---|---|---|---|",
    ])
    if controls:
        for control in controls:
            runtime_info = control.get("runtime") if isinstance(control.get("runtime"), dict) else {}
            decision, _ = control_decision(control)
            lines.append(
                f"| {markdown_text(control.get('path'))} | {markdown_text(control_field(control, 'job'))} | "
                f"{markdown_text(control_field(control, 'owner'))} | {markdown_text(runtime_info.get('load_timing'))} | "
                f"{markdown_text(control_field(control, 'enforcement_type'))} | {markdown_text(evidence_states(control))} | "
                f"{markdown_text(decision_display(decision))} |"
            )
    else:
        lines.append("| No visible controls found | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNDECIDED |")

    lines.extend([
        "",
        "## Run map: what actually shaped one job",
        "",
        f"Trace status: **{markdown_text(run_map['trace_status'])}**",
        "",
        markdown_text(run_map["trace_note"]),
        "",
        "| Funnel stage | Trace status | Observed count | Evidence detail |",
        "|---|---|---:|---|",
    ])
    for stage in run_map["funnel"]:
        count = stage["count"] if stage["count"] is not None else "UNKNOWN"
        lines.append(
            f"| {markdown_text(stage['stage'])} | {markdown_text(stage['status'])} | "
            f"{markdown_text(count)} | {markdown_text(stage['detail'])} |"
        )

    lines.extend(["", "## Cleanup decisions", ""])
    if decisions:
        lines.extend(["### First recommendations", ""])
        for item in decisions[:3]:
            lines.extend([
                f"- **{markdown_text(decision_display(item['decision']))}: {markdown_text(item['control'])}**",
                f"  - Why: {markdown_text(item['reason'])}",
                f"  - Evidence: {markdown_text(item['evidence_state'])}",
            ])
        lines.extend(["", "### Full decision table", ""])
        lines.extend(["| Control | Decision | Evidence | Reason |", "|---|---|---|---|"])
        for item in decisions:
            lines.append(
                f"| {markdown_text(item['control'])} | {markdown_text(decision_display(item['decision']))} | "
                f"{markdown_text(item['evidence_state'])} | {markdown_text(item['reason'])} |"
            )
    else:
        lines.append("No cleanup decisions were made by the static scanner. Review or trace evidence is required first.")

    lines.extend(["", "## Coverage", "", "| Area | Evidence state | Detail |", "|---|---|---|"])
    for item in coverage:
        lines.append(
            f"| {markdown_text(item.get('area'))} | {markdown_text(item.get('evidence_state'))} | "
            f"{markdown_text(item.get('detail'))} |"
        )
    if not coverage:
        lines.append("| Coverage not supplied | UNKNOWN | The map did not declare its coverage. |")

    lines.extend([
        "",
        "## Evidence-state key",
        "",
        "- **VERIFIED:** Directly observed in the bounded evidence available to this report.",
        "- **USER_REPORTED:** Supplied by the caller but not independently verified.",
        "- **INFERRED:** Suggested by static evidence; runtime behavior was not observed.",
        "- **INACCESSIBLE:** The surface or selected scope did not expose the evidence.",
        "- **NOT_APPLICABLE:** The static scan cannot answer this type of question.",
        "",
        f"Generated: {markdown_text(payload.get('generated_at'))}",
        "",
    ])
    return "\n".join(lines)


def render_html(payload: dict[str, Any]) -> str:
    runtime = normalize_runtime(payload)
    setup = payload["setup_map"]
    controls = [item for item in setup.get("controls", []) if isinstance(item, dict)]
    summary = setup.get("summary") if isinstance(setup.get("summary"), dict) else {}
    run_map = normalize_run_map(payload)
    blind_spots = [item for item in payload.get("blind_spots", []) if isinstance(item, dict)]
    coverage = [item for item in payload.get("coverage", []) if isinstance(item, dict)]
    decisions = collect_decisions(payload)
    stations = group_setup_stations(controls)

    station_cards = []
    for index, station in enumerate(stations, start=1):
        station_controls = station["controls"]
        if station_controls:
            examples = "".join(
                f"<li><span>{html_text(control_field(item, 'job'))}</span><code>{html_text(item.get('path'))}</code></li>"
                for item in station_controls[:3]
            )
        else:
            examples = '<li class="unknown">No visible control here. Hidden or unexported controls may still exist.</li>'
        station_cards.append(
            f'<li class="station"><span class="station-number" aria-hidden="true">{index}</span>'
            f'<h3>{html_text(station["title"])}</h3><p>{html_text(station["description"])}</p>'
            f'<strong>{len(station_controls)} visible</strong><ul>{examples}</ul></li>'
        )

    blind_rows = "".join(
        "<tr>"
        f"<th scope=\"row\">{html_text(item.get('id'))}</th>"
        f"<td><span class=\"state\">{html_text(item.get('evidence_state'))}</span></td>"
        f"<td>{html_text(blind_spot_detail(item))}</td>"
        "</tr>"
        for item in blind_spots
    ) or '<tr><td colspan="3">No blind spots were declared. That absence is not proof of complete coverage.</td></tr>'

    control_rows = []
    for control in controls:
        runtime_info = control.get("runtime") if isinstance(control.get("runtime"), dict) else {}
        decision, _ = control_decision(control)
        control_rows.append(
            "<tr>"
            f"<th scope=\"row\"><code>{html_text(control.get('path'))}</code></th>"
            f"<td>{html_text(control_field(control, 'job'))}</td>"
            f"<td>{html_text(control_field(control, 'owner'))}</td>"
            f"<td>{html_text(runtime_info.get('load_timing'))}</td>"
            f"<td>{html_text(control_field(control, 'enforcement_type'))}</td>"
            f"<td>{html_text(evidence_states(control))}</td>"
            f"<td>{html_text(decision_display(decision))}</td>"
            "</tr>"
        )
    if not control_rows:
        control_rows.append('<tr><td colspan="7">No visible controls were found inside the selected scan bounds.</td></tr>')

    funnel_items = "".join(
        "<li>"
        f"<h3>{html_text(stage['stage'])}</h3>"
        f"<p><span class=\"state\">{html_text(stage['status'])}</span> · "
        f"Count: {html_text(stage['count'] if stage['count'] is not None else 'UNKNOWN')}</p>"
        f"<p>{html_text(stage['detail'])}</p>"
        "</li>"
        for stage in run_map["funnel"]
    )

    if decisions:
        recommendation_cards = "".join(
            '<article class="recommendation">'
            f'<p class="state">{html_text(decision_display(item["decision"]))}</p>'
            f'<h3>{html_text(item["control"])}</h3>'
            f'<p>{html_text(item["reason"])}</p>'
            f'<small>Evidence: {html_text(item["evidence_state"])}</small>'
            '</article>'
            for item in decisions[:3]
        )
        decision_rows = "".join(
            "<tr>"
            f"<th scope=\"row\">{html_text(item['control'])}</th>"
            f"<td>{html_text(decision_display(item['decision']))}</td>"
            f"<td>{html_text(item['evidence_state'])}</td>"
            f"<td>{html_text(item['reason'])}</td>"
            "</tr>"
            for item in decisions
        )
        decision_content = (
            '<h3>First recommendations</h3><div class="recommendations">' + recommendation_cards + '</div>'
            '<h3>Full decision table</h3>'
            '<div class="table-wrap" tabindex="0" role="region" aria-label="Cleanup decisions table">'
            '<table><caption>Declared cleanup decisions</caption><thead><tr>'
            '<th scope="col">Control</th><th scope="col">Decision</th><th scope="col">Evidence</th>'
            '<th scope="col">Reason</th></tr></thead><tbody>' + decision_rows + "</tbody></table></div>"
        )
    else:
        decision_content = (
            '<p class="empty"><strong>No cleanup decisions yet.</strong> The static scanner deliberately leaves controls '
            "undecided until review or trace evidence supports a change.</p>"
        )

    coverage_rows = "".join(
        "<tr>"
        f"<th scope=\"row\">{html_text(item.get('area'))}</th>"
        f"<td><span class=\"state\">{html_text(item.get('evidence_state'))}</span></td>"
        f"<td>{html_text(item.get('detail'))}</td>"
        "</tr>"
        for item in coverage
    ) or '<tr><td colspan="3">Coverage was not supplied. Treat the report as incomplete.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>What shapes your AI before you type</title>
  <style>
    :root {{ color-scheme: light; --ink:#17211b; --muted:#536158; --paper:#fbfaf6; --panel:#fff; --line:#cfd8d1; --accent:#1d5a43; --accent-soft:#e7f2ec; --warning:#7a3d00; --warning-bg:#fff1dc; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--paper); font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    a {{ color:var(--accent); }}
    a:focus-visible, [tabindex]:focus-visible {{ outline:3px solid #0067c5; outline-offset:3px; }}
    .skip {{ position:absolute; left:1rem; top:-5rem; padding:.7rem 1rem; background:#fff; z-index:10; }}
    .skip:focus {{ top:1rem; }}
    header, main, footer {{ width:min(1120px, calc(100% - 2rem)); margin-inline:auto; }}
    header {{ padding:3.5rem 0 1.5rem; }}
    h1 {{ font-size:clamp(2rem,5vw,4rem); line-height:1.05; max-width:16ch; margin:0 0 1rem; }}
    h2 {{ font-size:clamp(1.4rem,3vw,2rem); margin:0 0 .8rem; }}
    h3 {{ margin:.1rem 0 .3rem; }}
    .lede {{ max-width:72ch; font-size:1.15rem; color:var(--muted); }}
    section {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:clamp(1rem,3vw,2rem); margin:1rem 0; }}
    .warning {{ border-left:7px solid var(--warning); background:var(--warning-bg); }}
    .runtime, .metrics {{ display:grid; gap:.75rem; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); margin:1rem 0 0; }}
    .metric {{ padding:1rem; background:var(--accent-soft); border-radius:10px; }}
    .metric strong {{ display:block; font-size:1.45rem; }}
    .eyebrow {{ margin:0 0 .6rem; color:var(--accent); font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
    .state {{ display:inline-block; padding:.12rem .45rem; border:1px solid currentColor; border-radius:999px; font-size:.8rem; font-weight:750; letter-spacing:.02em; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:9px; }}
    table {{ border-collapse:collapse; width:100%; min-width:720px; }}
    caption {{ text-align:left; padding:.85rem; font-weight:750; }}
    th, td {{ border-top:1px solid var(--line); padding:.75rem; text-align:left; vertical-align:top; }}
    thead th {{ background:#edf1ed; }}
    tbody th {{ font-weight:650; }}
    code {{ overflow-wrap:anywhere; }}
    .funnel {{ display:grid; gap:.7rem; list-style:none; padding:0; counter-reset:stage; }}
    .funnel li {{ position:relative; padding:1rem 1rem 1rem 4rem; border:1px solid var(--line); border-radius:10px; }}
    .funnel li::before {{ counter-increment:stage; content:counter(stage); position:absolute; left:1rem; top:1rem; width:2rem; height:2rem; border-radius:50%; display:grid; place-items:center; color:#fff; background:var(--accent); font-weight:800; }}
    .funnel p {{ margin:.2rem 0; }}
    .stations {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:.65rem; list-style:none; padding:0; margin:1.25rem 0 1.75rem; }}
    .station {{ position:relative; min-width:0; padding:1rem; border:1px solid var(--line); border-top:5px solid var(--accent); border-radius:10px; background:#f8fbf9; }}
    .station:not(:last-child)::after {{ content:"→"; position:absolute; right:-.62rem; top:1rem; z-index:2; width:1.2rem; height:1.2rem; display:grid; place-items:center; color:var(--accent); background:var(--paper); font-weight:900; }}
    .station-number {{ display:grid; place-items:center; width:1.8rem; height:1.8rem; margin-bottom:.65rem; border-radius:50%; color:#fff; background:var(--accent); font-weight:800; }}
    .station > strong {{ display:block; margin:.8rem 0 .35rem; }}
    .station ul {{ list-style:none; padding:0; margin:.35rem 0 0; }}
    .station li {{ padding:.45rem 0; border-top:1px solid var(--line); }}
    .station li span, .station li code {{ display:block; }}
    .station li span {{ color:var(--muted); font-size:.78rem; }}
    .station .unknown {{ color:var(--muted); font-size:.88rem; }}
    .recommendations {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.75rem; margin:0 0 1.5rem; }}
    .recommendation {{ padding:1rem; border:1px solid var(--line); border-radius:10px; background:var(--accent-soft); }}
    .empty {{ padding:1rem; border:2px dashed var(--line); border-radius:10px; }}
    footer {{ padding:1.5rem 0 3rem; color:var(--muted); }}
    @media (max-width:900px) {{ .stations {{ grid-template-columns:1fr; }} .station:not(:last-child)::after {{ content:"↓"; right:auto; left:1.3rem; top:auto; bottom:-.9rem; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto !important; }} }}
  </style>
</head>
<body>
  <a class="skip" href="#main">Skip to report</a>
  <header>
    <p class="eyebrow">Your AI Setup Map</p>
    <h1>What shapes your AI before you type</h1>
    <p class="state">READ-ONLY STATIC MAP</p>
    <p class="lede">This report keeps two different questions separate: what controls are visible or declared in the setup, and what trace evidence proves actually shaped one job.</p>
    <div class="runtime" aria-label="Reported runtime">
      <div class="metric"><span>Reported surface</span><strong>{html_text(runtime['surface'])}</strong><small>{html_text(runtime['surface_evidence'])}</small></div>
      <div class="metric"><span>Reported model or router</span><strong>{html_text(runtime['model'])}</strong><small>{html_text(runtime['model_evidence'])}</small></div>
    </div>
  </header>
  <main id="main">
    <section class="warning" aria-labelledby="blind-spots-title">
      <h2 id="blind-spots-title">Blind spots</h2>
      <p><strong>Do not treat this map as a complete record of the product runtime.</strong> These limits remain visible by design.</p>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Blind spots table">
        <table><caption>Evidence the selected surface did not expose</caption><thead><tr><th scope="col">Area</th><th scope="col">Evidence</th><th scope="col">What remains unknown</th></tr></thead><tbody>{blind_rows}</tbody></table>
      </div>
    </section>

    <section aria-labelledby="setup-title">
      <h2 id="setup-title">Setup map: what is visible or declared</h2>
      <p>These files were present inside the bounded scan. Presence does not prove that the runtime loaded or followed them.</p>
      <div class="metrics">
        <div class="metric"><span>Visible controls</span><strong>{html_text(summary.get('visible_controls'), str(len(controls)))}</strong></div>
        <div class="metric"><span>Inspected bytes</span><strong>{html_text(summary.get('inspected_bytes'))}</strong></div>
        <div class="metric"><span>Undecided controls</span><strong>{html_text(summary.get('undecided_controls'))}</strong></div>
      </div>
      <ol class="stations" aria-label="Five stations in the visible AI setup">{''.join(station_cards)}</ol>
      <h3>Visible-control drill-down</h3>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Visible setup controls table">
        <table><caption>Target-relative controls visible to the scanner</caption><thead><tr><th scope="col">Control</th><th scope="col">Job</th><th scope="col">Owner</th><th scope="col">Load timing</th><th scope="col">Control type</th><th scope="col">Evidence</th><th scope="col">Decision</th></tr></thead><tbody>{''.join(control_rows)}</tbody></table>
      </div>
    </section>

    <section aria-labelledby="run-title">
      <h2 id="run-title">Run map: what actually shaped one job</h2>
      <p><span class="state">{html_text(run_map['trace_status'])}</span> {html_text(run_map['trace_note'])}</p>
      <ol class="funnel" aria-label="Run evidence funnel">{funnel_items}</ol>
    </section>

    <section aria-labelledby="decision-title">
      <h2 id="decision-title">Cleanup decisions</h2>
      {decision_content}
    </section>

    <section aria-labelledby="coverage-title">
      <h2 id="coverage-title">Coverage</h2>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Coverage and evidence table">
        <table><caption>What each evidence state can support</caption><thead><tr><th scope="col">Area</th><th scope="col">Evidence state</th><th scope="col">Detail</th></tr></thead><tbody>{coverage_rows}</tbody></table>
      </div>
      <h3>Evidence-state key</h3>
      <dl>
        <dt><strong>VERIFIED</strong></dt><dd>Directly observed in the bounded evidence available to this report.</dd>
        <dt><strong>USER_REPORTED</strong></dt><dd>Supplied by the caller but not independently verified.</dd>
        <dt><strong>INFERRED</strong></dt><dd>Suggested by static evidence; runtime behavior was not observed.</dd>
        <dt><strong>INACCESSIBLE</strong></dt><dd>The surface or selected scope did not expose the evidence.</dd>
        <dt><strong>NOT_APPLICABLE</strong></dt><dd>The static scan cannot answer this type of question.</dd>
      </dl>
    </section>
  </main>
  <footer>Generated {html_text(payload.get('generated_at'))}. Audited text was treated as untrusted data and was not reproduced in this report.</footer>
</body>
</html>
"""


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def validate_paths(source: Path, output_html: Path, output_markdown: Path) -> None:
    source = source.expanduser().resolve()
    html_path = output_html.expanduser().resolve(strict=False)
    markdown_path = output_markdown.expanduser().resolve(strict=False)
    if html_path == markdown_path:
        raise RenderError("HTML and Markdown outputs must be different files")
    if source in {html_path, markdown_path}:
        raise RenderError("Renderer outputs must not overwrite the input map")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_json", type=Path, metavar="MAP_JSON")
    parser.add_argument("--output-html", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_paths(args.map_json, args.output_html, args.output_markdown)
        payload = load_map(args.map_json)
        html_report = render_html(payload)
        markdown_report = render_markdown(payload)
        atomic_write_text(args.output_html, html_report)
        atomic_write_text(args.output_markdown, markdown_report)
    except (OSError, RenderError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "html": str(args.output_html),
        "markdown": str(args.output_markdown),
        "run_trace": normalize_run_map(payload)["trace_status"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
