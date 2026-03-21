"""Fixtures for pyramid_sa_testing plugin tests."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def app(build_app):
    """WSGI app with a health endpoint for testing the plugin fixtures."""

    def configure(config):
        config.add_route("health", "/health")
        config.add_view(
            lambda request: {"status": "ok"}, route_name="health", renderer="json"
        )

    return build_app(configure=configure)
