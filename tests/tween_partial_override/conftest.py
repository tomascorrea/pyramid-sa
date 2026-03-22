"""Fixtures for partial error formatter override tests."""

import pytest
from sqlalchemy import create_engine
from tests.tween_partial_override.app import create_app

from pyramid_sa import Base


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app with only not_found formatter overridden."""
    return create_app(dbengine=db_engine)
