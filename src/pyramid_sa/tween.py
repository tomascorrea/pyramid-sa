"""Pyramid tween that translates service-layer exceptions into HTTP errors."""

import logging
from collections.abc import Callable
from typing import Any

from pyramid.httpexceptions import HTTPConflict, HTTPNotFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)

ErrorBodyFormatter = Callable[[Any], dict[str, Any]]

_REGISTRY_KEY_NOT_FOUND = "sa.error_formatter.not_found"
_REGISTRY_KEY_CONFLICT = "sa.error_formatter.conflict"


def default_not_found_body(request: Any) -> dict[str, Any]:
    """Return the default 404 error body."""
    return {"error": "not_found", "message": "Resource not found."}


def default_conflict_body(request: Any) -> dict[str, Any]:
    """Return the default 409 error body."""
    return {
        "error": "conflict",
        "message": "Operation violates a uniqueness constraint.",
    }


def sa_error_formatter(
    config: Any,
    *,
    not_found: ErrorBodyFormatter | None = None,
    conflict: ErrorBodyFormatter | None = None,
) -> None:
    """Configure custom error body formatters for the exception tween.

    Each formatter is a callable that receives the current request and returns
    a dict used as the ``json_body`` of the HTTP error response.

    Usage::

        def my_not_found(request):
            return {"code": "NOT_FOUND", "detail": "Resource not found."}

        config.include("pyramid_sa")
        config.sa_error_formatter(not_found=my_not_found)
    """
    if not_found is not None:
        config.registry[_REGISTRY_KEY_NOT_FOUND] = not_found
    if conflict is not None:
        config.registry[_REGISTRY_KEY_CONFLICT] = conflict


def exception_tween_factory(handler: Any, registry: Any) -> Callable:
    """Catch domain exceptions and return consistent JSON error responses."""
    not_found_formatter: ErrorBodyFormatter = registry.get(
        _REGISTRY_KEY_NOT_FOUND, default_not_found_body
    )
    conflict_formatter: ErrorBodyFormatter = registry.get(
        _REGISTRY_KEY_CONFLICT, default_conflict_body
    )

    def exception_tween(request: Any) -> Any:
        try:
            return handler(request)
        except NoResultFound:
            raise HTTPNotFound(
                json_body=not_found_formatter(request),
            ) from None
        except IntegrityError as exc:
            log.warning("Integrity error: %s", exc.orig)
            raise HTTPConflict(
                json_body=conflict_formatter(request),
            ) from exc

    return exception_tween
