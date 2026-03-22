"""Simulated consuming app for soft-delete integration tests."""

from pyramid.config import Configurator

from tests.conftest import TestSecurityPolicy


def create_app(dbengine=None, **settings):
    """App with audit AND soft delete enabled."""
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    config.sa_enable_audit()
    config.sa_enable_soft_delete()
    config.set_security_policy(TestSecurityPolicy())
    config.sa_scan_models("tests.soft_delete.app.models")
    return config.make_wsgi_app()


def create_app_no_soft_delete(dbengine=None, **settings):
    """App with audit only — soft delete NOT enabled."""
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    config.sa_enable_audit()
    config.set_security_policy(TestSecurityPolicy())
    config.sa_scan_models("tests.soft_delete.app.models")
    return config.make_wsgi_app()
