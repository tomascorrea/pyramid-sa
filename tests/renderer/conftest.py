"""Fixtures for renderer tests."""

from __future__ import annotations

import pytest
import webtest
from pyramid.config import Configurator


@pytest.fixture()
def renderer_app():
    """Pyramid Configurator with pyramid_sa included, ready for route registration."""
    config = Configurator(settings={"sqlalchemy.url": "sqlite://"})
    config.include("pyramid_sa")
    return config


@pytest.fixture()
def make_testapp():
    """Factory that builds a WebTest TestApp from a Configurator."""

    def _make(config: Configurator) -> webtest.TestApp:
        return webtest.TestApp(config.make_wsgi_app())

    return _make
