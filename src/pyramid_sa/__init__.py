"""Pyramid SQLAlchemy Integration."""

import importlib

from sqlalchemy.orm import configure_mappers

from pyramid_sa.audit import AuditMixin, sa_enable_audit
from pyramid_sa.meta import Base, generate_uuid
from pyramid_sa.renderer import configure_json_renderer
from pyramid_sa.session import get_engine, get_session_factory, get_tm_session
from pyramid_sa.soft_delete import (
    RestoreConflictError,
    SoftDeleteMixin,
    SoftDeleteSession,
    SoftDeleteUniqueIndex,
    sa_enable_soft_delete,
    soft_delete_mapped_column,
)
from pyramid_sa.tween import (
    default_conflict_body,
    default_not_found_body,
    sa_error_formatter,
)


class Model(AuditMixin, SoftDeleteMixin, Base):
    """Auditable, soft-deletable base class — the common case.

    Use instead of ``Base`` when the model needs both audit columns and
    soft-delete support::

        class Article(Model):
            __tablename__ = "articles"
            ...
    """

    __abstract__ = True


__all__ = [
    "AuditMixin",
    "Base",
    "Model",
    "RestoreConflictError",
    "SoftDeleteMixin",
    "SoftDeleteSession",
    "SoftDeleteUniqueIndex",
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


def _scan_models_directive(config: object, *module_paths: str) -> None:
    """Import model modules and configure SQLAlchemy mappers.

    Accepts one or more dotted Python module paths.  Each module is imported
    (which registers its models with ``Base``), then ``configure_mappers()``
    is called once so that all relationships are resolved.

    Usage::

        config.include("pyramid_sa")
        config.sa_scan_models("myapp.models")
    """
    if not module_paths:
        raise ValueError("sa_scan_models requires at least one module path")
    for path in module_paths:
        importlib.import_module(path)
    configure_mappers()


def includeme(config):
    """Wire SQLAlchemy into a Pyramid application.

    Activate with ``config.include("pyramid_sa")``.
    """
    settings = config.get_settings()
    config.include("pyramid_tm")

    engine = config.registry.get("dbengine")
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

    configure_json_renderer(config)

    config.add_directive("sa_scan_models", _scan_models_directive)
    config.add_directive("sa_enable_audit", sa_enable_audit)
    config.add_directive("sa_enable_soft_delete", sa_enable_soft_delete)
    config.add_directive("sa_error_formatter", sa_error_formatter)
