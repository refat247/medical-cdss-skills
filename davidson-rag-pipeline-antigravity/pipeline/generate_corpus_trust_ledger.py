"""v2.6.4 — CLI for the deterministic trust-ledger generator
(pipeline/stages/trust_ledger.py). Corpus-Scale Gate Closure, MUST-FIX #3, part 2.

Usage:
    python generate_corpus_trust_ledger.py <corpus_root> [--write] [--in-place]

Default is dry-run/read-only: scans the corpus, prints the proposed
CORPUS_TRUST_STATUS.md content, and writes it to
<corpus_root>/CORPUS_TRUST_STATUS.md.DRYRUN.report instead of the real file
(guarded_write_file's standard dry-run behavior). Nothing durable is ever
written without explicit authorization.

To actually update the committed CORPUS_TRUST_STATUS.md:
    python generate_corpus_trust_ledger.py <corpus_root> --write --in-place

--in-place is required because CORPUS_TRUST_STATUS.md already exists as a
tracked file — same is_new_file=False contract every other guarded writer
in this pipeline uses. A timestamped backup of the previous ledger is taken
automatically before the real file is overwritten.
"""
import argparse
import sys
import io
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stages.trust_ledger import build_corpus_trust_ledger, render_corpus_trust_status
from pipeline.stages.mutation_guard import guarded_write_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", help="Root directory containing chapter subdirectories.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    ledger = build_corpus_trust_ledger(args.corpus_root)
    content = render_corpus_trust_status(ledger)

    target_path = os.path.join(args.corpus_root, "CORPUS_TRUST_STATUS.md")
    is_new = not os.path.exists(target_path)
    result = guarded_write_file(
        target_path, content, args=args, is_new_file=is_new,
        out_dir=args.corpus_root, prefix=None,
        target_description="the corpus-wide CORPUS_TRUST_STATUS.md trust ledger",
    )

    print(f"\n{len(ledger['chapters'])} chapter(s) classified: "
          f"{sum(1 for c in ledger['chapters'] if c['trusted_for_downstream_use'])} trusted.")
    for c in ledger["chapters"]:
        print(f"  {c['chapter_dir']}: {c['classification']}"
              f"{' [TRUSTED]' if c['trusted_for_downstream_use'] else ''}")
    return result


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main(sys.argv[1:])
