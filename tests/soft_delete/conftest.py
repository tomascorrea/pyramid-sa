"""Fixtures for soft delete tests."""

import pytest
from sqlalchemy import create_engine

from pyramid_sa import Base, get_tm_session
from tests.soft_delete.app import create_app, create_app_no_soft_delete


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


@pytest.fixture(scope="session")
def no_sd_app(db_engine):
    """WSGI app with audit only — soft delete NOT enabled."""
    return create_app_no_soft_delete(dbengine=db_engine)


@pytest.fixture()
def no_sd_dbsession(no_sd_app, tm):
    """Session from the app without soft delete."""
    session_factory = no_sd_app.registry["dbsession_factory"]
    return get_tm_session(session_factory, tm)
