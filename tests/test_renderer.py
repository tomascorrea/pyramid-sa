"""Tests for pyramid_sa.renderer — JSON adapters."""

import datetime
from uuid import uuid4

import webtest
from pyramid.config import Configurator


class TestJsonRenderer:
    def test_datetime_serialized_as_iso(self):
        config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
        config.include("pyramid_sa")
        config.add_route("dt", "/dt")
        config.add_view(
            lambda r: {"ts": datetime.datetime(2026, 3, 21, 12, 0, 0)},
            route_name="dt",
            renderer="json",
        )
        app = config.make_wsgi_app()
        testapp = webtest.TestApp(app)

        response = testapp.get("/dt")
        assert response.json["ts"] == "2026-03-21T12:00:00"

    def test_date_serialized_as_iso(self):
        config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
        config.include("pyramid_sa")
        config.add_route("d", "/d")
        config.add_view(
            lambda r: {"date": datetime.date(2026, 3, 21)},
            route_name="d",
            renderer="json",
        )
        app = config.make_wsgi_app()
        testapp = webtest.TestApp(app)

        response = testapp.get("/d")
        assert response.json["date"] == "2026-03-21"

    def test_uuid_serialized_as_string(self):
        u = uuid4()
        config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
        config.include("pyramid_sa")
        config.add_route("u", "/u")
        config.add_view(
            lambda r: {"id": u},
            route_name="u",
            renderer="json",
        )
        app = config.make_wsgi_app()
        testapp = webtest.TestApp(app)

        response = testapp.get("/u")
        assert response.json["id"] == str(u)
