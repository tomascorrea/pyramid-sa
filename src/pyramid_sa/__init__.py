"""Pyramid SQLAlchemy Integration."""

import importlib
from types import ModuleType

from sqlalchemy.orm import configure_mappers

from pyramid_sa.meta import Base
from pyramid_sa.models import (
    AuditMixin,
    Model,
    RestoreConflictError,
    SoftDeleteMixin,
    SoftDeleteSession,
    SoftDeleteUniqueIndex,
    sa_enable_audit,
    sa_enable_soft_delete,
    soft_delete_mapped_column,
)
from pyramid_sa.renderer import configure_json_renderer
from pyramid_sa.session import get_engine, get_session_factory, get_tm_session
from pyramid_sa.tween import (
    default_conflict_body,
    default_not_found_body,
    sa_error_formatter,
)
from pyramid_sa.utils import generate_uuid

__all__ = [
    "AuditMixin",
    "Base",
    "Model",
    "RestoreConflictError",
    "SoftDeleteMixin",
    "SoftDeleteSession",
    "SoftDeleteUniqueIndex",
    "configure_json_renderer",
    "default_conflict_body",
    "default_not_found_body",
    "generate_uuid",
    "get_engine",
    "get_session_factory",
    "get_tm_session",
    "sa_enable_audit",
    "sa_enable_soft_delete",
    "sa_error_formatter",
    "soft_delete_mapped_column",
]


def _scan_models_directive(config: object, *module_paths: str | ModuleType) -> None:
    """Import model modules and configure SQLAlchemy mappers.

    Accepts one or more dotted Python module paths or already-imported module
    objects.  Each string path is imported (which registers its models with
    ``Base``); module objects are accepted as-is.  Then ``configure_mappers()``
    is called once so that all relationships are resolved.

    Usage::

        config.include("pyramid_sa")
        config.sa_scan_models("myapp.models")

        import myapp.models
        config.sa_scan_models(myapp.models)
    """
    if not module_paths:
        raise ValueError("sa_scan_models requires at least one module path")
    for path in module_paths:
        if not isinstance(path, ModuleType):
            importlib.import_module(path)
    configure_mappers()


def _add_request_to_session_tween_factory(handler, registry):
    """Ensure ``request.dbsession.info["request"]`` is always set.

    Without this tween, sessions injected via ``request.environ["app.dbsession"]``
    (the standard test path) would lack the request reference, causing audit
    listeners to silently skip field population.
    """

    def tween(request):
        request.dbsession.info["request"] = request
        return handler(request)

    return tween


def includeme(config):
    """Wire SQLAlchemy into a Pyramid application.

    Activate with ``config.include("pyramid_sa")``.
    """
    settings = config.get_settings()
    config.include("pyramid_tm")
    config.include("pyramid_retry")

    engine = config.registry.get("dbengine") or settings.get("dbengine")
    if engine is None:
        engine = get_engine(settings)

    session_factory = get_session_factory(engine)
    config.registry["dbsession_factory"] = session_factory

    def dbsession(request):
        if "app.dbsession" in request.environ:
            return request.environ["app.dbsession"]
        return get_tm_session(session_factory, request.tm, request=request)

    config.add_request_method(dbsession, "dbsession", reify=True)

    config.add_tween(
        "pyramid_sa.tween.exception_tween_factory",
        under="pyramid.tweens.excview_tween_factory",
    )
    config.add_tween(
        "pyramid_sa._add_request_to_session_tween_factory",
        under="pyramid_sa.tween.exception_tween_factory",
    )

    config.add_directive("sa_json_renderer", configure_json_renderer)
    config.add_directive("sa_scan_models", _scan_models_directive)
    config.add_directive("sa_enable_audit", sa_enable_audit)
    config.add_directive("sa_enable_soft_delete", sa_enable_soft_delete)
    config.add_directive("sa_error_formatter", sa_error_formatter)
