"""Simulated consuming app for CLI integration tests."""

from pyramid.config import Configurator


def create_app(dbengine=None, **settings):
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    config.sa_enable_audit()
    config.sa_scan_models("tests.cli.app.models")
    return config.make_wsgi_app()
