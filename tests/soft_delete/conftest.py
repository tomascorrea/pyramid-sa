"""Fixtures for soft delete tests."""

import pytest
from sqlalchemy import create_engine

from pyramid_sa import Base
from tests.soft_delete.app import create_app


@pytest.fixture(scope="session")
def db_engine():
    """Bare engine — tables created after app config transforms constraints."""
    engine = create_engine("sqlite://")
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def app(db_engine):
    """WSGI app with soft delete enabled.

    Tables are created AFTER the app so that the unique-index transformation
    has already been applied to the metadata.
    """
    application = create_app(dbengine=db_engine)
    Base.metadata.create_all(db_engine)
    return application
