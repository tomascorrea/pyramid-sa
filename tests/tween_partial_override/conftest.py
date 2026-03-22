"""Fixtures for partial error formatter override tests."""

import pytest
from tests.conftest import _pg_engine
from tests.tween_partial_override.app import create_app

from pyramid_sa import Base


@pytest.fixture(scope="session")
def db_engine(postgresql_proc):
    engine = _pg_engine(postgresql_proc)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app with only not_found formatter overridden."""
    return create_app(dbengine=db_engine)
