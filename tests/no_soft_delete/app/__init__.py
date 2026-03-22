"""Simulated consuming app WITHOUT soft delete — audit only."""

from pyramid.config import Configurator
from tests.conftest import TestSecurityPolicy


def create_app(dbengine=None, **settings):
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    config.sa_enable_audit()
    config.set_security_policy(TestSecurityPolicy())
    config.sa_scan_models("tests.no_soft_delete.app.models")
    return config.make_wsgi_app()
