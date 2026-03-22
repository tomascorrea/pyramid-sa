"""Tests for the exception tween with custom error formatters."""

import webtest


def test_not_found_uses_custom_formatter(app):
    """Verify NoResultFound uses the app-configured custom body."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/not-found", expect_errors=True)

    assert response.status_int == 404
    assert response.json == {
        "code": "NOT_FOUND",
        "detail": "Nothing here.",
    }


def test_conflict_uses_custom_formatter(app):
    """Verify IntegrityError uses the app-configured custom body."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/conflict", expect_errors=True)

    assert response.status_int == 409
    assert response.json == {
        "code": "CONFLICT",
        "detail": "Duplicate entry.",
    }
