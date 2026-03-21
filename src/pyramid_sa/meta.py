"""SQLAlchemy declarative base, audit mixin, and event listeners."""

import uuid
from datetime import UTC, datetime

from camel_converter import dict_to_camel
from sqlalchemy import DateTime, MetaData, String, event, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, Mapper, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _now() -> datetime:
    return datetime.now(UTC)


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


class AuditMixin:
    """Audit columns and utility methods inherited by all models."""

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=_now,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        onupdate=_now,
    )
    created_ip: Mapped[str | None] = mapped_column(String(40))
    updated_ip: Mapped[str | None] = mapped_column(String(40))
    created_by: Mapped[str | None] = mapped_column(String(40))
    updated_by: Mapped[str | None] = mapped_column(String(40))

    def as_dict(
        self,
        hide_internal_fields: bool = True,
        convert_to_camel: bool = True,
        exclude: list[str] | None = None,
    ) -> dict:
        exclude = exclude or []
        ret = {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
            if c.key not in exclude
        }
        if hide_internal_fields:
            ret.pop("id", None)
            if "uuid" in ret:
                ret["id"] = ret.pop("uuid")
        if convert_to_camel:
            ret = dict_to_camel(ret)
        return ret

    def copy_with(self, **kwargs) -> "AuditMixin":
        excluded = {"id", "uuid", "created_at", "updated_at"}
        mapper_obj = inspect(self.__class__)
        data = {
            col.key: kwargs.get(col.key, getattr(self, col.key))
            for col in mapper_obj.column_attrs
            if col.key not in excluded
        }
        return self.__class__(**data)


class Base(AuditMixin, DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@event.listens_for(Mapper, "before_insert")
def _set_created_audit_fields(mapper, connection, target):
    session = inspect(target).session
    if session and (request := session.info.get("request")):
        target.created_by = (
            str(request.authenticated_userid)[:40]
            if request.authenticated_userid
            else None
        )
        target.created_ip = request.client_addr


@event.listens_for(Mapper, "before_update")
def _set_updated_audit_fields(mapper, connection, target):
    session = inspect(target).session
    if session and (request := session.info.get("request")):
        target.updated_by = (
            str(request.authenticated_userid)[:40]
            if request.authenticated_userid
            else None
        )
        target.updated_ip = request.client_addr
