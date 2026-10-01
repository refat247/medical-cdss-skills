"""Unit tests for Hurst CDSS Navigator interface."""

import os
import pytest
from scripts.navigator import HurstNavigator, ROUTER_PATH


def test_navigator_init():
    nav = HurstNavigator()
    assert str(nav.router_path) == str(ROUTER_PATH)


def test_navigator_outline_execution():
    if not os.path.exists(ROUTER_PATH):
        pytest.skip("Router not found at production path")
    nav = HurstNavigator()
    output = nav.outline("Acute heart failure")
    assert "OUTLINE" in output or "subfacets" in output.lower() or "acute" in output.lower()


def test_navigator_diff_execution():
    if not os.path.exists(ROUTER_PATH):
        pytest.skip("Router not found at production path")
    nav = HurstNavigator()
    output = nav.diff("Takotsubo")
    assert "Takotsubo" in output or "vs" in output.lower()


def test_navigator_validate_therapy():
    if not os.path.exists(ROUTER_PATH):
        pytest.skip("Router not found at production path")
    nav = HurstNavigator()
    output = nav.validate_therapy("Sacubitril/valsartan", "heart failure")
    assert "Sacubitril" in output or "THERAPY" in output or "heart failure" in output.lower()
