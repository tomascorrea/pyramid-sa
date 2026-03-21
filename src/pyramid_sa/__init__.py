"""Pyramid SQLAlchemy Integration."""

from pyramid_sa.meta import Base, generate_uuid
from pyramid_sa.renderer import configure_json_renderer
from pyramid_sa.session import get_engine, get_session_factory, get_tm_session

__all__ = [
    "Base",
    "generate_uuid",
    "get_engine",
    "get_session_factory",
    "get_tm_session",
]


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
