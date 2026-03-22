"""Fixtures for default tween tests."""

import pytest
from sqlalchemy import create_engine

from pyramid_sa import Base
from tests.tween.app import create_app


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app with default error formatters."""
    return create_app(dbengine=db_engine)
