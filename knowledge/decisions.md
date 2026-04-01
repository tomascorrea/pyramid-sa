# Architectural Decisions

Record of key technical and architectural decisions for this project.

## Template

Use this format when adding a new decision:

### YYYY-MM-DD — Decision Title

**Status**: Accepted | Superseded | Deprecated

**Context**: What is the issue or situation that motivates this decision?

**Decision**: What is the change that we're proposing or have agreed to?

**Consequences**: What are the trade-offs and results of this decision?

---

## Decisions

### 2026-03-21 — Initial project setup

**Status**: Accepted

**Context**: Starting a reusable Pyramid+SQLAlchemy integration library extracted from production patterns.

**Decision**: Using uv with src layout, ruff + black for linting/formatting, pytest for testing, and MkDocs for documentation.

**Consequences**: Consistent project structure that follows Python best practices. All team members and AI assistants can rely on the same conventions.

### 2026-03-21 — Alembic scaffold owned by consuming app

**Status**: Accepted

**Context**: Alembic migration versions must live in the consuming application, not in the library. The library provides migration runner helpers but had no way to bootstrap the alembic directory structure.

**Decision**: Bundle alembic template files under `pyramid_sa/templates/alembic/` and provide a `db init-alembic` CLI command that copies them into the consuming app's working directory. Templates are read via `importlib.resources`. The command refuses to overwrite unless `--force` is passed.

**Consequences**: Consuming apps get a one-command setup for alembic, pre-wired with pyramid-sa helpers. Migration versions stay in the app, never in the library. The templates directory uses a distinct name (`templates/`) to avoid confusion with actual alembic migration data.

### 2026-03-21 — Separate testing package

**Status**: Accepted

**Context**: Test fixtures (pytest plugin) depend on webtest and transaction, which should not ship in production.

**Decision**: Split into two packages in one repo: `pyramid-sa` (main library) and `pyramid-sa-testing` (pytest plugin). The testing package has its own pyproject.toml under `testing/`.

**Consequences**: Production installs carry zero test code or test dependencies. Consuming apps add `pyramid-sa-testing` to dev dependencies only.

### 2026-03-22 — Configurable mixins: columns vs behavior separation

**Status**: Accepted

**Context**: AuditMixin was baked into Base, meaning every model got audit columns with no opt-out. Adding soft delete required a similar pattern but we wanted both features to be opt-in.

**Decision**: Separate columns (mixins) from behavior (Pyramid directives). `AuditMixin` and `SoftDeleteMixin` provide columns at import time. `config.sa_enable_audit()` and `config.sa_enable_soft_delete()` activate event listeners at app startup. A `Model` convenience class combines both mixins with Base for the common case.

**Consequences**: Apps choose exactly which features they need. Models can have soft-delete columns without soft-delete behavior (useful for shared schemas). Soft-delete event listeners are scoped to the app's sessionmaker, not the global Session class, preventing cross-app leakage.

### 2026-03-22 — ORMClass as Base foundation

**Status**: Accepted

**Context**: `as_dict` and `copy_with` were part of `AuditMixin`, but these utility methods are useful on any model, not just audited ones.

**Decision**: Extract utility methods into `ORMClass` and make `Base` inherit from it (`Base(ORMClass, DeclarativeBase)`). Every model gets `as_dict` and `copy_with` automatically, regardless of which mixins it uses.

**Consequences**: Clean separation — `ORMClass` has utility methods, `AuditMixin` has audit columns, `SoftDeleteMixin` has soft-delete columns. No method/column coupling.

### 2026-03-22 — Soft-delete event scoping on sessionmaker

**Status**: Accepted

**Context**: Soft-delete event listeners (`before_flush`, `do_orm_execute`) were initially registered on the global `Session` class. In tests running multiple Pyramid apps (one with soft delete, one without), this caused the no-soft-delete app to inherit soft-delete behavior.

**Decision**: Register soft-delete session events on the specific `sessionmaker` instance from `config.registry["dbsession_factory"]`, not the `Session` class. Audit events remain on the global `Mapper` (they check `isinstance` and are harmless when no `AuditMixin` models exist).

**Consequences**: Each Pyramid app gets exactly the soft-delete behavior it opted into. Multiple apps in the same process (common in tests) don't interfere with each other.

### 2026-03-22 — PostgreSQL test infrastructure via pytest-postgresql

**Status**: Accepted

**Context**: All tests ran against SQLite in-memory. The library had partial PostgreSQL awareness (e.g. `postgresql_where` in soft-delete partial indexes) but had never been tested against a real PostgreSQL instance. SQLite's behavioral differences (e.g. lack of real partial unique indexes) meant bugs could reach production undetected.

**Decision**: Switch the entire test suite to PostgreSQL using pytest-postgresql. The `postgresql_proc` fixture starts a temporary PostgreSQL process per test session. The devcontainer Dockerfile installs PostgreSQL server binaries. The soft-delete module uses a dedicated database because its metadata transformation (unique constraints to partial indexes) conflicts with tables created by other modules before the transformation runs.

**Consequences**: Tests now validate against real PostgreSQL behavior. The soft-delete partial unique index test, which passed on SQLite by coincidence, was validated to work correctly on PostgreSQL. The testing plugin (`pyramid-sa-testing`) also defaults to PostgreSQL, so consuming apps get PostgreSQL testing out of the box. The devcontainer image is slightly larger due to PostgreSQL server packages.

