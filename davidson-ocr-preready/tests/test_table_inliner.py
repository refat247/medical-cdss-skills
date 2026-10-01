"""Tests for preready/table_inliner.py."""
import os
import tempfile
import pytest
from preready.table_inliner import find_table_files, inline_tables


def test_find_table_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        p1 = os.path.join(tmp_dir, "pages", "page-1")
        p2 = os.path.join(tmp_dir, "pages", "page-2")
        os.makedirs(p1, exist_ok=True)
        os.makedirs(p2, exist_ok=True)

        open(os.path.join(p1, "tbl-0.md"), "w").write("| a | b |\n| 1 | 2 |")
        open(os.path.join(p2, "tbl-1.md"), "w").write("| c | d |\n| 3 | 4 |")

        table_map = find_table_files(tmp_dir)
        assert len(table_map) == 2
        assert "tbl-0.md" in table_map
        assert "tbl-1.md" in table_map


def test_inline_tables_with_headings():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tbl_file = os.path.join(tmp_dir, "tbl-0.md")
        with open(tbl_file, "w") as f:
            f.write("| Error | Type |\n| --- | --- |\n| No fault | Disease |")

        table_map = {"tbl-0.md": tbl_file}
        md_text = (
            "# Intro\n\n"
            "1.1 Root causes of diagnostic error\n\n"
            "[tbl-0.md](tbl-0.md)\n\n"
            "Next paragraph."
        )

        inlined, audits = inline_tables(md_text, table_map)
        assert "### 1.1 Root causes of diagnostic error" in inlined
        assert inlined.count("Root causes of diagnostic error") == 1
        assert "| Error | Type |" in inlined
        assert "[tbl-0.md]" not in inlined
        assert len(audits) == 1
        assert audits[0]["status"] == "INLINED"


def test_ensure_table_delimiters_injection():
    from preready.table_inliner import ensure_table_delimiters
    raw_table_no_delim = "| Drug | Route | Dose |\n| Adrenaline | IM | 0.5 mg |"
    fixed = ensure_table_delimiters(raw_table_no_delim)
    assert "| --- | --- | --- |" in fixed

    already_valid = "| Drug | Dose |\n| --- | --- |\n| Salbutamol | 5 mg |"
    assert ensure_table_delimiters(already_valid) == already_valid
