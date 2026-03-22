"""Tests for partial error formatter override — only not_found is customised."""

import webtest


def test_not_found_uses_custom_formatter(app):
    """Verify not_found uses the overridden formatter."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/not-found", expect_errors=True)

    assert response.status_int == 404
    assert response.json == {
        "code": "NOT_FOUND",
        "detail": "Custom 404.",
    }


def test_conflict_uses_default_formatter(app):
    """Verify conflict still uses the default formatter when not overridden."""
    testapp = webtest.TestApp(app)
    response = testapp.get("/conflict", expect_errors=True)

    assert response.status_int == 409
    assert response.json == {
        "error": "conflict",
        "message": "Operation violates a uniqueness constraint.",
    }
