"""Tests for preready/header_normalizer.py."""
import pytest
from preready.header_normalizer import clean_ocr_running_headers, normalize_heading_hierarchy


def test_clean_ocr_running_headers():
    text = (
        "Medical\nHIGHER STUDY\n\n2\n\nCLINICAL DECISION-MAKING\n\n# Introduction\n\n"
        "Knowledge is required.\n\n3\n\nNext page text."
    )
    cleaned = clean_ocr_running_headers(text)
    assert "HIGHER STUDY" not in cleaned
    assert "CLINICAL DECISION-MAKING" not in cleaned
    assert "# Introduction" in cleaned
    assert "Knowledge is required." in cleaned
    assert "<!-- page: 2 -->" in cleaned
    assert "<!-- page: 3 -->" in cleaned


def test_normalize_heading_hierarchy():
    text = (
        "# Chapter Title\n\n"
        "# Section A\n\n"
        "# Section B\n\n"
        "Box 1.1 Root Causes\n\n"
        "1.2 Reasons for Error\n"
    )
    normalized = normalize_heading_hierarchy(text)
    assert "# Chapter Title" in normalized
    assert "## Section A" in normalized
    assert "## Section B" in normalized
    assert "### Box 1.1 Root Causes" in normalized
    assert "### 1.2 Reasons for Error" in normalized


def test_clean_ocr_running_headers_preserves_clinical_uppercase_terms():
    text = (
        "ELSEVIER\n\n"
        "142 • CLINICAL DECISION-MAKING\n\n"
        "ECG FINDINGS\n\n"
        "ST elevation in leads II, III, aVF.\n\n"
        "MYOCARDIAL INFARCTION\n\n"
        "Immediate aspirin 300 mg given.\n\n"
        "CHAPTER 1 • CLINICAL DECISION-MAKING\n\n"
        "CLINICAL FEATURES\n\n"
        "Crushing retrosternal chest pain.\n"
    )
    cleaned = clean_ocr_running_headers(text)
    assert "ELSEVIER" not in cleaned
    assert "<!-- page: 142 -->" in cleaned
    assert "CHAPTER 1 • CLINICAL DECISION-MAKING" not in cleaned
    assert "ECG FINDINGS" in cleaned
    assert "MYOCARDIAL INFARCTION" in cleaned
    assert "CLINICAL FEATURES" in cleaned
    assert "Crushing retrosternal chest pain." in cleaned


def test_clean_ocr_running_headers_guideline_and_years():
    text = (
        "National Guideline for the Management of Measles\n\n"
        "Published in:\n\n"
        "2026\n\n"
        "\\( \\therefore m = \\frac{3}{11} \\)\n\n"
        "15\n\n"
        "Clinical guidance content.\n"
    )
    cleaned = clean_ocr_running_headers(text)
    assert "National Guideline for the Management of Measles" not in cleaned
    assert "\\therefore" not in cleaned
    assert "2026" in cleaned
    assert "<!-- page: 15 -->" in cleaned
    assert "Clinical guidance content." in cleaned


def test_clean_ocr_running_headers_supplement_pages_and_mastheads():
    text = (
        "Diabetes Care Volume 49, Supplement 1, January 2026\n\n"
        "https://doi.org/10.2337/dc26-S001\n\n"
        "Downloaded from http://diabetesjournals.org/care/article-pdf/by guest\n\n"
        "S145\n\n"
        "Recommendation 9.4 text.\n\n"
        "Suppl. 22\n\n"
        "Further recommendation text.\n"
    )
    cleaned = clean_ocr_running_headers(text)
    assert "Diabetes Care Volume 49" not in cleaned
    assert "doi.org" not in cleaned
    assert "Downloaded from" not in cleaned
    assert "<!-- page: S145 -->" in cleaned
    assert "<!-- page: S22 -->" in cleaned
    assert "Recommendation 9.4 text." in cleaned



