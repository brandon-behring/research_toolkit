"""Shared pytest fixtures for the research_toolkit test suite."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def mini_dir() -> Path:
    return FIXTURES / "mini_topic_timeseries_anomaly"


@pytest.fixture(scope="session")
def vol25_dir() -> Path:
    return FIXTURES / "vol25_snapshot" / "real"
