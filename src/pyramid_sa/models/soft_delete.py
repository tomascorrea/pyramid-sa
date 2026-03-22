"""Soft delete mixin, session subclass, and Pyramid directive."""

import logging
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    String,
    UniqueConstraint,
    and_,
    event,
    inspect,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    MappedColumn,
    Mapper,
    Session,
    mapped_column,
    with_loader_criteria,
)

from pyramid_sa.meta import Base
from pyramid_sa.utils import _now

logger = logging.getLogger(__name__)

_HARD_DELETE_FLAG = "_pyramid_sa_hard_delete"
_ACTIVE_INDEX_SUFFIX = "_active"

_soft_delete_models: set[type] = set()


class SoftDeleteUniqueIndex(Index):
    """Partial unique index that only constrains active (non-deleted) rows.

    Place in ``__table_args__`` on any ``SoftDeleteMixin`` model to create
    a unique index with ``WHERE deleted_at IS NULL``.  Soft-deleted rows
    are excluded, allowing reuse of unique values::

        class ScopedArticle(Model):
            __tablename__ = "scoped_articles"
            tenant_id: Mapped[str] = mapped_column(String(40))
            slug: Mapped[str] = mapped_column(String(255))

            __table_args__ = (SoftDeleteUniqueIndex("tenant_id", "slug"),)

    For single-column uniqueness at the column level, use
    ``soft_delete_mapped_column(unique=True)`` instead.
    """

    _is_soft_delete_index = True

    def __init__(self, *columns: str, name: str | None = None) -> None:
        self._sd_column_names = columns
        self._sd_custom_name = name
        super().__init__(name, *columns, unique=True)

    def _set_parent(self, parent, **kwargs):
        super()._set_parent(parent, **kwargs)
        if "deleted_at" not in parent.c:
            raise TypeError(
                f"SoftDeleteUniqueIndex requires SoftDeleteMixin. "
                f"Table '{parent.name}' has no 'deleted_at' column."
            )


def soft_delete_mapped_column(*args, unique: bool = False, **kwargs) -> MappedColumn:
    """Like ``mapped_column`` but ``unique=True`` creates a soft-delete-aware index.

    When *unique* is ``True``, the column gets a partial unique index
    (``WHERE deleted_at IS NULL``) instead of a plain ``UniqueConstraint``.
    Soft-deleted rows won't block reuse of the column's value::

        class Article(Model):
            slug: Mapped[str] = soft_delete_mapped_column(String(255), unique=True)
            uuid: Mapped[str] = mapped_column(unique=True)  # stays globally unique

    The partial index is created during mapper configuration
    (``after_configured``).  The model must include ``SoftDeleteMixin``.
    """
    info = dict(kwargs.pop("info", None) or {})
    if unique:
        info["soft_delete_unique"] = True
    return mapped_column(*args, unique=False, info=info, **kwargs)


class RestoreConflictError(Exception):
    """Raised when restoring a soft-deleted row would violate a unique constraint.

    Attributes:
        instance: The model instance that cannot be restored.
        conflicts: Column groups that conflict, e.g. ``[("slug",)]`` or
            ``[("tenant_id", "code")]`` for a multi-column unique.
    """

    def __init__(self, instance: object, conflicts: list[tuple[str, ...]]) -> None:
        self.instance = instance
        self.conflicts = conflicts
        model_name = type(instance).__name__
        col_desc = ", ".join(
            "(" + ", ".join(cols) + ")" if len(cols) > 1 else cols[0]
            for cols in conflicts
        )
        super().__init__(
            f"Cannot restore {model_name}: "
            f"unique conflict on {col_desc} with active rows."
        )


