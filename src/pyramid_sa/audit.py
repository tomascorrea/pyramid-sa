"""Audit event listeners and Pyramid directive for automatic audit fields."""

from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapper

from pyramid_sa.meta import AuditMixin


def _set_created_audit_fields(mapper: Mapper, connection, target) -> None:
    if not isinstance(target, AuditMixin):
        return
    session = inspect(target).session
    if session and (request := session.info.get("request")):
        target.created_by = (
            str(request.authenticated_userid)[:40]
            if request.authenticated_userid
            else None
        )
        target.created_ip = request.client_addr


def _set_updated_audit_fields(mapper: Mapper, connection, target) -> None:
    if not isinstance(target, AuditMixin):
        return
    session = inspect(target).session
    if session and (request := session.info.get("request")):
        target.updated_by = (
            str(request.authenticated_userid)[:40]
            if request.authenticated_userid
            else None
        )
        target.updated_ip = request.client_addr


def sa_enable_audit(config) -> None:
    """Activate automatic audit field population.

    Registers ``before_insert`` and ``before_update`` event listeners that
    set ``created_by`` / ``created_ip`` and ``updated_by`` / ``updated_ip``
    from the current request.

    Usage::

        config.include("pyramid_sa")
        config.sa_enable_audit()
    """
    if not event.contains(Mapper, "before_insert", _set_created_audit_fields):
        event.listen(Mapper, "before_insert", _set_created_audit_fields)
    if not event.contains(Mapper, "before_update", _set_updated_audit_fields):
        event.listen(Mapper, "before_update", _set_updated_audit_fields)
