"""Regenerates fixture_manifest.json's sha256 hashes for the files in this
directory. Run manually whenever a fixture file is deliberately updated
(e.g. re-freezing against a newer, still-approved Chapter 05 state) --
never run automatically as part of the test suite, since that would defeat
the manifest's purpose (detecting silent drift).

Usage: python generate_manifest.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_FILES = {
    "repaired_s2_fixture.md": "Frozen REPAIRED_S2.md snapshot -- Stage 2 output, "
                               "post-repair, pre-chunking source of truth.",
    "chunks_fixture.md": "Frozen chunks.md snapshot -- post-Stage-4B output, WITH the "
                          "v2.6.1 source_lines corrections already applied (L2-080, "
                          "L2-086, L1-056, L2-097, L2-118, L2-126).",
    "rag_optimised_fixture.md": "Frozen RAG_Optimised.md snapshot -- Stage 5 output, "
                                 "consistent with chunks_fixture.md.",
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = {
        "fixture_version": "1.0",
        "source_chapter": "05",
        "approved_under_pipeline_version": "2.6.2",
        "generated_from": "D:\\davidson_25_full_pipeline\\05\\ "
                           "(real Chapter 05 output directory, post v2.6.1 source_lines corrections)",
        "files": {
            name: {"sha256": sha256_of(os.path.join(HERE, name)), "purpose": purpose}
            for name, purpose in FIXTURE_FILES.items()
        },
    }
    out_path = os.path.join(HERE, "fixture_manifest.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {out_path}")
    for name, info in manifest["files"].items():
        print(f"  {name}: {info['sha256'][:16]}...")


if __name__ == "__main__":
    main()
