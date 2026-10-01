"""Tests for preready/image_normalizer.py."""
import os
import tempfile
import pytest
from preready.image_normalizer import find_image_files, normalize_images


def test_find_image_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        p1 = os.path.join(tmp_dir, "pages", "page-3")
        os.makedirs(p1, exist_ok=True)
        open(os.path.join(p1, "img-0.jpeg"), "wb").write(b"mock_bytes")

        img_map = find_image_files(tmp_dir)
        assert "img-0.jpeg" in img_map


def test_normalize_images_and_captions():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_img = os.path.join(tmp_dir, "img-0.jpeg")
        open(src_img, "wb").write(b"mock_img_content")
        img_map = {"img-0.jpeg": src_img}
        assets_dir = os.path.join(tmp_dir, "assets", "figures")

        md_text = (
            "Clinical findings are shown below:\n\n"
            "![img-0.jpeg](img-0.jpeg)\n\n"
            "Fig. 1.1 Likelihood ratio of Kernig sign in meningitis.\n\n"
            "Next text."
        )

        norm_text, audits = normalize_images(md_text, img_map, assets_dir, ch_num=1)
        assert "![Fig 1.1: Likelihood ratio of Kernig sign in meningitis.](assets/figures/ch01_fig_01.jpeg)" in norm_text
        assert os.path.exists(os.path.join(assets_dir, "ch01_fig_01.jpeg"))
        assert len(audits) == 1
        assert audits[0]["copied"] is True


def test_normalize_images_cross_chapter_caption_does_not_mutate_ch_num():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src1 = os.path.join(tmp_dir, "img-0.jpeg")
        src2 = os.path.join(tmp_dir, "img-1.jpeg")
        open(src1, "wb").write(b"img1")
        open(src2, "wb").write(b"img2")
        img_map = {"img-0.jpeg": src1, "img-1.jpeg": src2}
        assets_dir = os.path.join(tmp_dir, "assets", "figures")

        # Chapter 5 text: first image has no caption (should be ch05_fig_01),
        # second image has cross-ref Fig 1.1 citation (should be ch01_fig_01 without corrupting chapter 5 context)
        md_text = (
            "![img-0.jpeg](img-0.jpeg)\n\n"
            "Some text in chapter 5.\n\n"
            "![img-1.jpeg](img-1.jpeg)\n\n"
            "Fig. 1.1 Citation of diagnostic flowchart.\n\n"
        )

        norm_text, audits = normalize_images(md_text, img_map, assets_dir, ch_num=5)
        # Verify first image gets chapter 5 fallback fig 01
        assert "ch05_fig_01.jpeg" in norm_text
        # Verify second image matches caption
        assert "ch01_fig_01.jpeg" in norm_text
        assert len(audits) == 2
        assert audits[0]["canonical_name"] == "ch05_fig_01.jpeg"
        assert audits[1]["canonical_name"] == "ch01_fig_01.jpeg"


def test_normalize_images_forward_fallback_order():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src1 = os.path.join(tmp_dir, "img-0.jpeg")
        src2 = os.path.join(tmp_dir, "img-1.jpeg")
        src3 = os.path.join(tmp_dir, "img-2.jpeg")
        for p in (src1, src2, src3):
            open(p, "wb").write(b"bytes")
        img_map = {"img-0.jpeg": src1, "img-1.jpeg": src2, "img-2.jpeg": src3}
        assets_dir = os.path.join(tmp_dir, "assets", "figures")

        md_text = (
            "First image:\n![img-0.jpeg](img-0.jpeg)\n\n"
            "Second image:\n![img-1.jpeg](img-1.jpeg)\n\n"
            "Third image:\n![img-2.jpeg](img-2.jpeg)\n\n"
        )

        norm_text, audits = normalize_images(md_text, img_map, assets_dir, ch_num=7)
        assert len(audits) == 3
        # In forward document order: fig_01, fig_02, fig_03
        assert audits[0]["canonical_name"] == "ch07_fig_01.jpeg"
        assert audits[1]["canonical_name"] == "ch07_fig_02.jpeg"
        assert audits[2]["canonical_name"] == "ch07_fig_03.jpeg"


