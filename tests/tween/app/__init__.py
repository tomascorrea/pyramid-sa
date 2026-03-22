"""Simulated consuming app with default error formatters."""

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPOk
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


def _view_not_found(request):
    raise NoResultFound()


def _view_conflict(request):
    raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))


def _view_ok(request):
    return HTTPOk(json_body={"status": "ok"})


def _view_value_error(request):
    raise ValueError("unrelated")


def create_app(dbengine=None, **settings):
    config = Configurator(settings=settings)
    if dbengine is not None:
        config.registry["dbengine"] = dbengine
    config.include("pyramid_sa")

    config.add_route("not_found", "/not-found")
    config.add_view(_view_not_found, route_name="not_found", renderer="json")

    config.add_route("conflict", "/conflict")
    config.add_view(_view_conflict, route_name="conflict", renderer="json")

    config.add_route("ok", "/ok")
    config.add_view(_view_ok, route_name="ok")

    config.add_route("value_error", "/value-error")
    config.add_view(_view_value_error, route_name="value_error", renderer="json")

    return config.make_wsgi_app()
