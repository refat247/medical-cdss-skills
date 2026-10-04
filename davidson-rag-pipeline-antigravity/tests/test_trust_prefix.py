"""SECOND_SWEEP 1.30: the trust record must follow the newest run's checkpoint, not the alphabetically first."""
import os

from pipeline.stages.trust_ledger import _derive_prefix


def test_newest_checkpoint_wins(tmp_path):
    old, new = tmp_path / "A_old_CHECKPOINT.json", tmp_path / "Z_new_CHECKPOINT.json"
    old.write_text("{}", encoding="utf-8")
    new.write_text("{}", encoding="utf-8")
    os.utime(old, (1_000_000, 1_000_000))
    os.utime(new, (2_000_000, 2_000_000))
    assert _derive_prefix(str(tmp_path)) == "Z_new"


def test_single_checkpoint_and_empty_dir_unchanged(tmp_path):
    assert _derive_prefix(str(tmp_path)) is None
    (tmp_path / "Only_CHECKPOINT.json").write_text("{}", encoding="utf-8")
    assert _derive_prefix(str(tmp_path)) == "Only"
