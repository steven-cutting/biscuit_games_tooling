"""The network gate: cases that download allium run only with BG_TOOLING_NETWORK=1."""

from __future__ import annotations

import os

import pytest

NETWORK = os.environ.get("BG_TOOLING_NETWORK") == "1"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip_network = pytest.mark.skip(reason="set BG_TOOLING_NETWORK=1")
    for item in items:
        if "network" in item.keywords and not NETWORK:
            item.add_marker(skip_network)
