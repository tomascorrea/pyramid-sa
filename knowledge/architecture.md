# Architecture

## Overview

pyramid-sa is a Pyramid integration library that provides SQLAlchemy session management, a declarative base with utility methods, opt-in audit and soft-delete mixins activated via Pyramid directives, exception-to-HTTP mapping, JSON rendering, Alembic migration helpers, and CLI commands. A companion package (pyramid-sa-testing) ships a pytest plugin with database test fixtures.

## Components

- **__init__.py** — `includeme` (Pyramid entry point), `sa_scan_models` directive, `Model` convenience base class (AuditMixin + SoftDeleteMixin + Base)
- **meta.py** — `ORMClass` (utility methods: `as_dict`, `copy_with`), `Base` (DeclarativeBase + ORMClass), naming conventions, `generate_uuid`, `_now`
- **audit.py** — `AuditMixin` (audit columns), `before_insert`/`before_update` event listeners, `sa_enable_audit` directive
- **soft_delete.py** — `SoftDeleteMixin` (soft-delete columns + `soft_delete()`/`restore()`/`is_deleted`), `SoftDeleteSession` (`hard_delete()`), event listeners (delete interception, query filtering, unique index transformation), `sa_enable_soft_delete` directive
- **session.py** — Engine creation, session factory (uses `SoftDeleteSession`), transaction-managed sessions via pyramid_tm + zope.sqlalchemy
- **tween.py** — Exception tween translating `NoResultFound` → 404 and `IntegrityError` → 409
- **renderer.py** — JSON renderer with adapters for datetime, date, UUID
- **scripts/alembic.py** — Offline/online migration runner helpers
- **scripts/cli.py** — Click `db` command group (init-alembic, drop, initialize)
- **templates/alembic/** — Bundled alembic scaffold templates copied into consuming apps by `db init-alembic`
- **pyramid_sa_testing** (separate package) — Pytest plugin providing engine, session, transaction, and WebTest fixtures

## Data Flow

1. Consuming app calls `config.include("pyramid_sa")`
2. `includeme` wires pyramid_tm, engine, session factory, tween, renderer, and registers directives (`sa_scan_models`, `sa_enable_audit`, `sa_enable_soft_delete`)
3. App calls `config.sa_enable_audit()` to activate audit event listeners
4. App calls `config.sa_enable_soft_delete()` to activate soft-delete behavior (query filtering, delete interception, unique index transformation)
5. App calls `config.sa_scan_models("myapp.models")` to import model modules and configure mappers
6. Each request gets a `request.dbsession` (reified, transaction-managed)
7. Audit event listeners populate created_by/updated_by from the request
8. Soft-delete event listeners intercept `session.delete()` and filter queries
9. On exceptions, the tween maps SA errors to HTTP responses

## Columns vs Behavior

Mixins provide **columns** at import time. Directives activate **behavior** at app startup. This separation means:

- Models can use `AuditMixin` or `SoftDeleteMixin` for columns without any runtime behavior
- `config.sa_enable_audit()` registers event listeners that populate audit fields from the request
- `config.sa_enable_soft_delete()` registers event listeners scoped to the app's sessionmaker (not global)

## External Dependencies

pyramid, sqlalchemy, alembic, pyramid-tm, zope-sqlalchemy, click, camel-converter