### 2026-03-22 — Configurable exception tween error body formatters

**Status**: Accepted

**Context**: The exception tween hardcoded JSON error response bodies (`{"error": "not_found", "message": "..."}` for 404, similar for 409). Consuming apps needed to customize the error schema to match their own API conventions.

**Decision**: Add a `sa_error_formatter` Pyramid directive that accepts keyword-only `not_found` and `conflict` arguments, each a callable with signature `(request) -> dict`. The tween reads formatters from the registry at app creation time, falling back to default functions that preserve the original behavior. Both arguments are optional, allowing partial overrides.

**Consequences**: Apps can customize error response bodies without forking or monkey-patching the tween. The formatter receives the request, giving access to locale, auth context, or any request-scoped data. Default behavior is unchanged for apps that don't call the directive.

### 2026-03-22 — Restore conflict safety via can_restore()

**Status**: Accepted

**Context**: When a soft-deleted row is restored but another active row already holds its unique value, the database raises an opaque `IntegrityError` referencing a partial index name. Developers had no pre-check and no friendly error message.

**Decision**: Add `can_restore()` to `SoftDeleteMixin` that inspects the model's partial unique indexes (named `uq_{table}_{cols}_active`) and queries for active rows with matching values. `restore()` calls `can_restore()` before clearing `deleted_at` and raises `RestoreConflictError` if conflicts exist. The check runs only when `restore()` is called — no per-flush overhead. `can_restore()` is also available independently for pre-checking. Considered alternatives: `before_flush` event listener (rejected — too expensive on every flush), separate `safe_restore()` method (rejected — easy to forget).

**Consequences**: Developers get an immediate, descriptive error when restoring would violate uniqueness. `RestoreConflictError` includes the conflicting column groups and the instance. Works for single-column and multi-column unique constraints. Models without partial unique indexes (no `sa_enable_soft_delete()` called, or no unique columns) always return safe from `can_restore()`.

### 2026-03-22 — Explicit soft-delete unique indexes

**Status**: Accepted (supersedes the implicit `_transform_unique_constraints` approach)

**Context**: `sa_enable_soft_delete()` magically transformed all `UniqueConstraint`s on soft-delete models into partial indexes. This was implicit (the developer writes `unique=True` and the framework silently changes the semantics), offered no opt-out for globally unique columns like `uuid`, didn't support `Index(..., unique=True)`, and confused Alembic autogenerate.

**Decision**: Replace the magic transformation with two explicit APIs the developer imports and uses: `SoftDeleteUniqueIndex(*columns)` for multi-column unique indexes in `__table_args__`, and `soft_delete_mapped_column(..., unique=True)` for single-column uniqueness at the column level. Both produce partial unique indexes with `WHERE deleted_at IS NULL`. A warning is logged when a plain `UniqueConstraint` is detected on a soft-delete model, nudging the developer to choose explicitly. `SoftDeleteUniqueIndex` validates at table creation time that the model has a `deleted_at` column (from `SoftDeleteMixin`), raising `TypeError` if not. Regular `mapped_column(unique=True)` stays globally unique — the developer chooses per-column.

**Consequences**: Explicit is better than implicit. Developers opt in per-column, so globally unique columns (UUIDs, external IDs) are no longer silently transformed. `can_restore()` continues to work because both APIs produce indexes named `uq_{table}_{cols}_active`. This is a breaking change — consuming apps must update their models to use the new APIs. The warning helps catch missed columns during migration.

### 2026-03-31 — Bugs and improvements from production comparison (v0.8.0)

**Status**: Accepted

**Context**: Comparing pyramid-sa v0.8.0 against battle-tested production patterns revealed several bugs and improvement opportunities.

**Decision**: Applied the following changes:

- **B1**: `get_engine` now uses `engine_from_config` instead of `create_engine(url)`, so all `sqlalchemy.*` INI keys (pool_size, pool_recycle, echo, etc.) are honoured.
- **B2**: Added a request-session tween (`_add_request_to_session_tween_factory`) that sets `request.dbsession.info["request"] = request` on every request, ensuring audit listeners work even when sessions are injected via `request.environ["app.dbsession"]`.
- **B3**: Testing plugin fixtures now set `REMOTE_ADDR` and wire `dbsession.info["request"]` so audit fields populate correctly in tests.
- **B4**: JSON renderer is now opt-in via `config.sa_json_renderer()` directive instead of being registered unconditionally. **Breaking change** — consuming apps must call the directive explicitly.
- **I1**: `pyramid_retry` is now included by default for transient DB error handling. Added to dependencies.
- **I2**: `includeme` checks both `config.registry` and `settings` for a pre-configured `"dbengine"`.
- **I3**: `sa_scan_models` accepts both dotted string paths and module objects.
- **I6**: Error body formatters now receive the caught exception via `exc` keyword argument. Default formatters accept `**kwargs` for backwards compatibility.

**Consequences**: B4 is a breaking change for consuming apps that relied on the auto-registered renderer. I6 requires existing custom formatters to accept `**kwargs` or an `exc` keyword. All other changes are backwards-compatible.
