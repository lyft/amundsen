# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item

# This file configures the roundtrip pytest option and skips roundtrip tests without it


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--roundtrip-neptune", action="store_true", default=False, help="Run roundtrip tests. These tests are slow and require \
        a configured neptune instance."
    )
    parser.addoption(
        "--roundtrip-janusgraph", action="store_true", default=False, help="Run roundtrip tests. These tests are slow and require \
        a configured janusgraph instance."
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "roundtrip: mark test as roundtrip")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    roundtrip_neptune: bool = config.getoption("--roundtrip-neptune")
    roundtrip_janusgraph: bool = config.getoption("--roundtrip-janusgraph")
    skip_roundtrip = pytest.mark.skip(reason="need the approprirate --roundtrip-[neptune|janus] option to run")
    for item in items:
        if "NeptuneGremlinProxyTest" in item.keywords and not roundtrip_neptune:
            item.add_marker(skip_roundtrip)
        if "JanusGraphGremlinProxyTest" in item.keywords and not roundtrip_janusgraph:
            item.add_marker(skip_roundtrip)
