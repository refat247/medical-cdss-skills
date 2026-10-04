"""Unit tests for Harrison CDSS Navigator interface."""

import os
import pytest
from scripts.navigator import HarrisonNavigator, ROUTER_PATH

# These tests exercise the real packaged router/corpus; without it they SKIP (wrapper behaviour is covered
# hermetically by test_navigator_contract.py).
pytestmark = pytest.mark.skipif(not os.path.exists(ROUTER_PATH), reason="real CDSS package not present (set CDSS_PACKAGE_DIR)")



def test_navigator_init():
    nav = HarrisonNavigator()
    assert nav.is_available() is True


def test_navigator_query_execution():
    nav = HarrisonNavigator()
    output = nav.query("Acute myocardial infarction", compress=True)
    assert len(output) > 50
