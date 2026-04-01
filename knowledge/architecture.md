# Architecture

## Overview

pyramid-sa is a Pyramid integration library that provides SQLAlchemy session management, a declarative base with utility methods, opt-in audit and soft-delete mixins activated via Pyramid directives, exception-to-HTTP mapping, JSON rendering, Alembic migration helpers, and CLI commands. A companion package (pyramid-sa-testing) ships a pytest plugin with database test fixtures.

## Components

- **__init__.py** — `includeme` (Pyramid entry point), `sa_scan_models` directive, top-level re-exports
- **meta.py** — `ORMClass` (utility methods: `as_dict`, `copy_with`), `Base` (DeclarativeBase + ORMClass), naming conventions
- **utils.py** — Shared helpers: `_now` (UTC timestamp), `generate_uuid` (UUID v4)
- **models/__init__.py** — `Model` convenience base class (AuditMixin + SoftDeleteMixin + Base), re-exports from audit and soft_delete submodules
- **models/audit.py** — `AuditMixin` (audit columns), `before_insert`/`before_update` event listeners, `sa_enable_audit` directive
- **models/soft_delete.py** — `SoftDeleteMixin` (soft-delete columns + `soft_delete()`/`restore()`/`is_deleted`/`can_restore()`), `SoftDeleteSession` (`hard_delete()`), `SoftDeleteUniqueIndex` (partial unique index for `__table_args__`), `soft_delete_mapped_column` (column-level partial unique index), `RestoreConflictError`, event listeners (delete interception, query filtering, index finalization), `sa_enable_soft_delete` directive
- **session.py** — Engine creation, session factory (uses `SoftDeleteSession`), transaction-managed sessions via pyramid_tm + zope.sqlalchemy
- **tween.py** — Exception tween translating `NoResultFound` → 404 and `IntegrityError` → 409, with configurable error body formatters via `sa_error_formatter` directive
- **renderer.py** — JSON renderer with adapters for datetime, date, UUID
- **scripts/alembic.py** — Offline/online migration runner helpers
- **scripts/cli.py** — Click `db` command group (init-alembic, drop, initialize)
- **templates/alembic/** — Bundled alembic scaffold templates copied into consuming apps by `db init-alembic`
- **pyramid_sa_testing** (separate package) — Pytest plugin providing engine, session, transaction, and WebTest fixtures

## Data Flow

1. Consuming app calls `config.include("pyramid_sa")`
2. `includeme` wires pyramid_tm, pyramid_retry, engine, session factory, tweens (exception mapping + request-session wiring), and registers directives (`sa_json_renderer`, `sa_scan_models`, `sa_enable_audit`, `sa_enable_soft_delete`, `sa_error_formatter`)
3. App calls `config.sa_json_renderer()` to register the JSON renderer (opt-in)
4. App calls `config.sa_enable_audit()` to activate audit event listeners
5. App calls `config.sa_enable_soft_delete()` to activate soft-delete behavior (query filtering, delete interception, index finalization for `SoftDeleteUniqueIndex` and `soft_delete_mapped_column`)
6. App calls `config.sa_scan_models("myapp.models")` to import model modules and configure mappers (accepts strings or module objects)
7. Each request gets a `request.dbsession` (reified, transaction-managed); the request-session tween ensures `dbsession.info["request"]` is always set
8. Audit event listeners populate created_by/updated_by/created_ip/updated_ip from the request
9. Soft-delete event listeners intercept `session.delete()` and filter queries
10. On exceptions, the tween maps SA errors to HTTP responses; formatters receive the exception via `exc` keyword

## Columns vs Behavior

Mixins provide **columns** at import time. Directives activate **behavior** at app startup. This separation means:

- Models can use `AuditMixin` or `SoftDeleteMixin` for columns without any runtime behavior
- `config.sa_enable_audit()` registers event listeners that populate audit fields from the request
- `config.sa_enable_soft_delete()` registers event listeners scoped to the app's sessionmaker (not global)

## Test Infrastructure

All tests run against PostgreSQL via pytest-postgresql. The `postgresql_proc` fixture (auto-registered by the plugin) starts a temporary PostgreSQL process on a random port per test session. Each `db_engine` fixture builds a `postgresql+psycopg://` URL from the process connection info. Doomed transactions provide per-test isolation.

The soft-delete test module uses a dedicated database (`test_soft_delete`) because `sa_enable_soft_delete()` finalizes `SoftDeleteUniqueIndex` markers and `soft_delete_mapped_column` columns into partial indexes during `after_configured`. Other modules share the default `postgres` database.

The `pyramid_sa_testing` plugin provides `pyramid_sa_engine` (backed by `postgresql_proc`), `pyramid_sa_tm`, `pyramid_sa_dbsession`, `pyramid_sa_testapp`, and `pyramid_sa_app_request` fixtures.

The devcontainer Dockerfile installs PostgreSQL server binaries so `postgresql_proc` can start its own instance.

## Timezone Handling

`_now()` in `utils.py` uses `datetime.UTC` (Python 3.11+) to produce timezone-aware UTC datetimes. The `tzinfo` is `datetime.timezone.utc`. This compares equal to `pytz.UTC` but has a different `repr`. Projects migrating from naive datetimes (`TIMESTAMP WITHOUT TIME ZONE`) should ensure column types use `TIMESTAMP(timezone=True)` or cast existing data.

## Testing Plugin Override Points

The `pyramid_sa_engine` fixture is the intended override point for projects that use a different PostgreSQL driver or test infrastructure. Override it in your `conftest.py` to yield a SQLAlchemy `Engine` instance and handle cleanup (e.g., `drop_all`, `dispose`). All other plugin fixtures (`pyramid_sa_tm`, `pyramid_sa_dbsession`, `pyramid_sa_testapp`, `pyramid_sa_app_request`) build on top of the engine and the `app` fixture.

## External Dependencies

pyramid, sqlalchemy, alembic, pyramid-tm, pyramid-retry, zope-sqlalchemy, click, camel-converter

Dev/test: pytest-postgresql, psycopg
