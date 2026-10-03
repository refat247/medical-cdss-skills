"""One-off: applies migrate_checkpoint_schema_to_v2() to Chapter 05's real
checkpoint, which had picked up a MIXED schema state (old ambiguous
`pipeline_version` field co-existing with the new
`last_processed_with_pipeline_version` field, written by
rerun_stage6_ch05.py's mark_stage_complete() calls, which -- unlike
load_or_create_checkpoint() -- don't trigger schema migration on their own
since they use load_checkpoint(), not load_or_create_checkpoint()).

Backup already taken by hand before running this
(05/_v2_6_2_checkpoint_backup/CHECKPOINT.json.pre-schema-v2-migration.bak).
Losslessly preserves checkpoint_created_with_pipeline_version == "2.5.1"
(Chapter 05's real historical creation version) -- never overwrites it with
the installed version.

v2.6.3 SAFETY GUARDRAIL: retrofitted to use the new explicit
migrate_checkpoint_schema() API (checkpoint_utils.py, v2.6.3 requirement 1)
instead of calling migrate_checkpoint_schema_to_v2() + save_checkpoint()
directly. Default is dry-run (prints the before/after plan, writes
nothing); pass --apply to actually migrate. migrate_checkpoint_schema()
itself takes its own timestamped backup before writing (backup=True
default), on top of the pre-existing hand-taken backup referenced above.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.checkpoint_utils import read_checkpoint, migrate_checkpoint_schema, checkpoint_path_for

OUT_DIR = r"D:\davidson_25_full_pipeline\05"
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                         help="Actually migrate and persist. Default is dry-run.")
    args = parser.parse_args(argv)

    cp_path = checkpoint_path_for(OUT_DIR, PREFIX)
    checkpoint, _ = read_checkpoint(OUT_DIR, PREFIX)
    before = dict(checkpoint["chapter_info"])

    result = migrate_checkpoint_schema(checkpoint, cp_path, dry_run=not args.apply, backup=True)

    print("Before:", json.dumps(before, indent=2))
    print("After: ", json.dumps(checkpoint["chapter_info"], indent=2))
    print("Result:", json.dumps(result, indent=2))

    if args.apply and result["migrated"]:
        assert checkpoint["chapter_info"]["checkpoint_created_with_pipeline_version"] == "2.5.1"
        assert "pipeline_version" not in checkpoint["chapter_info"]
        print("Verified: historical creation version preserved as 2.5.1, old ambiguous field removed.")
    elif not args.apply:
        print("[DRY RUN] Nothing written. Re-run with --apply to migrate for real.")
    return result


if __name__ == "__main__":
    main()
