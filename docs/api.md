# API Reference

Complete public API grouped by module. All items listed here are importable from their respective modules. Items marked with **top-level** are also importable directly from `pyramid_sa`.

## `pyramid_sa`

The top-level package re-exports the most commonly used names and provides the Pyramid entry point.

### `includeme(config)`

Pyramid entry point. Activate with `config.include("pyramid_sa")`. Wires engine, session factory, `request.dbsession`, exception tween, JSON renderer, and registers all directives.

### `Model`

**top-level** — `class Model(AuditMixin, SoftDeleteMixin, Base)`

Abstract base class combining audit columns, soft-delete columns, and all `Base` utilities. Use for models that need both features.

---

## `pyramid_sa.meta`

### `Base`

**top-level** — `class Base(ORMClass, DeclarativeBase)`

Declarative base with naming conventions and utility methods. All models should inherit from this (or from `Model`).

### `ORMClass`

Mixin class providing utility methods on all models.

**`as_dict(hide_internal_fields=True, convert_to_camel=True, exclude=None) -> dict`**

Convert instance to a dictionary. See [Base & Models](models.md#as_dict) for details.

**`copy_with(**kwargs) -> Self`**

Create a detached copy with optional field overrides. Excludes `id`, `uuid`, `created_at`, `updated_at`.

### `generate_uuid() -> uuid.UUID`

**top-level** — Returns a new UUID v4.

---

## `pyramid_sa.audit`

### `AuditMixin`

**top-level** — Mixin adding audit columns: `created_at`, `updated_at`, `created_by`, `updated_by`, `created_ip`, `updated_ip`.

### `sa_enable_audit(config) -> None`

**top-level** — Pyramid directive. Registers `before_insert` and `before_update` event listeners that populate audit fields from `request.authenticated_userid` and `request.client_addr`.

---

## `pyramid_sa.soft_delete`

### `SoftDeleteMixin`

**top-level** — Mixin adding soft-delete columns and instance methods.

**Columns:** `deleted_at` (DateTime), `deleted_by` (String(40)), `deleted_ip` (String(40))

**`is_deleted -> bool`** (property)

Returns `True` if `deleted_at` is not `None`.

**`soft_delete() -> None`**

Mark the instance as soft-deleted. Sets `deleted_at`, `deleted_by`, and `deleted_ip` from the request.

**`can_restore() -> list[tuple[str, ...]]`**

Check for unique constraint conflicts before restoring. Returns a list of conflicting column groups (empty = safe to restore).

**`restore() -> None`**

Clear `deleted_at`, `deleted_by`, and `deleted_ip`. Raises `RestoreConflictError` if an active row conflicts.

### `SoftDeleteSession`

**top-level** — `class SoftDeleteSession(Session)`

Session subclass used by pyramid-sa's session factory.

**`hard_delete(instance) -> None`**

Perform a real SQL DELETE, bypassing soft-delete interception.

### `SoftDeleteUniqueIndex(*columns, name=None)`

**top-level** — `class SoftDeleteUniqueIndex(Index)`

Partial unique index for `__table_args__`. Creates `WHERE deleted_at IS NULL` unique index on the specified columns. Validates that the model has `SoftDeleteMixin`.

### `soft_delete_mapped_column(*args, unique=False, **kwargs) -> MappedColumn`

**top-level** — Like `mapped_column` but `unique=True` creates a soft-delete-aware partial unique index instead of a plain unique constraint.

### `RestoreConflictError`

**top-level** — `class RestoreConflictError(Exception)`

Raised by `restore()` when an active row conflicts with the soft-deleted row's unique values.

**Attributes:**

- `instance` — the model instance that cannot be restored
- `conflicts` — list of column-name tuples, e.g. `[("slug",)]` or `[("tenant_id", "code")]`

### `sa_enable_soft_delete(config) -> None`

**top-level** — Pyramid directive. Registers event listeners for delete interception, query filtering, and index finalization on the app's sessionmaker.

---

## `pyramid_sa.session`

### `get_engine(settings, prefix="sqlalchemy.") -> Engine`

**top-level** — Create a SQLAlchemy engine from the `{prefix}url` key in settings.

### `get_session_factory(engine) -> sessionmaker[SoftDeleteSession]`

**top-level** — Create a session factory bound to the engine, using `SoftDeleteSession`.

### `get_tm_session(session_factory, transaction_manager, request=None) -> SoftDeleteSession`

**top-level** — Create a transaction-managed session. Registers the session with zope.sqlalchemy and stores the request in `session.info["request"]`.

---

## `pyramid_sa.tween`

### `sa_error_formatter(config, *, not_found=None, conflict=None) -> None`

**top-level** — Pyramid directive. Configure custom error body formatters for the exception tween. Each formatter is `(request) -> dict`.

### `default_not_found_body(request) -> dict`

**top-level** — Returns `{"error": "not_found", "message": "Resource not found."}`.

### `default_conflict_body(request) -> dict`

**top-level** — Returns `{"error": "conflict", "message": "Operation violates a uniqueness constraint."}`.

### `exception_tween_factory(handler, registry) -> Callable`

Tween factory that catches `NoResultFound` (→ 404) and `IntegrityError` (→ 409).

---

## `pyramid_sa.renderer`

### `configure_json_renderer(config) -> None`

Register a JSON renderer with adapters for `datetime` (→ ISO string), `date` (→ ISO string), and `UUID` (→ string).

---

## `pyramid_sa.scripts.cli`

### `db`

Click command group for database management. Contains `init-alembic`, `drop`, and `initialize` subcommands. See [Database & Migrations](database.md) for usage.

---

## `pyramid_sa.scripts.alembic`

### `run_migrations_offline(target_metadata) -> None`

Run Alembic migrations in offline mode (SQL output only).

### `run_migrations_online(target_metadata) -> None`

Run Alembic migrations in online mode (direct database connection).
