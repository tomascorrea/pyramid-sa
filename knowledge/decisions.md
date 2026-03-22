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

### 2026-03-22 — Configurable exception tween error body formatters

**Status**: Accepted

**Context**: The exception tween hardcoded JSON error response bodies (`{"error": "not_found", "message": "..."}` for 404, similar for 409). Consuming apps needed to customize the error schema to match their own API conventions.

**Decision**: Add a `sa_error_formatter` Pyramid directive that accepts keyword-only `not_found` and `conflict` arguments, each a callable with signature `(request) -> dict`. The tween reads formatters from the registry at app creation time, falling back to default functions that preserve the original behavior. Both arguments are optional, allowing partial overrides.

**Consequences**: Apps can customize error response bodies without forking or monkey-patching the tween. The formatter receives the request, giving access to locale, auth context, or any request-scoped data. Default behavior is unchanged for apps that don't call the directive.
