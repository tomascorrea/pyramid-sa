"""Simulated consuming app for CLI integration tests."""

from pyramid.config import Configurator
from sqlalchemy.orm import configure_mappers

import tests.cli.app.models  # noqa: F401


def create_app(dbengine=None, **settings):
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    configure_mappers()
    return config.make_wsgi_app()
