"""Tests for pyramid_sa_testing — pytest plugin fixtures."""

from __future__ import annotations

import uuid  # noqa: TCH003 — needed at runtime for SQLAlchemy mapped annotations

import pytest
from pyramid.config import Configurator
from sqlalchemy import String, create_engine
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, generate_uuid


class Widget(Base):
    """Test-only model for verifying plugin fixtures."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    label: Mapped[str] = mapped_column(String(100))


@pytest.fixture(scope="session")
def pyramid_sa_engine():
    """Override the plugin's default engine for these tests."""
    engine = create_engine("sqlite://")
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def app(pyramid_sa_engine):
    """Minimal Pyramid app for testing the plugin fixtures."""
    config = Configurator(settings={})
    config.registry["dbengine"] = pyramid_sa_engine
    config.include("pyramid_sa")

    config.add_route("health", "/health")
    config.add_view(
        lambda request: {"status": "ok"}, route_name="health", renderer="json"
    )

    wsgi_app = config.make_wsgi_app()
    Base.metadata.create_all(pyramid_sa_engine)
    return wsgi_app


class TestPluginFixtures:
    def test_tm_is_doomed(self, pyramid_sa_tm):
        assert pyramid_sa_tm.isDoomed()

    def test_dbsession_works(self, pyramid_sa_dbsession):
        widget = Widget(label="test-widget")
        pyramid_sa_dbsession.add(widget)
        pyramid_sa_dbsession.flush()

        assert widget.id is not None
        assert widget.label == "test-widget"

    def test_testapp_makes_requests(self, pyramid_sa_testapp):
        response = pyramid_sa_testapp.get("/health", status=200)
        assert response.json["status"] == "ok"

    def test_app_request_has_dbsession(self, pyramid_sa_app_request):
        assert pyramid_sa_app_request.dbsession is not None

    def test_dbsession_rolls_back_between_tests(self, pyramid_sa_dbsession):
        """This test runs after test_dbsession_works — the widget should not exist."""
        count = pyramid_sa_dbsession.query(Widget).count()
        assert count == 0
