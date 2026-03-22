"""SQLAlchemy declarative base, audit mixin, and utility helpers."""

import uuid
from datetime import UTC, datetime

from camel_converter import dict_to_camel
from sqlalchemy import DateTime, MetaData, String, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
