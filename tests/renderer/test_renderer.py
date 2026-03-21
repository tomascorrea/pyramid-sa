"""Tests for pyramid_sa.renderer — JSON adapters."""

from __future__ import annotations

import datetime
from uuid import uuid4


def test_datetime_serialized_as_iso(renderer_app, make_testapp):
    """Verify datetime objects are serialized to ISO-8601 strings."""
    renderer_app.add_route("dt", "/dt")
    renderer_app.add_view(
        lambda r: {"ts": datetime.datetime(2026, 3, 21, 12, 0, 0)},
        route_name="dt",
        renderer="json",
    )
    testapp = make_testapp(renderer_app)

    response = testapp.get("/dt")
    assert response.json["ts"] == "2026-03-21T12:00:00"


def test_date_serialized_as_iso(renderer_app, make_testapp):
    """Verify date objects are serialized to ISO-8601 strings."""
    renderer_app.add_route("d", "/d")
    renderer_app.add_view(
        lambda r: {"date": datetime.date(2026, 3, 21)},
        route_name="d",
        renderer="json",
    )
    testapp = make_testapp(renderer_app)

    response = testapp.get("/d")
    assert response.json["date"] == "2026-03-21"


def test_uuid_serialized_as_string(renderer_app, make_testapp):
    """Verify UUID objects are serialized to their string representation."""
    u = uuid4()
    renderer_app.add_route("u", "/u")
    renderer_app.add_view(
        lambda r: {"id": u},
        route_name="u",
        renderer="json",
    )
    testapp = make_testapp(renderer_app)

    response = testapp.get("/u")
    assert response.json["id"] == str(u)
