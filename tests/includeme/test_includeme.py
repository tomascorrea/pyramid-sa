"""Tests for pyramid_sa.includeme — Pyramid integration."""

import datetime

import pytest
import webtest
from pyramid.config import Configurator
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound

from pyramid_sa import Base


def test_registers_dbsession_factory():
    """Verify includeme registers a dbsession_factory in the registry."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")
    config.commit()

    assert "dbsession_factory" in config.registry


def test_uses_pre_set_dbengine():
    """Verify includeme reuses an engine already set in the registry."""
    engine = create_engine("sqlite://")
    config = Configurator(settings={})
    config.registry["dbengine"] = engine
    config.include("pyramid_sa")
    config.commit()

    factory = config.registry["dbsession_factory"]
    assert factory.kw["bind"] is engine


def test_request_dbsession_via_webtest():
    """Verify requests have a dbsession attribute after includeme."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    config = Configurator(settings={})
    config.registry["dbengine"] = engine
    config.include("pyramid_sa")
    config.add_route("check", "/check")
    config.add_view(
        lambda request: {"has_dbsession": hasattr(request, "dbsession")},
        route_name="check",
        renderer="json",
    )
    app = config.make_wsgi_app()
    testapp = webtest.TestApp(app)

    response = testapp.get("/check")
    assert response.json["has_dbsession"] is True


def test_exception_tween_returns_404_for_not_found():
    """Verify the exception tween maps NoResultFound to a 404 response."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")
    config.add_route("fail", "/fail")

    def failing_view(request):
        raise NoResultFound()

    config.add_view(failing_view, route_name="fail", renderer="json")
    app = config.make_wsgi_app()
    testapp = webtest.TestApp(app)

    response = testapp.get("/fail", expect_errors=True)
    assert response.status_int == 404
    assert response.json["error"] == "not_found"


def test_json_renderer_handles_datetime():
    """Verify the JSON renderer serializes datetime to ISO-8601."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")
    config.add_route("time", "/time")
    config.add_view(
        lambda request: {"ts": datetime.datetime(2026, 3, 21, 12, 0, 0)},
        route_name="time",
        renderer="json",
    )
    app = config.make_wsgi_app()
    testapp = webtest.TestApp(app)

    response = testapp.get("/time")
    assert response.json["ts"] == "2026-03-21T12:00:00"


def test_sa_scan_models_registers_directive():
    """Verify includeme registers the sa_scan_models directive."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")

    assert hasattr(config, "sa_scan_models")


def test_sa_scan_models_imports_module():
    """Verify sa_scan_models imports the given module and registers its tables."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")
    config.sa_scan_models("tests.cli.app.models")

    assert "books" in Base.metadata.tables


def test_sa_scan_models_accepts_multiple_paths():
    """Verify sa_scan_models accepts multiple dotted module paths."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")
    config.sa_scan_models("tests.cli.app.models", "tests.conftest")

    assert "books" in Base.metadata.tables
    assert "items" in Base.metadata.tables


def test_sa_scan_models_raises_on_no_args():
    """Verify sa_scan_models raises ValueError when called without arguments."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")

    with pytest.raises(ValueError, match="at least one module path"):
        config.sa_scan_models()


def test_sa_scan_models_raises_on_bad_module():
    """Verify sa_scan_models raises ModuleNotFoundError for nonexistent modules."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")

    with pytest.raises(ModuleNotFoundError):
        config.sa_scan_models("nonexistent.module")
