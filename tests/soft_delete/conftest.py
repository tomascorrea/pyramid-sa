"""Fixtures for soft delete tests."""

import psycopg
import pytest

from pyramid_sa import Base
from tests.conftest import _pg_engine
from tests.soft_delete.app import create_app


@pytest.fixture(scope="session")
def db_engine(postgresql_proc):
    """Separate database — tables created after app config transforms constraints.

    Soft-delete transforms unique constraints into partial indexes. A dedicated
    database avoids conflicts with other test modules that create tables before
    the transformation runs.
    """
    with psycopg.connect(
        host=postgresql_proc.host,
        port=postgresql_proc.port,
        user=postgresql_proc.user,
        dbname="postgres",
        autocommit=True,
    ) as conn:
        conn.execute("CREATE DATABASE test_soft_delete")

    engine = _pg_engine(postgresql_proc, dbname="test_soft_delete")
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
