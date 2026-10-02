from pathlib import Path
from PIL import Image
import json

from speaker_notes_builder.core import dhash_image, hamming_hex, allocate_timing


def test_duplicate_hash(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    Image.new("RGB", (100, 100), "white").save(a)
    Image.new("RGB", (100, 100), "white").save(b)
    assert hamming_hex(dhash_image(a), dhash_image(b)) == 0


def test_timing_reconciles(tmp_path):
    manifest = {
        "slides": [
            {"slide": 1, "include": True, "role_guess": "divider", "semantic_density": "low", "is_duplicate_of": None},
            {"slide": 2, "include": True, "role_guess": "evidence", "semantic_density": "high", "is_duplicate_of": None},
            {"slide": 3, "include": True, "role_guess": "case", "semantic_density": "medium", "is_duplicate_of": None}
        ]
    }
    (tmp_path / "deck_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    plan = allocate_timing(tmp_path, talk_minutes=10, qa_minutes=2)
    assert plan["available_speaking_seconds"] == 480
    assert plan["allocated_seconds"] == 480
    assert plan["slides"][1]["allocated_seconds"] > plan["slides"][0]["allocated_seconds"]
