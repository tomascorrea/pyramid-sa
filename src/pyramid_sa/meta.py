"""SQLAlchemy declarative base and utility helpers."""

import uuid
from datetime import UTC, datetime

from camel_converter import dict_to_camel
from sqlalchemy import MetaData, inspect
from sqlalchemy.orm import DeclarativeBase

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


class ORMClass:
    """Utility methods available on every model via Base."""

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

    def copy_with(self, **kwargs):
        excluded = {"id", "uuid", "created_at", "updated_at"}
        mapper_obj = inspect(self.__class__)
        data = {
            col.key: kwargs.get(col.key, getattr(self, col.key))
            for col in mapper_obj.column_attrs
            if col.key not in excluded
        }
        return self.__class__(**data)


class Base(ORMClass, DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
