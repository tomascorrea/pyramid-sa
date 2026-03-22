"""Fixtures for no-soft-delete tests."""

import pytest
from tests.no_soft_delete.app import create_app


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app with audit only — soft delete NOT enabled."""
    return create_app(dbengine=db_engine)
