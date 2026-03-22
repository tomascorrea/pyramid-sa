"""Shared test fixtures for pyramid-sa."""

from __future__ import annotations

import uuid  # noqa: TCH003 — needed at runtime for SQLAlchemy mapped annotations
from typing import TYPE_CHECKING

import pytest
import transaction
import webtest
from pyramid.config import Configurator
from pyramid.scripting import prepare
from sqlalchemy import String, create_engine
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import AuditMixin, Base, generate_uuid, get_tm_session

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyramid.request import Request
    from pyramid.router import Router


class Item(AuditMixin, Base):
    """Example model used by tests."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    name: Mapped[str] = mapped_column(String(255))


class TestSecurityPolicy:
    """Environ-driven security policy for tests.

    Reads the userid from ``request.environ["test.userid"]``.
    When the key is absent the request is unauthenticated.
    """

    def identity(self, request: Request) -> str | None:
        return request.environ.get("test.userid")

    def authenticated_userid(self, request: Request) -> str | None:
        return request.environ.get("test.userid")

    def permits(self, request: Request, context: object, permission: str) -> bool:
        return True

    def remember(self, request: Request, userid: str, **kw: object) -> list:
        return []

    def forget(self, request: Request, **kw: object) -> list:
        return []


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def build_app(db_engine):
    """App factory. Call with an optional configure callback to customise the app."""

    def _build(configure: Callable[[Configurator], None] | None = None) -> Router:
        config = Configurator(settings={})
        config.registry["dbengine"] = db_engine
        config.include("pyramid_sa")
        config.sa_enable_audit()
        config.set_security_policy(TestSecurityPolicy())
        if configure is not None:
            configure(config)
        return config.make_wsgi_app()

    return _build


@pytest.fixture(scope="session")
def app(build_app):
    """Default WSGI app — override in module conftest for custom configuration."""
    return build_app()


@pytest.fixture()
def tm():
    """Doomed transaction manager — auto-rollback after each test."""
    t = transaction.TransactionManager(explicit=True)
    t.begin()
    t.doom()
    yield t
    t.abort()


@pytest.fixture()
def dbsession(app, tm):
    """Transaction-managed session without a request (audit fields stay None)."""
    session_factory = app.registry["dbsession_factory"]
    return get_tm_session(session_factory, tm)


@pytest.fixture()
def app_request(app, tm, dbsession):
    """Real Pyramid request with the database session wired in."""
    with prepare(registry=app.registry) as env:
        request = env["request"]
        request.host = "example.com"
        request.environ.update(
            {
                "REMOTE_ADDR": "127.0.0.1",
                "tm.active": True,
                "tm.manager": tm,
                "app.dbsession": dbsession,
            }
        )
        request.dbsession = dbsession
        request.tm = tm
        dbsession.info["request"] = request
        yield request


@pytest.fixture()
def authenticated_request(app_request):
    """Real Pyramid request with authentication set for audit listener tests."""
    app_request.environ["test.userid"] = "test-user"
    return app_request


@pytest.fixture()
def testapp(app, tm, dbsession):
    """WebTest TestApp with the test transaction and session injected."""
    return webtest.TestApp(
        app,
        extra_environ={
            "HTTP_HOST": "example.com",
            "tm.active": True,
            "tm.manager": tm,
            "app.dbsession": dbsession,
        },
    )
