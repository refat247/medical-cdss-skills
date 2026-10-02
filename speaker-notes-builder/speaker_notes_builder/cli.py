from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .clinical import lint_scripts
from .core import allocate_timing, inspect_deck
from .docx_builder import build_docx
from .qa import build_quality_report, inject_notes, validate_project, verify_docx, verify_pptx


def _print(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def schema_validate(project: Path) -> dict:
    root = Path(__file__).resolve().parent.parent
    source_schema_dir = root / "schemas"
    packaged_schema_dir = Path(__file__).resolve().parent / "resources" / "schemas"
    schema_dir = source_schema_dir if source_schema_dir.exists() else packaged_schema_dir
    pairs = [
        (project / "deck_analysis.json", schema_dir / "deck_analysis.schema.json"),
        (project / "slide_briefs.json", schema_dir / "slide_briefs.schema.json"),
        (project / "scripts.json", schema_dir / "scripts.schema.json"),
        (project / "claim_ledger.json", schema_dir / "claim_ledger.schema.json"),
    ]
    errors = []
    for data_path, schema_path in pairs:
        if not data_path.exists():
            continue
        data = json.loads(data_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        v = Draft202012Validator(schema)
        for e in sorted(v.iter_errors(data), key=lambda x: list(x.path)):
            errors.append(f"{data_path.name}: {'/'.join(str(p) for p in e.path)}: {e.message}")
    return {"status": "FAIL" if errors else "PASS", "errors": errors}


def main(argv=None):
    p = argparse.ArgumentParser(prog="speaker-notes-builder")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("inspect")
    s.add_argument("--input", required=True)
    s.add_argument("--project", required=True)
    s.add_argument("--profile", default="default")
    s.add_argument("--dpi", type=int, default=150)

    s = sub.add_parser("allocate")
    s.add_argument("--project", required=True)
    s.add_argument("--talk-minutes", type=float, required=True)
    s.add_argument("--qa-minutes", type=float, default=0)

    s = sub.add_parser("validate")
    s.add_argument("--project", required=True)

    s = sub.add_parser("clinical-lint")
    s.add_argument("--project", required=True)

    s = sub.add_parser("build-docx")
    s.add_argument("--project", required=True)
    s.add_argument("--mode", choices=["rehearsal", "live"], default="rehearsal")
    s.add_argument("--output")

    s = sub.add_parser("inject")
    s.add_argument("--project", required=True)
    s.add_argument("--output", required=True)

    s = sub.add_parser("verify-docx")
    s.add_argument("--docx", required=True)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--project")

    s = sub.add_parser("verify-pptx")
    s.add_argument("--project", required=True)
    s.add_argument("--pptx", required=True)

    s = sub.add_parser("qa")
    s.add_argument("--project", required=True)

    args = p.parse_args(argv)
    if args.cmd == "inspect":
        _print(inspect_deck(args.input, args.project, args.profile, args.dpi))
    elif args.cmd == "allocate":
        _print(allocate_timing(args.project, args.talk_minutes, args.qa_minutes))
    elif args.cmd == "validate":
        project = Path(args.project)
        schema = schema_validate(project)
        base = validate_project(project)
        if schema["status"] == "FAIL":
            base["status"] = "FAIL"
            base.setdefault("problems", []).extend(schema["errors"])
            (project / "validation_report.json").write_text(json.dumps(base, indent=2), encoding="utf-8")
        _print(base)
    elif args.cmd == "clinical-lint":
        _print(lint_scripts(args.project))
    elif args.cmd == "build-docx":
        out = build_docx(args.project, args.mode, args.output)
        _print({"status": "BUILT", "path": str(out)})
    elif args.cmd == "inject":
        out = inject_notes(args.project, args.output)
        _print({"status": "BUILT", "path": str(out)})
    elif args.cmd == "verify-docx":
        _print(verify_docx(args.docx, args.output_dir, args.project))
    elif args.cmd == "verify-pptx":
        _print(verify_pptx(args.project, args.pptx))
    elif args.cmd == "qa":
        _print(build_quality_report(args.project))


if __name__ == "__main__":
    main()
