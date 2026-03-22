"""Soft delete mixin, session subclass, and Pyramid directive."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint, event, inspect
from sqlalchemy.orm import Mapped, Mapper, Session, mapped_column, with_loader_criteria

from pyramid_sa.meta import Base

_HARD_DELETE_FLAG = "_pyramid_sa_hard_delete"

_soft_delete_models: set[type] = set()


def _now() -> datetime:
    return datetime.now(UTC)


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

    def restore(self) -> None:
        """Un-delete this instance."""
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


def _discover_and_transform_soft_delete_models() -> None:
    """``after_configured`` handler: discover models and transform unique indexes."""
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if not isinstance(cls, type) or not issubclass(cls, SoftDeleteMixin):
            continue
        if cls is SoftDeleteMixin:
            continue
        _soft_delete_models.add(cls)
        _transform_unique_constraints(cls)


def _transform_unique_constraints(model: type) -> None:
    """Replace plain unique constraints with filtered partial indexes."""
    table = model.__table__
    deleted_at_col = table.c.deleted_at

    constraints_to_remove: list[UniqueConstraint] = []
    indexes_to_add: list[Index] = []

    for constraint in list(table.constraints):
        if not isinstance(constraint, UniqueConstraint):
            continue
        columns = list(constraint.columns)
        if not columns:
            continue
        # Skip if this constraint is also the primary key
        pk_col_names = {c.name for c in table.primary_key.columns}
        constraint_col_names = {c.name for c in columns}
        if constraint_col_names == pk_col_names:
            continue

        constraints_to_remove.append(constraint)
        col_names = "_".join(c.name for c in columns)
        idx_name = f"uq_{table.name}_{col_names}_active"

        # Skip if we already created this index (idempotency)
        if any(idx.name == idx_name for idx in table.indexes):
            continue

        indexes_to_add.append(
            Index(
                idx_name,
                *columns,
                unique=True,
                sqlite_where=deleted_at_col.is_(None),
                postgresql_where=deleted_at_col.is_(None),
            )
        )

    for constraint in constraints_to_remove:
        table.constraints.discard(constraint)
        for col in constraint.columns:
            col.unique = False

    for idx in indexes_to_add:
        table.indexes.add(idx)


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
    * **Unique index transformation** — ``UniqueConstraint`` on soft-delete
      models become filtered partial indexes (``WHERE deleted_at IS NULL``).

    Usage::

        config.include("pyramid_sa")
        config.sa_enable_soft_delete()
    """
    factory = config.registry["dbsession_factory"]
    if not event.contains(factory, "before_flush", _convert_deletes_to_soft_deletes):
        event.listen(factory, "before_flush", _convert_deletes_to_soft_deletes)
    if not event.contains(factory, "do_orm_execute", _soft_delete_query_filter):
        event.listen(factory, "do_orm_execute", _soft_delete_query_filter)
    if not event.contains(
        Mapper, "after_configured", _discover_and_transform_soft_delete_models
    ):
        event.listen(
            Mapper, "after_configured", _discover_and_transform_soft_delete_models
        )
    # Run eagerly for mappers that were already configured before this
    # directive was called (common in test setups where models are imported
    # at collection time).
    _discover_and_transform_soft_delete_models()
