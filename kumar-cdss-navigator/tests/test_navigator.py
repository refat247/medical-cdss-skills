"""Unit tests for Kumar & Clark CDSS Navigator interface."""

import json
import os
import pytest
from scripts.navigator import KumarNavigator, ROUTER_PATH

# These tests exercise the real packaged router/corpus; without it they SKIP (wrapper behaviour is covered
# hermetically by test_navigator_contract.py).
pytestmark = pytest.mark.skipif(not os.path.exists(ROUTER_PATH), reason="real CDSS package not present (set CDSS_PACKAGE_DIR)")



def test_navigator_init():
    nav = KumarNavigator()
    assert str(nav.router_path) == ROUTER_PATH
    assert nav.is_available() is True


def test_navigator_query_execution():
    nav = KumarNavigator()
    output = nav.query("Atrial fibrillation anticoagulation", top_k=2, compress=True)
    assert "KUMAR & CLARK 11TH ED CDSS RETRIEVAL" in output
    assert "Atrial fibrillation" in output
    assert "Latency:" in output


def test_navigator_json_output():
    nav = KumarNavigator()
    output = nav.query("Diabetic ketoacidosis", top_k=1, json_output=True)
    data = json.loads(output)
    assert "query" in data
    assert "latency_ms" in data
    assert "chunks" in data
    assert len(data["chunks"]) > 0


def test_navigator_vignette_execution():
    nav = KumarNavigator()
    vignette = "54-year-old female presents with acute jaundice, right upper quadrant pain, and fever with rigors."
    output = nav.vignette(vignette, top_k=2, compress=True)
    assert "KUMAR & CLARK 11TH ED CDSS RETRIEVAL" in output
    assert len(output) > 100


def test_navigator_outline_execution():
    nav = KumarNavigator()
    output = nav.outline("Acid-base")
    assert "KUMAR & CLARK 11TH ED CONCEPT OUTLINE" in output
    assert "Subfacets" in output


def test_navigator_diff_execution():
    nav = KumarNavigator()
    output = nav.diff("Conjunctivitis")
    assert "DIFFERENTIAL" in output or "CONCEPT" in output
    assert "Conjunctivitis" in output


def test_navigator_validate_therapy():
    nav = KumarNavigator()
    output = nav.validate_therapy("Sacubitril")
    assert "SACUBITRIL" in output
    assert "Cardiovascular pharmacotherapy" in output
