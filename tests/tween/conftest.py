"""Fixtures for default tween tests."""

import pytest

from pyramid_sa import Base
from tests.conftest import _pg_engine
from tests.tween.app import create_app


@pytest.fixture(scope="session")
def db_engine(postgresql_proc):
    engine = _pg_engine(postgresql_proc)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app with default error formatters."""
    return create_app(dbengine=db_engine)
