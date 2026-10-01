"""CLI wrapper for CP-08 (pipeline/stages/checkpoint_migration_v2_6_4.py).

Usage:
    python checkpoint_migrate_v2_6_4.py <glob-of-*_CHECKPOINT.json> [--apply]

Default is dry-run (prints the plan for every matching checkpoint, writes
nothing). Pass --apply to actually back up, migrate, and verify each file.

Example:
    python checkpoint_migrate_v2_6_4.py "D:\\davidson_25_full_pipeline\\**\\*_CHECKPOINT.json"
    python checkpoint_migrate_v2_6_4.py "D:\\davidson_25_full_pipeline\\**\\*_CHECKPOINT.json" --apply
"""
import sys
import io
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.stages.checkpoint_migration_v2_6_4 import migrate_checkpoint_file


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    pattern = sys.argv[1]
    apply_mode = "--apply" in sys.argv[2:]

    paths = sorted(glob.glob(pattern, recursive=True))
    if not paths:
        print(f"No files matched pattern: {pattern}")
        raise SystemExit(1)

    print(f"{'APPLY' if apply_mode else 'DRY-RUN'} mode — {len(paths)} checkpoint file(s) matched\n")
    for p in paths:
        try:
            result = migrate_checkpoint_file(p, dry_run=not apply_mode)
        except RuntimeError as e:
            print(f"[FAILED] {p}\n  {e}\n")
            continue
        plan = result["plan"]
        print(f"[{plan['action'].upper()}] {p}")
        print(f"  before: {plan['before']}")
        print(f"  after:  {plan['after']}")
        if apply_mode:
            print(f"  backup: {result['backup_path']}")
            print(f"  verified: {result['verified']}")
        print()


if __name__ == "__main__":
    main()