def test_normalize_images_collision_and_sub_numbering():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src1 = os.path.join(tmp_dir, "img-0.jpeg")
        src2 = os.path.join(tmp_dir, "img-1.jpeg")
        src3 = os.path.join(tmp_dir, "img-2.jpeg")
        src4 = os.path.join(tmp_dir, "img-3.jpeg")
        for p in (src1, src2, src3, src4):
            open(p, "wb").write(b"bytes")
        img_map = {"img-0.jpeg": src1, "img-1.jpeg": src2, "img-2.jpeg": src3, "img-3.jpeg": src4}
        assets_dir = os.path.join(tmp_dir, "assets", "figures")

        md_text = (
            "![img-0.jpeg](img-0.jpeg)\n\n"
            "Fig. 2.1 Main diagram Panel A.\n\n"
            "![img-1.jpeg](img-1.jpeg)\n\n"
            "Fig. 2.1 Main diagram Panel B.\n\n"
            "![img-2.jpeg](img-2.jpeg)\n\n"  # Uncaptioned - should take fig_02
            "![img-3.jpeg](img-3.jpeg)\n\n"
            "Fig. 2.3 Other figure.\n\n"
        )

        norm_text, audits = normalize_images(md_text, img_map, assets_dir, ch_num=2)
        assert len(audits) == 4
        assert audits[0]["canonical_name"] == "ch02_fig_01.jpeg"
        assert audits[1]["canonical_name"] == "ch02_fig_01_sub01.jpeg"
        assert audits[2]["canonical_name"] == "ch02_fig_02.jpeg"
        assert audits[3]["canonical_name"] == "ch02_fig_03.jpeg"
        assert os.path.exists(os.path.join(assets_dir, "ch02_fig_01.jpeg"))
        assert os.path.exists(os.path.join(assets_dir, "ch02_fig_01_sub01.jpeg"))
        assert os.path.exists(os.path.join(assets_dir, "ch02_fig_02.jpeg"))
        assert os.path.exists(os.path.join(assets_dir, "ch02_fig_03.jpeg"))


def test_normalize_images_single_number_and_bold():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src1 = os.path.join(tmp_dir, "img-0.jpeg")
        src2 = os.path.join(tmp_dir, "img-1.jpeg")
        open(src1, "wb").write(b"bytes1")
        open(src2, "wb").write(b"bytes2")
        img_map = {"img-0.jpeg": src1, "img-1.jpeg": src2}
        assets_dir = os.path.join(tmp_dir, "assets", "figures")

        md_text = (
            "![img-0.jpeg](img-0.jpeg)\n\n"
            "Figure 1: Risk factor for dengue haemorrhagic fever.\n\n"
            "![img-1.jpeg](img-1.jpeg)\n\n"
            "**Figure 8: Monthly trend of dengue cases in 2024.**\n\n"
        )

        norm_text, audits = normalize_images(md_text, img_map, assets_dir, ch_num=1)
        assert len(audits) == 2
        assert audits[0]["canonical_name"] == "ch01_fig_01.jpeg"
        assert audits[0]["fig_key"] == "1.1"
        assert audits[1]["canonical_name"] == "ch01_fig_08.jpeg"
        assert audits[1]["fig_key"] == "1.8"
        assert os.path.exists(os.path.join(assets_dir, "ch01_fig_01.jpeg"))
        assert os.path.exists(os.path.join(assets_dir, "ch01_fig_08.jpeg"))


def test_normalize_images_lookahead_with_intervening_notes():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src = os.path.join(tmp_dir, "img-17.jpeg")
        open(src, "wb").write(b"bytes")
        img_map = {"img-17.jpeg": src}
        assets_dir = os.path.join(tmp_dir, "assets", "figures")

        md_text = (
            "Clinical decision algorithm:\n\n"
            "![img-17.jpeg](img-17.jpeg)\n\n"
            "1. Note on dosing.\n"
            "2. Note on titrating.\n\n"
            "Figure 9.5—Intensifying to injectable therapies in type 2 diabetes. Adapted from Davies.\n\n"
            "Following text."
        )

        norm_text, audits = normalize_images(md_text, img_map, assets_dir, ch_num=9)
        assert len(audits) == 1
        assert audits[0]["canonical_name"] == "ch09_fig_05.jpeg"
        assert audits[0]["fig_key"] == "9.5"
        assert "Intensifying to injectable therapies" in audits[0]["caption"]
        assert "![Fig 9.5: Intensifying to injectable therapies in type 2 diabetes. Adapted from Davies.](assets/figures/ch09_fig_05.jpeg)" in norm_text
        assert "1. Note on dosing." in norm_text
        assert "2. Note on titrating." in norm_text
        assert os.path.exists(os.path.join(assets_dir, "ch09_fig_05.jpeg"))
