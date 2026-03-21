"""Pyramid tween that translates service-layer exceptions into HTTP errors."""

import logging

from pyramid.httpexceptions import HTTPConflict, HTTPNotFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)


def exception_tween_factory(handler, registry):
    """Catch domain exceptions and return consistent JSON error responses."""

    def exception_tween(request):
        try:
            return handler(request)
        except NoResultFound:
            raise HTTPNotFound(
                json_body={"error": "not_found", "message": "Resource not found."}
            ) from None
        except IntegrityError as exc:
            log.warning("Integrity error: %s", exc.orig)
            raise HTTPConflict(
                json_body={
                    "error": "conflict",
                    "message": "Operation violates a uniqueness constraint.",
                }
            ) from exc

    return exception_tween
