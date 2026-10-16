"""Render one claim ledger as output version 1, 2, 3, or 4.

Output versions are reading shapes. They are not the skill package SemVer.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

STATUSES = {
    "SUPPORTED": "SUPPORTED",
    "SLIDE_PAPER": "SLIDE-PAPER",
    "DO_NOT_SAY": "DO NOT SAY",
    "CONFLICT": "CONFLICT",
}


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "groups" not in data or "ward_limit" not in data:
        raise SystemExit("ledger missing groups or ward_limit")
    return data


def claims(data: dict):
    for group in data["groups"]:
        for claim in group["claims"]:
            yield group, claim


def render_v1(data: dict) -> str:
    books, guides, refused = [], [], []
    for group, claim in claims(data):
        line = f"- Slide {claim['slide']}: {claim['claim']} Say: {claim['say']} Locator: {claim['locator']}"
        if claim["status"] == "DO_NOT_SAY":
            refused.append(line)
        elif "PDF" in claim["locator"] or "ESC" in claim["locator"] or "AHA" in claim["locator"]:
            guides.append(line)
        else:
            books.append(line)
    parts = [
        f"# {data['deck_title']}",
        "",
        "Citation map. Books, then guidelines, then what not to say.",
        "",
        f"Ward limit: {data['ward_limit']}",
        "",
        "## Books",
        *books,
        "",
        "## Guidelines",
        *guides,
        "",
        "## Do not say",
        *refused,
        "",
    ]
    return "\n".join(parts)


def render_v2(data: dict) -> str:
    lines = [f"# {data['deck_title']}", "", data["one_sentence"], "", f"Ward limit: {data['ward_limit']}", ""]
    for group in data["groups"]:
        lines.append(f"## {group['title']}")
        lines.append("")
        lines.append(group["bridge"])
        bits = []
        for claim in group["claims"]:
            bits.append(f"{claim['say']} ({claim['locator']})")
        lines.append(" ".join(bits))
        lines.append("")
    return "\n".join(lines)


def render_v3(data: dict) -> str:
    lines = [
        f"# {data['deck_title']}",
        "",
        "## How to defend the talk",
        "### The line you must not cross",
        "",
        data["one_sentence"],
        "",
        data["ward_limit"],
        "",
        "## The talk",
    ]
    for group in data["groups"]:
        lines.extend(["", f"### {group['title']}", "", group["bridge"], ""])
        for claim in group["claims"]:
            lines.append(f"The slide says: {claim['claim']}")
            lines.append(f"What you may say: {claim['say']}")
            if claim.get("if_asked"):
                lines.append(f"If asked: {claim['if_asked']}")
            lines.append(f"Source: {claim['locator']}")
            lines.append("")
    lines.extend(["## If you are stopped", "### Questions", ""])
    for item in data.get("questions", []):
        lines.append(f"{item['q']} {item['a']} Locator: {item['locator']}")
        lines.append("")
    return "\n".join(lines)


def render_v4(data: dict) -> str:
    lines = [
        f"# {data['deck_title']}",
        "",
        "## Before you speak",
        "### The ward limit",
        "",
        data["ward_limit"],
        "",
        data["one_sentence"],
        "",
        "## The talk",
    ]
    for group in data["groups"]:
        lines.extend(["", f"### {group['title']}", "", group["bridge"], ""])
        for claim in group["claims"]:
            label = STATUSES[claim["status"]]
            lines.append(f"{label}. {claim['claim']} Say: {claim['say']} Locator: {claim['locator']} Ward: {claim['ward']}")
            lines.append("")
    lines.extend(["## If you are stopped", "### One sentence", "", data["one_sentence"], ""])
    return "\n".join(lines)


RENDERERS = {1: render_v1, 2: render_v2, 3: render_v3, 4: render_v4}


def render(data: dict, version: int) -> str:
    if version not in RENDERERS:
        raise SystemExit("output version must be 1, 2, 3, or 4")
    text = RENDERERS[version](data)
    if data["ward_limit"] not in text:
        raise SystemExit("ward limit dropped")
    return text


def maybe_html(md_path: Path, html_path: Path, title: str) -> str:
    builder = os.environ.get("DOCTOR_SLIDE_DEFENSE_HTML_BUILDER", "")
    if not builder:
        return "HTML NOT BUILT: DOCTOR_SLIDE_DEFENSE_HTML_BUILDER is unset"
    if not Path(builder).is_file():
        return "HTML NOT BUILT: builder path is not a file"
    proc = subprocess.run(
        [sys.executable, builder, str(md_path), "--title", title, "--book", "medicine", "--out", str(html_path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return "HTML NOT BUILT: " + (proc.stderr or proc.stdout or "builder failed").strip()
    return "HTML BUILT: " + str(html_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger")
    parser.add_argument("--output-version", type=int, required=True, choices=(1, 2, 3, 4))
    parser.add_argument("--out", required=True)
    parser.add_argument("--html")
    args = parser.parse_args()
    data = load(Path(args.ledger))
    text = render(data, args.output_version)
    out = Path(args.out)
    out.write_text(text, encoding="utf-8")
    print(f"WROTE output-version {args.output_version} {out}")
    if args.html:
        print(maybe_html(out, Path(args.html), data["deck_title"]))


if __name__ == "__main__":
    main()
