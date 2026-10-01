"""Unit tests for Harrison CDSS Navigator interface."""

import pytest
from scripts.navigator import HarrisonNavigator, ROUTER_PATH


def test_navigator_init():
    nav = HarrisonNavigator()
    assert nav.is_available() is True


def test_navigator_query_execution():
    nav = HarrisonNavigator()
    output = nav.query("Acute myocardial infarction", compress=True)
    assert len(output) > 50