class SoftDeleteMixin:
    """Columns and instance methods for soft-deletable models.

    Add this mixin to individual models, or create an abstract base that
    includes it for all models.  The columns are always present; the
    *behavior* (query filtering, delete interception, index transformation)
    is activated by ``config.sa_enable_soft_delete()``.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_by: Mapped[str | None] = mapped_column(String(40))
    deleted_ip: Mapped[str | None] = mapped_column(String(40))

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this instance as soft-deleted and populate audit fields."""
        self.deleted_at = _now()
        session = inspect(self).session
        if session and (request := session.info.get("request")):
            self.deleted_by = (
                str(request.authenticated_userid)[:40]
                if request.authenticated_userid
                else None
            )
            self.deleted_ip = request.client_addr

    def can_restore(self) -> list[tuple[str, ...]]:
        """Check whether restoring would conflict with active unique values.

        Returns a list of conflicting column groups.  An empty list means
        restore is safe.  Each element is a tuple of column names that form
        a unique constraint, e.g. ``("slug",)`` or ``("tenant_id", "code")``.

        Raises ``RuntimeError`` if the instance is not attached to a session.
        """
        session = inspect(self).session
        if session is None:
            raise RuntimeError(
                f"Cannot check restore conflicts: "
                f"{type(self).__name__} is not attached to a session."
            )

        table = type(self).__table__
        conflicts: list[tuple[str, ...]] = []

        for idx in table.indexes:
            if not idx.unique or not idx.name:
                continue
            if not idx.name.endswith(_ACTIVE_INDEX_SUFFIX):
                continue

            col_names = tuple(c.name for c in idx.columns)
            conditions = [table.c.deleted_at.is_(None)]
            for col_name in col_names:
                conditions.append(table.c[col_name] == getattr(self, col_name))

            stmt = (
                select(table.c[col_names[0]])
                .where(and_(*conditions))
                .limit(1)
                .execution_options(include_deleted=True)
            )
            if session.execute(stmt).first() is not None:
                conflicts.append(col_names)

        return conflicts

    def restore(self) -> None:
        """Un-delete this instance.

        Raises ``RestoreConflictError`` if restoring would violate a unique
        constraint with an existing active row.
        """
        conflicts = self.can_restore()
        if conflicts:
            raise RestoreConflictError(self, conflicts)
        self.deleted_at = None
        self.deleted_by = None
        self.deleted_ip = None


class SoftDeleteSession(Session):
    """Session subclass that adds ``hard_delete()``."""

    def hard_delete(self, instance) -> None:
        """Perform a real SQL DELETE, bypassing soft-delete interception."""
        object.__setattr__(instance, _HARD_DELETE_FLAG, True)
        super().delete(instance)


# ---------------------------------------------------------------------------
# Event listeners (registered by sa_enable_soft_delete)
# ---------------------------------------------------------------------------


def _convert_deletes_to_soft_deletes(session, flush_context, instances) -> None:
    """``before_flush`` handler: turn ``session.delete()`` into a soft delete."""
    for obj in list(session.deleted):
        if not isinstance(obj, SoftDeleteMixin):
            continue
        if getattr(obj, _HARD_DELETE_FLAG, False):
            object.__setattr__(obj, _HARD_DELETE_FLAG, False)
            continue
        # Undo the pending delete and convert to an update
        session.add(obj)
        obj.deleted_at = _now()
        sa_session = inspect(obj).session
        if sa_session and (request := sa_session.info.get("request")):
            obj.deleted_by = (
                str(request.authenticated_userid)[:40]
                if request.authenticated_userid
                else None
            )
            obj.deleted_ip = request.client_addr


def _soft_delete_query_filter(execute_state) -> None:
    """``do_orm_execute`` handler: exclude soft-deleted rows from SELECTs."""
    if not execute_state.is_select:
        return
    if execute_state.execution_options.get("include_deleted", False):
        return
    for model in _soft_delete_models:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                model,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )


def _discover_soft_delete_models() -> None:
    """``after_configured`` handler: discover models and process soft-delete indexes."""
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if not isinstance(cls, type) or not issubclass(cls, SoftDeleteMixin):
            continue
        if cls is SoftDeleteMixin:
            continue
        _soft_delete_models.add(cls)
        _finalize_soft_delete_indexes(cls)
        _process_soft_delete_columns(cls)
        _warn_plain_unique_constraints(cls)


