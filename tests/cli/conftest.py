"""Fixtures for CLI tests."""

from pathlib import Path

import pytest

from tests.cli.app import create_app


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app built from the simulated consuming app."""
    return create_app(dbengine=db_engine)


@pytest.fixture()
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change into a temporary directory for each test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
