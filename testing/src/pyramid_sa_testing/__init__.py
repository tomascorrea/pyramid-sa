"""Pytest plugin for pyramid-sa — auto-discovered via the pytest11 entry point."""

import pytest
import transaction
import webtest
from pyramid.scripting import prepare
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from pyramid_sa import Base, get_tm_session


@pytest.fixture(scope="session")
def pyramid_sa_engine(postgresql_proc):
    """PostgreSQL engine via pytest-postgresql. Override for other backends."""
    url = (
        f"postgresql+psycopg://{postgresql_proc.user}"
        f":@{postgresql_proc.host}:{postgresql_proc.port}/postgres"
    )
    engine = create_engine(url, poolclass=NullPool)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def pyramid_sa_tm():
    """Doomed transaction manager that aborts after each test (auto-rollback)."""
    tm = transaction.TransactionManager(explicit=True)
    tm.begin()
    tm.doom()
    yield tm
    tm.abort()


@pytest.fixture()
def pyramid_sa_dbsession(app, pyramid_sa_tm):
    """Database session bound to the test transaction manager."""
    session_factory = app.registry["dbsession_factory"]
    return get_tm_session(session_factory, pyramid_sa_tm)


@pytest.fixture()
def pyramid_sa_testapp(app, pyramid_sa_tm, pyramid_sa_dbsession):
    """WebTest TestApp with the test session injected."""
    return webtest.TestApp(
        app,
        extra_environ={
            "HTTP_HOST": "example.com",
            "REMOTE_ADDR": "127.0.0.1",
            "tm.active": True,
            "tm.manager": pyramid_sa_tm,
            "app.dbsession": pyramid_sa_dbsession,
        },
    )


@pytest.fixture()
def pyramid_sa_app_request(app, pyramid_sa_tm, pyramid_sa_dbsession):
    """Real Pyramid request for service-layer testing."""
    with prepare(registry=app.registry) as env:
        request = env["request"]
        request.host = "example.com"
        request.environ.update(
            {
                "REMOTE_ADDR": "127.0.0.1",
                "tm.active": True,
                "tm.manager": pyramid_sa_tm,
                "app.dbsession": pyramid_sa_dbsession,
            }
        )
        request.dbsession = pyramid_sa_dbsession
        request.tm = pyramid_sa_tm
        pyramid_sa_dbsession.info["request"] = request
        yield request
