"""Tests for the exception tween with default error formatters."""

import pytest
import webtest


def test_not_found_returns_404_with_default_body(app):
    """Verify NoResultFound maps to 404 with the default error body."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/not-found", expect_errors=True)

    assert response.status_int == 404
    assert response.json == {
        "error": "not_found",
        "message": "Resource not found.",
    }


def test_integrity_error_returns_409_with_default_body(app):
    """Verify IntegrityError maps to 409 with the default error body."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/conflict", expect_errors=True)

    assert response.status_int == 409
    assert response.json == {
        "error": "conflict",
        "message": "Operation violates a uniqueness constraint.",
    }


def test_normal_response_passes_through(app):
    """Verify a normal response is returned unchanged."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/ok")

    assert response.status_int == 200
    assert response.json == {"status": "ok"}


def test_other_exceptions_propagate(app):
    """Verify unhandled exceptions are not caught by the tween."""
    testapp = webtest.TestApp(app)

    with pytest.raises(ValueError, match="unrelated"):
        testapp.get("/value-error")
