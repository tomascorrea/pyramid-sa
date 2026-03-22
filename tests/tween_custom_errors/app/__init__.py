"""Simulated consuming app with custom error formatters."""

from pyramid.config import Configurator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


def custom_not_found_body(request):
    return {"code": "NOT_FOUND", "detail": "Nothing here."}


def custom_conflict_body(request):
    return {"code": "CONFLICT", "detail": "Duplicate entry."}


def _view_not_found(request):
    raise NoResultFound()


def _view_conflict(request):
    raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))


def create_app(dbengine=None, **settings):
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")
    config.sa_error_formatter(
        not_found=custom_not_found_body,
        conflict=custom_conflict_body,
    )

    config.add_route("not_found", "/not-found")
    config.add_view(_view_not_found, route_name="not_found", renderer="json")

    config.add_route("conflict", "/conflict")
    config.add_view(_view_conflict, route_name="conflict", renderer="json")

    return config.make_wsgi_app()