def _finalize_soft_delete_indexes(model: type) -> None:
    """Replace ``SoftDeleteUniqueIndex`` markers with configured partial indexes."""
    table = model.__table__
    deleted_at_col = table.c.deleted_at

    markers: list[tuple[Index, str, list]] = []

    for idx in list(table.indexes):
        if not getattr(idx, "_is_soft_delete_index", False):
            continue

        if idx._sd_custom_name:
            name = idx._sd_custom_name
        else:
            col_names = "_".join(c.name for c in idx.columns)
            name = f"uq_{table.name}_{col_names}{_ACTIVE_INDEX_SUFFIX}"

        markers.append((idx, name, list(idx.columns)))

    for marker, name, columns in markers:
        table.indexes.discard(marker)

        if any(existing.name == name for existing in table.indexes):
            continue

        Index(
            name,
            *columns,
            unique=True,
            postgresql_where=deleted_at_col.is_(None),
            sqlite_where=deleted_at_col.is_(None),
        )


def _process_soft_delete_columns(model: type) -> None:
    """Create partial unique indexes for ``soft_delete_mapped_column`` columns."""
    table = model.__table__
    deleted_at_col = table.c.deleted_at

    for col in table.columns:
        if not col.info.get("soft_delete_unique"):
            continue

        idx_name = f"uq_{table.name}_{col.name}{_ACTIVE_INDEX_SUFFIX}"
        if any(idx.name == idx_name for idx in table.indexes):
            continue

        table.indexes.add(
            Index(
                idx_name,
                col,
                unique=True,
                postgresql_where=deleted_at_col.is_(None),
                sqlite_where=deleted_at_col.is_(None),
            )
        )


def _warn_plain_unique_constraints(model: type) -> None:
    """Log a warning for plain ``UniqueConstraint`` on soft-delete models."""
    table = model.__table__
    pk_col_names = {c.name for c in table.primary_key.columns}

    for constraint in table.constraints:
        if not isinstance(constraint, UniqueConstraint):
            continue
        col_names = {c.name for c in constraint.columns}
        if not col_names or col_names == pk_col_names:
            continue
        logger.warning(
            "%s has a UniqueConstraint on (%s) but uses SoftDeleteMixin. "
            "Consider SoftDeleteUniqueIndex or "
            "soft_delete_mapped_column(unique=True) so soft-deleted rows "
            "don't block reuse of unique values. If global uniqueness is "
            "intended, this warning can be safely ignored.",
            model.__name__,
            ", ".join(sorted(col_names)),
        )


# ---------------------------------------------------------------------------
# Pyramid directive
# ---------------------------------------------------------------------------


def sa_enable_soft_delete(config) -> None:
    """Activate soft-delete behaviour for the application.

    Registers event listeners for:

    * **Delete interception** — ``session.delete()`` performs a soft delete
      on models with ``SoftDeleteMixin``.
    * **Query filtering** — SELECT queries automatically exclude soft-deleted
      rows.  Bypass with ``execution_options(include_deleted=True)``.
    * **Index finalization** — ``SoftDeleteUniqueIndex`` markers and
      ``soft_delete_mapped_column(unique=True)`` columns are converted into
      partial unique indexes (``WHERE deleted_at IS NULL``).  A warning is
      logged for any plain ``UniqueConstraint`` on a soft-delete model.

    Usage::

        config.include("pyramid_sa")
        config.sa_enable_soft_delete()
    """
    factory = config.registry["dbsession_factory"]
    if not event.contains(factory, "before_flush", _convert_deletes_to_soft_deletes):
        event.listen(factory, "before_flush", _convert_deletes_to_soft_deletes)
    if not event.contains(factory, "do_orm_execute", _soft_delete_query_filter):
        event.listen(factory, "do_orm_execute", _soft_delete_query_filter)
    if not event.contains(Mapper, "after_configured", _discover_soft_delete_models):
        event.listen(Mapper, "after_configured", _discover_soft_delete_models)
    # Run eagerly for mappers that were already configured before this
    # directive was called (common in test setups where models are imported
    # at collection time).
    _discover_soft_delete_models()
