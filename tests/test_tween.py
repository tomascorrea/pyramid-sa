"""Tests for pyramid_sa.tween — exception-to-HTTP mapping."""

import pytest
from pyramid import testing as pyramid_testing
from pyramid.httpexceptions import HTTPConflict, HTTPNotFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from pyramid_sa.tween import exception_tween_factory


def test_no_result_found_returns_404():
    """Verify NoResultFound is mapped to a 404 HTTPNotFound."""

    def handler(request):
        raise NoResultFound()

    tween = exception_tween_factory(handler, None)
    request = pyramid_testing.DummyRequest()

    with pytest.raises(HTTPNotFound) as exc_info:
        tween(request)

    assert exc_info.value.json_body["error"] == "not_found"


def test_integrity_error_returns_409():
    """Verify IntegrityError is mapped to a 409 HTTPConflict."""

    def handler(request):
        raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))

    tween = exception_tween_factory(handler, None)
    request = pyramid_testing.DummyRequest()

    with pytest.raises(HTTPConflict) as exc_info:
        tween(request)

    assert exc_info.value.json_body["error"] == "conflict"


def test_normal_response_passes_through():
    """Verify a normal response is returned unchanged."""

    def handler(request):
        return {"status": "ok"}

    tween = exception_tween_factory(handler, None)
    request = pyramid_testing.DummyRequest()

    result = tween(request)
    assert result == {"status": "ok"}


def test_other_exceptions_propagate():
    """Verify unhandled exceptions propagate without being caught."""

    def handler(request):
        raise ValueError("unrelated")

    tween = exception_tween_factory(handler, None)
    request = pyramid_testing.DummyRequest()

    with pytest.raises(ValueError, match="unrelated"):
        tween(request)
