"""Simulated consuming app with custom error formatters."""

from pyramid.config import Configurator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


def custom_not_found_body(request, exc=None, **kwargs):
    return {
        "code": "NOT_FOUND",
        "detail": "Nothing here.",
        "has_exc": exc is not None,
    }


def custom_conflict_body(request, exc=None, **kwargs):
    return {
        "code": "CONFLICT",
        "detail": str(exc.orig) if exc else "Duplicate entry.",
        "has_exc": exc is not None,
    }


def _view_not_found(request):
    raise NoResultFound()


def _view_conflict(request):
    raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))


def create_app(dbengine=None, **settings):
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    config.sa_json_renderer()
    config.sa_error_formatter(
        not_found=custom_not_found_body,
        conflict=custom_conflict_body,
    )

    config.add_route("not_found", "/not-found")
    config.add_view(_view_not_found, route_name="not_found", renderer="json")

    config.add_route("conflict", "/conflict")
    config.add_view(_view_conflict, route_name="conflict", renderer="json")

    return config.make_wsgi_app()
