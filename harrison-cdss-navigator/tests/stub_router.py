"""Stub cdss_qa_router for wrapper CONTRACT tests (no corpus needed). Behaviour is steered by env vars:
STUB_EXIT=<n> exit with n + stderr; STUB_BAD_BYTES=1 emit undecodable bytes; STUB_LONG=1 emit 3000 words."""
import argparse, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--query"); ap.add_argument("--vignette"); ap.add_argument("--outline"); ap.add_argument("--diff")
ap.add_argument("--validate-therapy", nargs="+"); ap.add_argument("--top_k", type=int, default=3)
ap.add_argument("--compress", action="store_true"); ap.add_argument("--json", action="store_true")
ap.add_argument("--comorbidities"); ap.add_argument("--interactive", action="store_true")
a, _ = ap.parse_known_args()

if os.environ.get("STUB_EXIT"):
    print("stub: router crashed", file=sys.stderr)
    print("partial output")
    sys.exit(int(os.environ["STUB_EXIT"]))
if os.environ.get("STUB_BAD_BYTES"):
    sys.stdout.buffer.write(b"abc\xff\xfedef\n"); sys.exit(0)
if os.environ.get("STUB_LONG"):
    words = " ".join(["word"] * 3000)
    print(json.dumps({"query": "x", "latency_ms": 0.1, "chunks": [{"text": words}]}) if a.json else words)
    sys.exit(0)
if a.query and a.json:
    print(json.dumps({"query": a.query, "latency_ms": 0.1, "chunks": [{"chunk_id": "S-1", "topic": "Atrial fibrillation"}]}))
elif a.query or a.vignette:
    print("STUB 11TH ED CDSS RETRIEVAL\nAtrial fibrillation anticoagulation evidence ...\nLatency: 0.1 ms")
elif a.outline:
    print("STUB CONCEPT OUTLINE\nSubfacets: a, b")
elif a.diff:
    print(f"DIFFERENTIAL for {a.diff}")
elif a.validate_therapy:
    print(f"{a.validate_therapy[0].upper()} drug safety matrix")
